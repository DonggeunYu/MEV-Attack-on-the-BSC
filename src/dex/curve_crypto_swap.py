import copy
from typing import Dict, List
from ..multicall import Call
from ..utils import multicall_by_chunk
from .dex import DexBase
from .curve_pool_info import INFORMATION_FOR_POOL
from ..types import PoolInfo
from ..utils import memoize

PRECISIONS = 0
PRECISION = 10**18


class CurveCryptoSwap(DexBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]) -> Dict:
        A_signature = "A()(uint256)"
        gamma_signature = "gamma()(uint256)"
        price_scale_signature = "price_scale()(uint256)"
        balances_signature = "balances(uint256)(uint256)"
        D_signature = "D()(uint256)"
        future_A_gamma_time = "future_A_gamma_time()(uint256)"
        fee_gamma_signature = "fee_gamma()(uint256)"
        mid_fee_signature = "mid_fee()(uint256)"
        out_fee_signature = "out_fee()(uint256)"

        address_length = len(pool_addresses[0])

        calls = []
        for address in pool_addresses:
            calls.extend(
                [
                    Call(address, [A_signature], [(address + "_A", lambda x: x)]),
                    Call(
                        address, [gamma_signature], [(address + "_gamma", lambda x: x)]
                    ),
                    Call(
                        address,
                        [price_scale_signature],
                        [(address + "_price_scale", lambda x: x)],
                    ),
                    Call(address, [D_signature], [(address + "_D", lambda x: x)]),
                    Call(
                        address,
                        [future_A_gamma_time],
                        [(address + "_future_A_gamma_time", lambda x: x)],
                    ),
                    Call(
                        address,
                        [fee_gamma_signature],
                        [(address + "_fee_gamma", lambda x: x)],
                    ),
                    Call(
                        address,
                        [mid_fee_signature],
                        [(address + "_mid_fee", lambda x: x)],
                    ),
                    Call(
                        address,
                        [out_fee_signature],
                        [(address + "_out_fee", lambda x: x)],
                    ),
                ]
            )

            for i in range(INFORMATION_FOR_POOL[address]["N_COINS"]):
                calls.append(
                    Call(
                        address,
                        [balances_signature, i],
                        [(address + f"_balance_{i}", lambda x: x)],
                    )
                )

        result = multicall_by_chunk(self.http_endpoint, calls)

        formmated_result = {}
        for k, v in result.items():
            address = k[:address_length]
            if address not in formmated_result:
                formmated_result[address] = {}

            if k[address_length + 1 :].startswith("balance"):
                if "balances" not in formmated_result[address]:
                    count = INFORMATION_FOR_POOL[address]["N_COINS"]
                    formmated_result[address]["balances"] = [0] * count
                formmated_result[address]["balances"][int(k[-1])] = v
                continue

            formmated_result[address][k[address_length + 1 :]] = v

        return formmated_result

    def fetch_pools_token_addresses(self, pool_addresses: List[str]) -> Dict:
        coins_signature = "coins(uint256)(address)"

        address_length = len(pool_addresses[0])

        calls = []
        for address in pool_addresses:
            for i in range(INFORMATION_FOR_POOL[address]["N_COINS"]):
                calls.append(
                    Call(
                        address,
                        [coins_signature, i],
                        [(address + f"_coin_{i}", lambda x: x)],
                    )
                )

        result = multicall_by_chunk(self.http_endpoint, calls)

        formmated_result = {}
        for k, v in result.items():
            address = k[:address_length]
            if address not in formmated_result:
                count = INFORMATION_FOR_POOL[address]["N_COINS"]
                formmated_result[address] = [0] * count

            formmated_result[address][int(k[-1])] = v

        for k, v in formmated_result.items():
            formmated_result[k] = tuple(v)

        return formmated_result

    def fetch_pools_fee(self, pool_addresses: List[str]) -> Dict:
        # dynamic fee
        return {address: 0 for address in pool_addresses}

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
        information_for_pool = INFORMATION_FOR_POOL[pool_address]
        n_coins = information_for_pool["N_COINS"]
        balances = reserve_info["balances"]
        price_scale = reserve_info["price_scale"]
        A = reserve_info["A"]
        gamma = reserve_info["gamma"]
        D = reserve_info["D"]
        future_A_gamma_time = reserve_info["future_A_gamma_time"]
        fee_gamma = reserve_info["fee_gamma"]
        mid_fee = reserve_info["mid_fee"]
        out_fee = reserve_info["out_fee"]

        token0_index = pool_info.token_addresses.index(token0)
        token1_index = pool_info.token_addresses.index(token1)

        def _get_precisions():
            p0 = PRECISIONS
            p1 = 10 ** (p0 >> 8)
            p0 = 10 ** (p0 & 255)
            return [p0, p1]

        def _xp(balances, price_scale):
            precisions = _get_precisions()
            return [
                balances[0] * precisions[0],
                balances[1] * precisions[1] * price_scale // PRECISION,
            ]

        precisions = _get_precisions()
        _price_scale = price_scale * precisions[1]
        xp = copy.deepcopy(balances)

        A_gamma = [A, gamma]
        D = D
        if future_A_gamma_time > 0:
            D = self._newton_D(
                A_gamma[0], A_gamma[1], _xp(balances, price_scale), n_coins
            )

        xp[token0_index] += amount_in
        xp = [xp[0] * precisions[0], xp[1] * _price_scale // PRECISION]
        y = self._newton_y(A_gamma[0], A_gamma[1], xp, D, token1_index, n_coins)
        dy = xp[token1_index] - y - 1

        xp[token1_index] = y
        if token1_index > 0:
            dy = dy * PRECISION // _price_scale
        else:
            dy = dy // precisions[0]
        dy -= self._fee(xp, fee_gamma, mid_fee, out_fee, n_coins) * dy // 10**10

        return dy

    @staticmethod
    def _fee(xp, fee_gamma, mid_fee, out_fee, n_coins):
        f = xp[0] + xp[1]  # sum
        f = (
            fee_gamma
            * 10**18
            // (
                fee_gamma
                + 10**18
                - (10**18 * n_coins**n_coins) * xp[0] // f * xp[1] // f
            )
        )
        return (mid_fee * f + out_fee * (10**18 - f)) // 10**18

    @staticmethod
    def _newton_D(ANN, gamma, x_unsorted, n_coins):
        A_MULTIPLIER = 10000
        MIN_A = n_coins**n_coins * A_MULTIPLIER // 10
        MAX_A = n_coins**n_coins * A_MULTIPLIER * 100000
        MIN_GAMMA = 10**10
        MAX_GAMMA = 2 * 10**16
        assert ANN > MIN_A - 1 and ANN < MAX_A + 1
        assert gamma > MIN_GAMMA - 1 and gamma < MAX_GAMMA + 1

        x = x_unsorted
        if x[0] < x[1]:
            x = [x_unsorted[1], x_unsorted[0]]

        assert x[0] > 10**9 - 1 and x[0] < 10**15 * 10**18 + 1
        assert x[1] * 10**18 // x[0] > 10**14 - 1

        D = n_coins * CurveCryptoSwap._geometric_mean(x, False, n_coins)
        S = x[0] + x[1]

        for i in range(255):
            D_prev = D

            K0 = (10**18 * n_coins**2) * x[0] // D * x[1] // D

            _g1k0 = gamma + 10**18
            if _g1k0 > K0:
                _g1k0 = _g1k0 - K0 + 1
            else:
                _g1k0 = K0 - _g1k0 + 1

            mul1 = 10**18 * D // gamma * _g1k0 // gamma * _g1k0 * A_MULTIPLIER // ANN

            mul2 = (2 * 10**18) * n_coins * K0 // _g1k0

            neg_fprime = (
                (S + S * mul2 // 10**18) + mul1 * n_coins // K0 - mul2 * D // 10**18
            )

            D_plus = D * (neg_fprime + S) // neg_fprime
            D_minus = D * D // neg_fprime
            if 10**18 > K0:
                D_minus += D * (mul1 // neg_fprime) // 10**18 * (10**18 - K0) // K0
            else:
                D_minus -= D * (mul1 // neg_fprime) // 10**18 * (K0 - 10**18) // K0

            if D_plus < D_minus:
                diff = D - D_prev
            else:
                diff = D_prev - D

            if diff * 10**14 < max(10**16, D):
                for _x in x:
                    frac = _x * 10**18 // D
                    assert (frac > 10**16 - 1) and (frac < 10**20 + 1)
                return D

    @staticmethod
    def _geometric_mean(unsorted_x, sort, n_coins):
        x = unsorted_x
        if sort and x[0] < x[1]:
            x = [unsorted_x[1], unsorted_x[0]]

        D = x[0]
        diff = 0
        for i in range(255):
            D_prev = D
            D = (D + x[0] * x[1] // D) // n_coins
            if D > D_prev:
                diff = D - D_prev
            else:
                diff = D_prev - D
            if diff <= 1 or diff * 10**18 < D:
                return D

    @staticmethod
    def _newton_y(ANN, gamma, x, D, i, n_coins):
        A_MULTIPLIER = 10000
        MIN_A = n_coins**n_coins * A_MULTIPLIER // 10
        MAX_A = n_coins**n_coins * A_MULTIPLIER * 100000
        MIN_GAMMA = 10**10
        MAX_GAMMA = 2 * 10**16
        assert ANN > MIN_A - 1 and ANN < MAX_A + 1
        assert gamma > MIN_GAMMA - 1 and gamma < MAX_GAMMA + 1
        assert D > 10**17 - 1 and D < 10**15 * 10**18 + 1

        x_j = x[1 - i]
        y = D**2 // (x_j * n_coins**2)
        K0_i = (10**18 * n_coins) * x_j // D

        assert (K0_i > 10**16 * n_coins - 1) and (K0_i < 10**20 * n_coins + 1)

        convergence_limit = max(max(x_j // 10**14, D // 10**14), 100)

        for j in range(255):
            y_prev = y

            K0 = K0_i * y * n_coins // D
            S = x_j + y

            _g1k0 = gamma + 10**18
            if _g1k0 > K0:
                _g1k0 = _g1k0 - K0 + 1
            else:
                _g1k0 = K0 - _g1k0 + 1

            mul1 = 10**18 * D // gamma * _g1k0 // gamma * _g1k0 * A_MULTIPLIER // ANN

            mul2 = 10**18 + (2 * 10**18) * K0 // _g1k0

            yfprime = 10**18 * y + S * mul2 + mul1
            _dyfprime = D * mul2
            if yfprime < _dyfprime:
                y = y_prev // 2
                continue
            else:
                yfprime -= _dyfprime

            fprime = yfprime // y

            y_minus = mul1 // fprime
            y_plus = (yfprime + 10**18 * D) // fprime + y_minus * 10**18 // K0
            y_minus += 10**18 * S // fprime

            if y_plus < y_minus:
                y = y_prev // 2
            else:
                y = y_plus - y_minus

            if y > y_prev:
                diff = y - y_prev
            else:
                diff = y_prev - y

            if diff < max(convergence_limit, y // 10**14):
                frac = y * 10**18 // D
                assert (frac > 10**16 - 1) and (frac < 10**20 + 1)
                return y
