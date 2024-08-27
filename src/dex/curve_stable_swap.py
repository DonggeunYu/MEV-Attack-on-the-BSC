import time
import copy
from typing import Dict, List, Tuple
from web3 import Web3
from ..multicall import Call
from ..utils import multicall_by_chunk
from .dex import DexBase
from ..types import PoolInfo
from .curve_pool_info import INFORMATION_FOR_POOL
from .curve_utils import calc_withdraw_one_coin, get_y, get_D
from ..utils import memoize

PRECISION = 10**18
FEE_DENOMINATOR = 10**10


class _CurveBase(DexBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def _fetch_pools_reserve_info(
        self, pool_addresses: List[str], balances_signature: str
    ):
        A_signature = "A()(uint256)"
        address_length = len(pool_addresses[0])
        calls = []
        for address in pool_addresses:
            assert address.lower() in INFORMATION_FOR_POOL
            call = Call(address, A_signature, [(address + "_A", lambda x: x)])
            calls.append(call)
            for i in range(INFORMATION_FOR_POOL[address.lower()]["N_COINS"]):
                call = Call(
                    address,
                    [balances_signature, i],
                    [(address + "_balances_" + str(i), lambda x: x)],
                )
                calls.append(call)

            # for specific pool type, we need to add extra calls
            pool_type = INFORMATION_FOR_POOL[address.lower()]["TYPE"]
            if pool_type == "AAVE":
                call = Call(
                    address,
                    "offpeg_fee_multiplier()(uint256)",
                    [(address + "_offpeg_fee_multiplier", lambda x: x)],
                )
                calls.append(call)
            elif pool_type in ["STORED_RATES", "USE_LENDING"]:
                for idx, coin_address in enumerate(
                    INFORMATION_FOR_POOL[address.lower()]["COINS"]
                ):
                    if (
                        pool_type == "USE_LENDING"
                        and not INFORMATION_FOR_POOL[address.lower()]["USE_LENDING"][
                            idx
                        ]
                    ):
                        continue

                    call = Call(
                        coin_address,
                        "exchangeRateStored()(uint256)",
                        [(address + "_exchangeRateStored_" + str(idx), lambda x: x)],
                    )
                    calls.append(call)
                    call = Call(
                        coin_address,
                        "supplyRatePerBlock()(uint256)",
                        [(address + "_supplyRatePerBlock_" + str(idx), lambda x: x)],
                    )
                    calls.append(call)
                    call = Call(
                        coin_address,
                        "accrualBlockNumber()(uint256)",
                        [(address + "_accrualBlockNumber_" + str(idx), lambda x: x)],
                    )
                    calls.append(call)
            elif pool_type == "USE_LENDING_1":
                for idx, coin_address in enumerate(
                    INFORMATION_FOR_POOL[address.lower()]["COINS"]
                ):
                    if not INFORMATION_FOR_POOL[address.lower()]["USE_LENDING"][idx]:
                        continue

                    call = Call(
                        coin_address,
                        "getPricePerFullShare()(uint256)",
                        [
                            (
                                address + "_getPricePerFullShare_" + str(idx),
                                lambda x: x,
                            )
                        ],
                    )
                    calls.append(call)
            elif pool_type == "BASE_VIRTUAL_PRICE":
                calls.extend(
                    [
                        Call(
                            address,
                            "base_cache_updated()(uint256)",
                            [(address + "_base_cache_updated", lambda x: x)],
                        ),
                        Call(
                            INFORMATION_FOR_POOL[address.lower()]["base_pool"],
                            "get_virtual_price()(uint256)",
                            [
                                (
                                    address + "_base_pool_get_virtual_price",
                                    lambda x: x,
                                )
                            ],
                        ),
                        Call(
                            address,
                            "base_virtual_price()(uint256)",
                            [(address + "_base_virtual_price", lambda x: x)],
                        ),
                    ]
                )
                if "base_pool" in INFORMATION_FOR_POOL[address.lower()]:
                    base_pool_address = INFORMATION_FOR_POOL[address.lower()][
                        "base_pool"
                    ]
                    lp_token_address = INFORMATION_FOR_POOL[base_pool_address.lower()][
                        "LP_TOKEN"
                    ]
                    calls.extend(
                        [
                            Call(
                                lp_token_address,
                                "totalSupply()(uint256)",
                                [
                                    (
                                        address + "_base_pool_lp_total_supply",
                                        lambda x: x,
                                    )
                                ],
                            ),
                            Call(
                                base_pool_address,
                                "A()(uint256)",
                                [(address + "_base_pool_A", lambda x: x)],
                            ),
                            Call(
                                base_pool_address,
                                "fee()(uint256)",
                                [(address + "_base_pool_fee", lambda x: x)],
                            ),
                        ]
                    )
                    if INFORMATION_FOR_POOL[base_pool_address.lower()][
                        "VYPER_VERSION_1"
                    ]:
                        _balances_signature = "balances(int128)(uint256)"
                    else:
                        _balances_signature = "balances(uint256)(uint256)"
                    for idx, base_pool_coin in enumerate(
                        INFORMATION_FOR_POOL[base_pool_address.lower()]["COINS"]
                    ):
                        call = Call(
                            base_pool_address,
                            [balances_signature, idx],
                            [
                                (
                                    address + "_base_pool_balances_" + str(idx),
                                    lambda x: x,
                                ),
                            ],
                        )
                        calls.append(call)

        result = multicall_by_chunk(self.http_endpoint, calls)

        formatted_result = {}
        for k, v in result.items():
            address = k[:address_length]
            if address not in formatted_result:
                count = INFORMATION_FOR_POOL[address.lower()]["N_COINS"]
                formatted_result[address] = {"balances": [0] * count}
            if k[address_length + 1 :].startswith("A"):
                formatted_result[address].update({"A": v})
                continue
            elif k[address_length + 1 :].startswith("balances_"):
                formatted_result[address]["balances"][int(k[-1])] = v
                continue

            if k[address_length + 1 :].startswith("exchangeRateStored_"):
                if "exchangeRateStored" not in formatted_result[address]:
                    count = len(INFORMATION_FOR_POOL[address.lower()]["COINS"])
                    formatted_result[address].update(
                        {"exchangeRateStored": [0] * count}
                    )
                formatted_result[address]["exchangeRateStored"][int(k[-1])] = v
                continue
            elif k[address_length + 1 :].startswith("supplyRatePerBlock_"):
                if "supplyRatePerBlock" not in formatted_result[address]:
                    count = len(INFORMATION_FOR_POOL[address.lower()]["COINS"])
                    formatted_result[address].update(
                        {"supplyRatePerBlock": [0] * count}
                    )
                formatted_result[address]["supplyRatePerBlock"][int(k[-1])] = v
                continue
            elif k[address_length + 1 :].startswith("accrualBlockNumber_"):
                if "accrualBlockNumber" not in formatted_result[address]:
                    count = len(INFORMATION_FOR_POOL[address.lower()]["COINS"])
                    formatted_result[address].update(
                        {"accrualBlockNumber": [0] * count}
                    )
                formatted_result[address]["accrualBlockNumber"][int(k[-1])] = v
                continue
            elif k[address_length + 1 :].startswith("getPricePerFullShare"):
                if "getPricePerFullShare" not in formatted_result[address]:
                    count = len(INFORMATION_FOR_POOL[address.lower()]["COINS"])
                    formatted_result[address].update(
                        {"getPricePerFullShare": [0] * count}
                    )
                formatted_result[address]["getPricePerFullShare"][int(k[-1])] = v
                continue
            elif k[address_length + 1 :].startswith("base_pool_balances_"):
                if "base_pool_balances" not in formatted_result[address]:
                    count = INFORMATION_FOR_POOL[
                        INFORMATION_FOR_POOL[address.lower()]["base_pool"].lower()
                    ]["N_COINS"]
                    formatted_result[address].update(
                        {"base_pool_balances": [0] * count}
                    )
                formatted_result[address]["base_pool_balances"][int(k[-1])] = v
                continue

            # for specific pool type, we need to add extra calls
            formatted_result[address].update({k[len(address) + 1 :]: v})

        return formatted_result

    def _fetch_pools_token_addresses(
        self, pool_addresses: List[str], coins_signature: str
    ) -> Dict[str, Tuple[str, ...]]:
        def get_count(address):
            if coins_signature.startswith("coins") or coins_signature.startswith(
                "underlying_coins"
            ):
                return INFORMATION_FOR_POOL[address.lower()]["N_COINS"]
            elif coins_signature.startswith("base_coins"):  # Meta pool
                return (
                    INFORMATION_FOR_POOL[address.lower()]["BASE_N_COINS"]
                    + INFORMATION_FOR_POOL[address.lower()]["N_COINS"]
                    - 1
                )
            else:
                raise ValueError(f"Invalid coins_signature: {coins_signature}")

        calls = []
        for address in pool_addresses:
            for i in range(get_count(address)):
                if coins_signature.startswith("base_coins"):  # Meta pool
                    max_coin = INFORMATION_FOR_POOL[address.lower()]["N_COINS"] - 1
                    if i < max_coin:
                        # Exclude the last coin which is the LP token
                        call = Call(
                            address,
                            ["coins(uint256)(address)", i],
                            [(address + "_" + str(i), lambda x: x)],
                        )
                    else:
                        call = Call(
                            address,
                            [coins_signature, i - max_coin],
                            [(address + "_" + str(i), lambda x: x)],
                        )
                    calls.append(call)
                else:
                    call = Call(
                        address,
                        [coins_signature, i],
                        [(address + "_" + str(i), lambda x: x)],
                    )
                    calls.append(call)

        result = multicall_by_chunk(self.http_endpoint, calls)

        formatted_result = {}
        for k, v in result.items():
            address = k[:-2]
            if address not in formatted_result:
                formatted_result[address] = []
            formatted_result[address].append(v)

        for k, v in formatted_result.items():
            formatted_result[k] = tuple(v)

        return formatted_result

    def fetch_pools_fee(self, addresses: List[str]):
        """
        Fetch fee from Curve pool

        Args:
            addresses: list of pool addresses

        Returns: dict of pool address and fee (fee is 1e10)
        """
        calls = []
        for address in addresses:
            call = Call(address, "fee()(uint256)", [(address, lambda x: x)])
            calls.append(call)

        result = multicall_by_chunk(self.http_endpoint, calls)
        return result

    @memoize(maxsize=512)
    def calculate_price(
        self,
        pool_info: PoolInfo,
        token0: str,
        token1: str,
        decimals0: int,
        decimals1: int,
    ):
        amount_in = 10**decimals0
        amount_out = self.calculate_amount_out(pool_info, amount_in, token0, token1)

        price = amount_out / amount_in
        return price

    def calculate_slippage(
        self,
        pool_info: PoolInfo,
        amount_in: int,
        token0: str,
        token1: str,
        decimals0: int,
        decimals1: int,
    ) -> float:
        amount = self.calculate_amount_out(pool_info, 10**decimals0, token0, token1)
        price = (amount / (10 ** (decimals1 - decimals0))) / (10**decimals0)
        slippage_amount = self.calculate_amount_out(
            pool_info, amount_in, token0, token1
        )
        slippage_price = (slippage_amount / (10 ** (decimals1 - decimals0))) / (
            10**decimals0
        )
        slippage = (price - slippage_price) / price
        return slippage

    def calculate_amount_out(
        self, pool_info: PoolInfo, amount_in: int, token0: str, token1: str, **kwargs
    ) -> int:
        pool_address = pool_info.address
        reserve_info = pool_info.reserve_info
        A = reserve_info["A"]
        balances = copy.deepcopy(reserve_info["balances"])
        information_for_pool = INFORMATION_FOR_POOL[pool_address.lower()]
        token0_index = pool_info.token_addresses.index(token0)
        token1_index = pool_info.token_addresses.index(token1)
        get_y_minus_one = (
            -1 if information_for_pool.get("GET_Y_MINUS_ONE", False) else 0
        )
        get_d_plus_one = information_for_pool.get("GET_D_PLUS_ONE", False)

        precision_mul = information_for_pool["PRECISION_MUL"]
        xp = []
        if information_for_pool["TYPE"] == "USE_BALANCES":
            xp = copy.deepcopy(balances)
            x = xp[token0_index] + amount_in
            y = get_y(A, token0_index, token1_index, x, xp, get_d_plus_one)
            dy = xp[token1_index] - y + get_y_minus_one

            _fee = pool_info.fee * dy // FEE_DENOMINATOR
            return int(dy - _fee)
        if information_for_pool["TYPE"] == "USE_RATES":
            for i in range(len(balances)):
                xp.append(precision_mul[i] * balances[i])
            x = xp[token0_index] + (amount_in * precision_mul[token0_index])
            y = get_y(A, token0_index, token1_index, x, xp)
            dy = (xp[token1_index] - y + get_y_minus_one) // precision_mul[token1_index]
            _fee = pool_info.fee * dy // FEE_DENOMINATOR
            return int(dy - _fee)

        elif information_for_pool["TYPE"] == "AAVE":
            for i in range(len(balances)):
                xp.append(precision_mul[i] * balances[i])
            x = xp[token0_index] + (amount_in * precision_mul[token0_index])
            A *= information_for_pool["A_PRECISION"]
            y = get_y(
                A,
                token0_index,
                token1_index,
                x,
                xp,
                information_for_pool["A_PRECISION"],
            )
            dy = (xp[token1_index] - y + get_y_minus_one) // precision_mul[token1_index]
            offpeg_fee_multiplier = reserve_info["offpeg_fee_multiplier"]
            if offpeg_fee_multiplier <= FEE_DENOMINATOR:
                _fee = pool_info.fee
            else:
                xpi = (xp[token0_index] + x) // 2
                xpj = (xp[token1_index] + y) // 2

                def _dynamic_fee(xpi, xpj, _fee, _feemul):
                    xps2 = xpi + xpj
                    xps2 *= xps2
                    return (_feemul * _fee) // (
                        (_feemul - FEE_DENOMINATOR) * 4 * xpi * xpj // xps2
                        + FEE_DENOMINATOR
                    )

                _fee = _dynamic_fee(xpi, xpj, pool_info.fee, offpeg_fee_multiplier)
                _fee = _fee * dy // FEE_DENOMINATOR
            return int(dy - _fee)

        elif information_for_pool["TYPE"] == "STORED_RATES":
            http_provider = Web3(Web3.HTTPProvider(self.http_endpoint))
            block_number = http_provider.eth.block_number
            rates = []
            for i in range(len(balances)):
                _rate = reserve_info["exchangeRateStored"][i]
                _rate += (
                    _rate
                    * reserve_info["supplyRatePerBlock"][i]
                    * (block_number - reserve_info["accrualBlockNumber"][i])
                    // PRECISION
                )
                rates.append(_rate)
                rates[i] *= precision_mul[i]
            for i in range(len(balances)):
                xp.append(rates[i] * balances[i] // PRECISION)

            if token0.lower() in [
                i.lower() for i in information_for_pool["COINS"]
            ]:  # get_y
                x = xp[token0_index] + (amount_in * rates[token0_index] // PRECISION)
                A *= information_for_pool["A_PRECISION"]
                y = get_y(
                    A,
                    token0_index,
                    token1_index,
                    x,
                    xp,
                    information_for_pool["A_PRECISION"],
                )
                dy = xp[token1_index] - y + get_y_minus_one
                return (
                    (dy - (pool_info.fee * dy // FEE_DENOMINATOR))
                    * PRECISION
                    // rates[token1_index]
                )
            else:  # get_y_underlying
                x = xp[token0_index] + (amount_in * precision_mul[token0_index])
                A *= information_for_pool["A_PRECISION"]
                y = get_y(
                    A,
                    token0_index,
                    token1_index,
                    x,
                    xp,
                    information_for_pool["A_PRECISION"],
                )
                dy = xp[token1_index] - y + get_y_minus_one
                _fee = pool_info.fee * dy // FEE_DENOMINATOR
                return int(dy - _fee) // precision_mul[token1_index]
        elif information_for_pool["TYPE"] == "USE_LENDING":
            http_provider = Web3(Web3.HTTPProvider(self.http_endpoint))
            block_number = http_provider.eth.block_number
            rates = copy.deepcopy(precision_mul)
            for i in range(len(balances)):
                if information_for_pool["USE_LENDING"][i]:
                    _rate = reserve_info["exchangeRateStored"][i]
                    _rate += (
                        _rate
                        * reserve_info["supplyRatePerBlock"][i]
                        * (block_number - reserve_info["accrualBlockNumber"][i])
                        // PRECISION
                    )
                    rates[i] *= _rate
                else:
                    rates[i] *= PRECISION
            for i in range(len(balances)):
                xp.append(rates[i] * balances[i] // PRECISION)

            if token0.lower() in [
                i.lower() for i in information_for_pool["COINS"]
            ]:  # get_y
                x = xp[token0_index] + (amount_in * rates[token0_index] // PRECISION)
                y = get_y(A, token0_index, token1_index, x, xp)
                dy = (
                    (xp[token1_index] - y + get_y_minus_one)
                    * PRECISION
                    // rates[token1_index]
                )
                _fee = pool_info.fee * dy // FEE_DENOMINATOR
                return int(dy - _fee)
            else:  # get_y_underlying
                x = xp[token0_index] + (amount_in * precision_mul[token0_index])
                y = get_y(A, token0_index, token1_index, x, xp)
                dy = (xp[token1_index] - y + get_y_minus_one) // precision_mul[
                    token1_index
                ]
                _fee = pool_info.fee * dy // FEE_DENOMINATOR
                return int(dy - _fee)

        elif information_for_pool["TYPE"] == "USE_LENDING_1":
            rates = copy.deepcopy(precision_mul)
            n_coins = information_for_pool["N_COINS"]
            for i in range(len(balances)):
                if information_for_pool["USE_LENDING"][i]:
                    _rate = reserve_info["getPricePerFullShare"][i]
                    rates[i] *= _rate
                else:
                    rates[i] *= PRECISION
            for i in range(len(balances)):
                xp.append(rates[i] * balances[i] // PRECISION)

            lowered_token = [i.lower() for i in information_for_pool["COINS"]]
            if token0 in lowered_token and token1 in lowered_token:  # get_y
                x = xp[token0_index] + (amount_in * rates[token0_index] // PRECISION)
                y = get_y(A, token0_index, token1_index, x, xp, n_coins=n_coins)
                dy = (
                    (xp[token1_index] - y + get_y_minus_one)
                    * PRECISION
                    // rates[token1_index]
                )
                _fee = pool_info.fee * dy // FEE_DENOMINATOR
                return dy - _fee
            else:  # get_y_underlying
                x = xp[token0_index] + (amount_in * precision_mul[token0_index])
                y = get_y(A, token0_index, token1_index, x, xp, n_coins=n_coins)
                dy = (xp[token1_index] - y + get_y_minus_one) // precision_mul[
                    token1_index
                ]
                _fee = pool_info.fee * dy // FEE_DENOMINATOR
                return dy - _fee
        elif information_for_pool["TYPE"] == "USE_RATE_MULTIPLIERS":
            rates = copy.deepcopy(information_for_pool["RATE_MULTIPLIERS"])

            def _xp_mem(_rates, balances):
                _xp = []
                for _i in range(len(balances)):
                    _xp.append(_rates[_i] * balances[_i] // PRECISION)
                return _xp

            xp = _xp_mem(rates, balances)
            x = xp[token0_index] + (amount_in * rates[token0_index] // PRECISION)
            y = get_y(A, token0_index, token1_index, x, xp)
            dy = xp[token1_index] - y + get_y_minus_one
            _fee = pool_info.fee * dy // FEE_DENOMINATOR
            return (dy - _fee) * PRECISION // rates[token1_index]

        elif information_for_pool["TYPE"] == "BASE_VIRTUAL_PRICE":
            if (
                time.time()
                > reserve_info["base_cache_updated"]
                + information_for_pool["BASE_CACHE_EXPIRES"]
            ):
                base_virtual_price = reserve_info["base_pool_get_virtual_price"]
            else:
                base_virtual_price = reserve_info["base_virtual_price"]

            lowered_tokens = [i.lower() for i in information_for_pool["COINS"]]
            if (
                token0.lower() in lowered_tokens and token1.lower() in lowered_tokens
            ):  # get_y
                rates = copy.deepcopy(precision_mul)
                rates = [i * PRECISION for i in rates]
                rates[-1] = base_virtual_price
                _rates = copy.deepcopy(rates)
                for i in range(len(balances)):
                    xp.append(_rates[i] * balances[i] // PRECISION)
                x = xp[token0_index] + (amount_in * rates[token0_index] // PRECISION)
                A *= information_for_pool["A_PRECISION"]
                y = get_y(
                    A,
                    token0_index,
                    token1_index,
                    x,
                    xp,
                    information_for_pool["A_PRECISION"],
                )
                dy = xp[token1_index] - y + get_y_minus_one
                _fee = pool_info.fee * dy // FEE_DENOMINATOR
                return int(dy - _fee) * PRECISION // rates[token1_index]
            else:  # get_y_underlying
                n_coins = information_for_pool["N_COINS"]
                max_coin = n_coins - 1
                xp = copy.deepcopy(precision_mul)
                xp = [i * PRECISION for i in xp]
                xp[max_coin] = base_virtual_price
                for i in range(n_coins):
                    xp[i] = xp[i] * balances[i] // PRECISION

                base_pool_n_coins = INFORMATION_FOR_POOL[
                    information_for_pool["base_pool"].lower()
                ]["N_COINS"]
                base_pool_address = information_for_pool["base_pool"].lower()
                base_i = token0_index - max_coin
                base_j = token1_index - max_coin
                meta_i = max_coin
                meta_j = max_coin
                if base_i < 0:
                    meta_i = token0_index
                if base_j < 0:
                    meta_j = token1_index

                if base_i < 0:
                    x = xp[token0_index] + (amount_in * precision_mul[token0_index])
                else:
                    if base_j < 0:
                        base_inputs = [
                            0 for _ in range(information_for_pool["BASE_N_COINS"])
                        ]
                        base_inputs[base_i] = amount_in

                        def calc_token_amount(amounts, deposit):
                            _balances = copy.deepcopy(
                                reserve_info["base_pool_balances"]
                            )
                            amp = reserve_info["base_pool_A"]

                            def _xp_mem(_balances):
                                _xp = INFORMATION_FOR_POOL[base_pool_address][
                                    "PRECISION_MUL"
                                ].copy()
                                for _i in range(len(_balances)):
                                    _xp[_i] *= _balances[_i]
                                return _xp

                            def get_D_mem(_balances, _amp):
                                return get_D(_xp_mem(_balances), _amp)

                            D0 = get_D_mem(_balances, amp)
                            for _i in range(len(_balances)):
                                if deposit:
                                    _balances[_i] += amounts[_i]
                                else:
                                    _balances[_i] -= amounts[_i]
                            D1 = get_D_mem(_balances, amp)
                            token_amount = reserve_info["base_pool_lp_total_supply"]
                            if deposit:
                                diff = D1 - D0
                            else:
                                diff = D0 - D1
                            return diff * token_amount // D0

                        x = (
                            calc_token_amount(base_inputs, True)
                            * base_virtual_price
                            // PRECISION
                        )
                        x -= x * reserve_info["base_pool_fee"] // (2 * FEE_DENOMINATOR)

                        x += xp[max_coin]
                    else:
                        # get_y of base pool
                        _rates = copy.deepcopy(
                            INFORMATION_FOR_POOL[base_pool_address]["PRECISION_MUL"]
                        )
                        _rates = [i * PRECISION for i in _rates]
                        _xp = []
                        for _i in range(base_pool_n_coins):
                            _xp.append(
                                reserve_info["base_pool_balances"][_i]
                                * _rates[_i]
                                // PRECISION
                            )
                        x = _xp[base_i] + (amount_in * _rates[base_i] // PRECISION)
                        y = get_y(
                            reserve_info["base_pool_A"],
                            base_i,
                            base_j,
                            x,
                            _xp,
                            n_coins=base_pool_n_coins,
                        )
                        base_pool_get_y_minus_one = (
                            -1
                            if INFORMATION_FOR_POOL[base_pool_address][
                                "GET_Y_MINUS_ONE"
                            ]
                            else 0
                        )
                        dy = (
                            (_xp[base_j] - y + base_pool_get_y_minus_one)
                            * PRECISION
                            // _rates[base_j]
                        )
                        _fee = reserve_info["base_pool_fee"] * dy // FEE_DENOMINATOR
                        return dy - _fee

                A *= information_for_pool["A_PRECISION"]
                y = get_y(
                    A,
                    meta_i,
                    meta_j,
                    x,
                    xp,
                    a_precision=information_for_pool["A_PRECISION"],
                )
                dy = xp[meta_j] - y + get_y_minus_one
                dy = dy - pool_info.fee * dy // FEE_DENOMINATOR
                if base_j < 0:
                    dy = dy // precision_mul[meta_j]
                else:
                    dy = calc_withdraw_one_coin(
                        dy * PRECISION // base_virtual_price,
                        base_j,
                        reserve_info,
                        base_pool_address,
                        base_pool_n_coins,
                    )[0]

                return dy


class CurveStableSwapInterface1(_CurveBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]):
        balances_signature = "balances(int128)(uint256)"
        return self._fetch_pools_reserve_info(pool_addresses, balances_signature)

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        coins_signature = "coins(int128)(address)"
        return self._fetch_pools_token_addresses(pool_addresses, coins_signature)


class CurveStableSwapInterface1Underlying(_CurveBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]):
        balances_signature = "balances(int128)(uint256)"
        return self._fetch_pools_reserve_info(pool_addresses, balances_signature)

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        coins_signature = "underlying_coins(int128)(address)"
        return self._fetch_pools_token_addresses(pool_addresses, coins_signature)


class CurveStableSwapInterface2(_CurveBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]):
        balances_signature = "balances(uint256)(uint256)"
        return self._fetch_pools_reserve_info(pool_addresses, balances_signature)

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        coins_signature = "coins(uint256)(address)"
        return self._fetch_pools_token_addresses(pool_addresses, coins_signature)


class CurveStableSwapInterface2Underlying(_CurveBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]):
        balances_signature = "balances(uint256)(uint256)"
        return self._fetch_pools_reserve_info(pool_addresses, balances_signature)

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        coins_signature = "underlying_coins(uint256)(address)"
        return self._fetch_pools_token_addresses(pool_addresses, coins_signature)


class CurveStableSwapMeta(_CurveBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]):
        balances_signature = "balances(uint256)(uint256)"
        return self._fetch_pools_reserve_info(pool_addresses, balances_signature)

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        coins_signature = "coins(uint256)(address)"
        return self._fetch_pools_token_addresses(pool_addresses, coins_signature)


class CurveSTableSwapMetaUnderlying(_CurveBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]):
        balances_signature = "balances(uint256)(uint256)"
        return self._fetch_pools_reserve_info(pool_addresses, balances_signature)

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        coins_signature = "base_coins(uint256)(address)"
        return self._fetch_pools_token_addresses(pool_addresses, coins_signature)
