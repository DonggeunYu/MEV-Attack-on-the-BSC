import copy
from typing import Dict, List, Tuple
from ..multicall import Call
from ..utils import multicall_by_chunk
from .dex import DexBase
from .curve_pool_info import INFORMATION_FOR_POOL
from .curve_utils import calc_withdraw_one_coin, get_y
from ..types import PoolInfo
from ..utils import memoize

MAX_COINS = 8
PRECISION = 10**18
A_PRECISION = 100
FEE_DENOMINATOR = 10**10


class CurveStableSwapNGBase(DexBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]) -> Dict:
        A_signature = "A()(uint256)"
        balances_signature = "get_balances()(uint256[])"
        stored_rates_signature = "stored_rates()(uint256[])"
        fee_signature = "fee()(uint256)"
        offpeg_fee_multiplier_signature = "offpeg_fee_multiplier()(uint256)"
        address_length = len(pool_addresses[0])
        calls = []
        for address in pool_addresses:
            assert address.lower() in INFORMATION_FOR_POOL
            calls.extend(
                [
                    Call(address, A_signature, [(address + "_A", lambda x: x)]),
                    Call(
                        address,
                        balances_signature,
                        [(address + "_balances", lambda x: x)],
                    ),
                    Call(
                        address,
                        stored_rates_signature,
                        [(address + "_stored_rates", lambda x: x)],
                    ),
                    Call(address, fee_signature, [(address + "_fee", lambda x: x)]),
                    Call(
                        address,
                        offpeg_fee_multiplier_signature,
                        [(address + "_offpeg_fee_multiplier", lambda x: x)],
                    ),
                ]
            )

            if "BASE_POOL" in INFORMATION_FOR_POOL[address.lower()]:
                base_pool_address = INFORMATION_FOR_POOL[address.lower()]["BASE_POOL"]
                lp_token_address = INFORMATION_FOR_POOL[base_pool_address.lower()][
                    "LP_TOKEN"
                ]

                calls.extend(
                    [
                        Call(
                            lp_token_address,
                            "totalSupply()(uint256)",
                            [(address + "_base_pool_lp_total_supply", lambda x: x)],
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
                for idx, base_pool_coin in enumerate(
                    INFORMATION_FOR_POOL[base_pool_address.lower()]["COINS"]
                ):
                    call = Call(
                        base_pool_address,
                        ["balances(uint256)(uint256)", idx],
                        [
                            (
                                address + "_base_pool_balances_" + str(idx),
                                lambda x: x,
                            ),
                        ],
                    )
                    calls.append(call)
        results = multicall_by_chunk(self.http_endpoint, calls)
        formatted_result = {}
        for k, v in results.items():
            address = k[:address_length]
            if address not in formatted_result:
                formatted_result[address] = {}

            if k[address_length + 1 :].startswith("base_pool_balances_"):
                if "base_pool_balances" not in formatted_result[address]:
                    count = INFORMATION_FOR_POOL[
                        INFORMATION_FOR_POOL[address.lower()]["BASE_POOL"].lower()
                    ]["N_COINS"]
                    formatted_result[address].update(
                        {"base_pool_balances": [0] * count}
                    )
                formatted_result[address]["base_pool_balances"][int(k[-1])] = v
                continue

            formatted_result[address].update({k[len(address) + 1 :]: v})

        return formatted_result

    def _fetch_pools_token_addresses(
        self, pool_addresses: List[str], coins_signature: str
    ) -> Dict[str, Tuple]:
        def get_count(address):
            if coins_signature.startswith("coins"):
                return INFORMATION_FOR_POOL[address.lower()]["N_COINS"]
            elif coins_signature.startswith("BASE_COINS"):  # Meta pool
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
                if coins_signature.startswith("BASE_COINS"):  # Meta pool
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

    def fetch_pools_fee(self, addresses: List[str]) -> Dict:
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

    def calculate_amount_out(
        self, pool_info: PoolInfo, amount_in: int, token0: str, token1: str, **kwargs
    ):
        pool_address = pool_info.address
        reserve_info = pool_info.reserve_info
        information_for_pool = INFORMATION_FOR_POOL[pool_address.lower()]
        token0_index = pool_info.token_addresses.index(token0)
        token1_index = pool_info.token_addresses.index(token1)

        n_coins = information_for_pool["N_COINS"]
        rates = reserve_info["stored_rates"]
        balances = reserve_info["balances"]
        xp = []
        for i in range(n_coins):
            xp.append(rates[i] * balances[i] // PRECISION)

        def get_dy():
            x = xp[token0_index] + (amount_in * rates[token0_index] // PRECISION)
            amp = reserve_info["A"] * A_PRECISION
            D = self._get_D(xp, amp, n_coins)
            y = self.get_y(token0_index, token1_index, x, xp, amp, D, n_coins)
            dy = xp[token1_index] - y - 1

            base_fee = reserve_info["fee"]
            fee_multiplier = reserve_info["offpeg_fee_multiplier"]
            fee = (
                self._dynamic_fee(
                    (xp[token0_index] + x) // 2,
                    (xp[token1_index] + y) // 2,
                    base_fee,
                    fee_multiplier,
                )
                * dy
                // FEE_DENOMINATOR
            )

            return (dy - fee) * PRECISION // rates[token1_index]

        if "COINS" not in information_for_pool:
            return get_dy()
        lowered_tokens = [i.lower() for i in information_for_pool["COINS"]]
        if token0.lower() in lowered_tokens and token1.lower() in lowered_tokens:
            return get_dy()
        else:
            max_coin = n_coins - 1
            base_n_coins = information_for_pool["BASE_N_COINS"]
            base_pool_address = information_for_pool["BASE_POOL"].lower()
            base_i = 0
            base_j = 0
            meta_i = 0
            meta_j = 0

            if token0_index != 0:
                base_i = token0_index - max_coin
                meta_i = 1
            if token1_index != 0:
                base_j = token1_index - max_coin
                meta_j = 1

            if token0_index == 0:
                x = xp[token0_index] + amount_in * rates[0] // (10**18)
            else:
                if token1_index == 0:
                    x = (
                        self._base_calc_token_amount(
                            amount_in,
                            base_i,
                            base_n_coins,
                            information_for_pool["BASE_POOL"].lower(),
                            True,
                            reserve_info,
                        )
                        * rates[1]
                        // PRECISION
                    )
                    x += xp[1]
                else:

                    def _get_dy(i, j, dx):
                        rates = INFORMATION_FOR_POOL[base_pool_address]["PRECISION_MUL"]
                        rates = [_i * PRECISION for _i in rates]
                        base_n_coins = INFORMATION_FOR_POOL[base_pool_address][
                            "N_COINS"
                        ]
                        A = reserve_info["base_pool_A"]

                        fee = reserve_info["base_pool_fee"]
                        xp = []
                        for _i in range(base_n_coins):
                            xp.append(
                                rates[_i]
                                * reserve_info["base_pool_balances"][_i]
                                // PRECISION
                            )

                        x = xp[i] + (dx * rates[i] // PRECISION)
                        y = get_y(A, i, j, x, xp, n_coins=base_n_coins)
                        dy = (xp[j] - y - 1) * PRECISION // rates[j]
                        _fee = fee * dy // FEE_DENOMINATOR
                        return dy - _fee

                    return _get_dy(base_i, base_j, amount_in)

            amp = reserve_info["A"] * A_PRECISION
            D = self._get_D(xp, amp, n_coins)
            y = self.get_y(meta_i, meta_j, x, xp, amp, D, n_coins)
            dy = xp[meta_j] - y - 1

            base_fee = reserve_info["fee"]
            fee_multiplier = reserve_info["offpeg_fee_multiplier"]

            dynamic_fee = self._dynamic_fee(
                (xp[meta_i] + x) // 2, (xp[meta_j] + y) // 2, base_fee, fee_multiplier
            )
            dy = dy - dynamic_fee * dy // FEE_DENOMINATOR

            if token1_index == 0:
                dy = dy * 10**18 // rates[0]
            else:
                base_pool_n_coins = INFORMATION_FOR_POOL[base_pool_address.lower()][
                    "N_COINS"
                ]
                dy = calc_withdraw_one_coin(
                    dy * PRECISION // rates[1],
                    base_j,
                    reserve_info,
                    base_pool_address,
                    base_pool_n_coins,
                )[0]

            return dy

    def _base_calc_token_amount(
        self, dx, base_i, base_n_coins, base_pool, is_deposit, reserve_info
    ):
        def calc_token_amount(amounts, deposit, reserve_info, base_pool_address):
            amp = reserve_info["base_pool_A"]
            base_balances = list(copy.deepcopy(reserve_info["base_pool_balances"]))
            token_amount = reserve_info["base_pool_lp_total_supply"]

            def _xp_mem(_balances):
                _xp = copy.deepcopy(
                    INFORMATION_FOR_POOL[base_pool_address]["PRECISION_MUL"]
                )
                for _i in range(len(_balances)):
                    _xp[_i] *= _balances[_i]
                return _xp

            def get_D_mem(_balances, _amp):
                def _get_D(xp, amp, a_precision=None, n_coins=None) -> int:
                    S = 0
                    for _x in xp:
                        S += _x
                    if S == 0:
                        return 0

                    n_coins = n_coins if n_coins else len(xp)

                    Dprev = 0
                    D = S
                    Ann = amp * n_coins
                    for _i in range(255):
                        D_P = D
                        for _x in xp:
                            D_P = D_P * D // (_x * n_coins)
                        Dprev = D
                        if a_precision:
                            D = (
                                (Ann * S // a_precision + D_P * n_coins)
                                * D
                                // (
                                    (Ann - a_precision) * D // a_precision
                                    + (n_coins + 1) * D_P
                                )
                            )
                        else:
                            D = (
                                (Ann * S + D_P * n_coins)
                                * D
                                // ((Ann - 1) * D + (n_coins + 1) * D_P)
                            )
                        if D > Dprev:
                            if D - Dprev <= 1:
                                break
                        else:
                            if Dprev - D <= 1:
                                break

                    return D

                return _get_D(_xp_mem(_balances), _amp, n_coins=len(_balances))

            D0 = get_D_mem(base_balances, amp)
            n_coins = len(base_balances)
            for i in range(n_coins):
                if deposit:
                    base_balances[i] += amounts[i]
                else:
                    base_balances[i] -= amounts[i]

            D1 = get_D_mem(base_balances, amp)
            if deposit:
                diff = D1 - D0
            else:
                diff = D0 - D1
            return diff * token_amount // D0

        if base_n_coins in [2, 3]:
            base_inputs = [0] * base_n_coins
            base_inputs[base_i] = dx
            return calc_token_amount(base_inputs, is_deposit, reserve_info, base_pool)
        else:
            base_inputs = [0] * MAX_COINS
            base_inputs[base_i] = dx
            return calc_token_amount(base_inputs, is_deposit, reserve_info, base_pool)

    def _get_D(self, _xp, _amp, n_coins):
        S = 0
        for i in range(n_coins):
            S += _xp[i]

        if S == 0:
            return 0

        D = S
        Ann = _amp * n_coins

        for i in range(255):
            D_P = D
            for x in _xp:
                D_P = D_P * D // x
            D_P = D_P // (n_coins**n_coins % (2**256))
            Dprev = D

            D = (
                (Ann * S // A_PRECISION + D_P * n_coins)
                * D
                // ((Ann - A_PRECISION) * D // A_PRECISION + (n_coins + 1) * D_P)
            )

            if D > Dprev:
                if D - Dprev <= 1:
                    break
            else:
                if Dprev - D <= 1:
                    break

        return D

    def get_y(self, i, j, x, xp, _amp, _D, n_coins):
        assert i != j
        assert j >= 0
        assert j < n_coins

        assert i >= 0
        assert i < n_coins

        amp = _amp
        D = _D
        S_ = 0
        _x = 0
        c = D
        Ann = amp * n_coins

        for _i in range(n_coins):
            if _i == i:
                _x = x
            elif _i != j:
                _x = xp[_i]
            else:
                continue
            S_ += _x
            c = c * D // (_x * n_coins)

        c = c * D * A_PRECISION // (Ann * n_coins)
        b = S_ + D * A_PRECISION // Ann
        y = D

        return self.newton_y(b, c, D, y)

    @staticmethod
    def newton_y(b, c, D, _y):
        y = _y

        for _i in range(255):
            y_prev = y
            y = (y * y + c) // (2 * y + b - D)

            if y > y_prev:
                if y - y_prev <= 1:
                    break
            else:
                if y_prev - y <= 1:
                    break

        return y

    @staticmethod
    def _dynamic_fee(xpi, xpj, _fee, _fee_multiplier):
        if _fee_multiplier <= FEE_DENOMINATOR:
            return _fee

        xps2 = (xpi + xpj) ** 2
        return (_fee_multiplier * _fee) // (
            (_fee_multiplier - FEE_DENOMINATOR) * 4 * xpi * xpj // xps2
            + FEE_DENOMINATOR
        )


class CurveStableSwapNGPlain(CurveStableSwapNGBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple]:
        return self._fetch_pools_token_addresses(
            pool_addresses, "coins(uint256)(address)"
        )


class CurveStableSwapNGMeta(CurveStableSwapNGPlain):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)


class CurveStableSwapNGMetaUnderlying(CurveStableSwapNGBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple]:
        return self._fetch_pools_token_addresses(
            pool_addresses, "BASE_COINS(uint256)(address)"
        )
