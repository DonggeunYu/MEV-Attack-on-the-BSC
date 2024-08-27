from .curve_crypto_swap import CurveCryptoSwap
from ..multicall import Call
from ..utils import multicall_by_chunk
from ..types import PoolInfo
from typing import List, Dict
import copy
from .curve_pool_info import INFORMATION_FOR_POOL

PRECISIONS = 0
PRECISION = 10**18


class CurveThreeCryptoSwap(CurveCryptoSwap):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str]) -> Dict:
        A_signature = "A()(uint256)"
        gamma_signature = "gamma()(uint256)"
        price_scale_signature = "price_scale(uint256)(uint256)"
        balances_signature = "balances(uint256)(uint256)"
        D_signature = "D()(uint256)"
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
                    Call(address, [D_signature], [(address + "_D", lambda x: x)]),
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

            for idx, i in enumerate(range(INFORMATION_FOR_POOL[address]["N_COINS"])):
                calls.append(
                    Call(
                        address,
                        [balances_signature, i],
                        [(address + f"_balance_{i}", lambda x: x)],
                    )
                )
                if idx < INFORMATION_FOR_POOL[address]["N_COINS"] - 1:
                    calls.append(
                        Call(
                            address,
                            [price_scale_signature, i],
                            [(address + f"_price_scale_{i}", lambda x: x)],
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
            elif k[address_length + 1 :].startswith("price_scale"):
                if "price_scale" not in formmated_result[address]:
                    count = INFORMATION_FOR_POOL[address]["N_COINS"]
                    formmated_result[address]["price_scale"] = [0] * (count - 1)
                formmated_result[address]["price_scale"][int(k[-1])] = v
                continue

            formmated_result[address][k[address_length + 1 :]] = v

        return formmated_result

    def calculate_amount_out(
        self, pool_info: PoolInfo, amount_in: int, token0: str, token1: str, **kwargs
    ):
        pool_address = pool_info.address
        reserve_info = pool_info.reserve_info
        information_for_pool = INFORMATION_FOR_POOL[pool_address]
        n_coins = information_for_pool["N_COINS"]
        precisions = information_for_pool["PRECISIONS"]
        balances = reserve_info["balances"]
        price_scale = reserve_info["price_scale"]
        A = reserve_info["A"]
        gamma = reserve_info["gamma"]
        D = reserve_info["D"]
        fee_gamma = reserve_info["fee_gamma"]
        mid_fee = reserve_info["mid_fee"]
        out_fee = reserve_info["out_fee"]

        token0_index = pool_info.token_addresses.index(token0)
        token1_index = pool_info.token_addresses.index(token1)

        xp = copy.deepcopy(balances)
        xp[token0_index] += amount_in
        xp[0] *= precisions[0]
        for k in range(n_coins - 1):
            xp[k + 1] = xp[k + 1] * price_scale[k] * precisions[k + 1] // PRECISION

        y = self._newton_y(A, gamma, copy.deepcopy(xp), D, token1_index, n_coins)
        dy = xp[token1_index] - y - 1
        xp[token1_index] = y
        if token1_index > 0:
            dy = dy * PRECISION // price_scale[token1_index - 1]
        dy = dy // precisions[token1_index]
        dy -= self._fee(xp, fee_gamma, mid_fee, out_fee, n_coins) * dy // 10**10

        return dy

    @staticmethod
    def _newton_y(ANN, gamma, x, D, i, n_coins):
        A_MULTIPLIER = 10000
        MIN_A = n_coins**n_coins * A_MULTIPLIER // 10
        MAX_A = n_coins**n_coins * A_MULTIPLIER * 100000
        MIN_GAMMA = 10**10
        MAX_GAMMA = 2 * 10**16

        assert ANN > MIN_A - 1 and ANN < MAX_A + 1  # dev: unsafe values A
        assert (
            gamma > MIN_GAMMA - 1 and gamma < MAX_GAMMA + 1
        )  # dev: unsafe values gamma
        assert D > 10**17 - 1 and D < 10**15 * 10**18 + 1  # dev: unsafe values D
        for k in range(3):
            if k != i:
                frac = x[k] * 10**18 // D
                assert (frac > 10**16 - 1) and (
                    frac < 10**20 + 1
                )  # dev: unsafe values x[i]

        y = D // n_coins
        K0_i = 10**18
        S_i = 0

        x_sorted = x
        x_sorted[i] = 0
        x_sorted = CurveThreeCryptoSwap.sort(x_sorted, n_coins)  # From high to low

        convergence_limit = max(max(x_sorted[0] // 10**14, D // 10**14), 100)
        for j in range(2, n_coins + 1):
            _x = x_sorted[n_coins - j]
            y = y * D // (_x * n_coins)  # Small _x first
            S_i += _x
        for j in range(n_coins - 1):
            K0_i = K0_i * x_sorted[j] * n_coins // D  # Large _x first

        for j in range(255):
            y_prev = y

            K0 = K0_i * y * n_coins // D
            S = S_i + y

            _g1k0 = gamma + 10**18
            if _g1k0 > K0:
                _g1k0 = _g1k0 - K0 + 1
            else:
                _g1k0 = K0 - _g1k0 + 1

            # D / (A * N**N) * _g1k0**2 / gamma**2
            mul1 = 10**18 * D // gamma * _g1k0 // gamma * _g1k0 * A_MULTIPLIER // ANN

            # 2*K0 / _g1k0
            mul2 = 10**18 + (2 * 10**18) * K0 // _g1k0

            yfprime = 10**18 * y + S * mul2 + mul1
            _dyfprime = D * mul2
            if yfprime < _dyfprime:
                y = y_prev // 2
                continue
            else:
                yfprime -= _dyfprime
            fprime = yfprime // y

            # y -= f / f_prime;  y = (y * fprime - f) / fprime
            # y = (yfprime + 10**18 * D - 10**18 * S) // fprime + mul1 // fprime * (10**18 - K0) // K0
            y_minus = mul1 // fprime
            y_plus = (yfprime + 10**18 * D) // fprime + y_minus * 10**18 // K0
            y_minus += 10**18 * S // fprime

            if y_plus < y_minus:
                y = y_prev // 2
            else:
                y = y_plus - y_minus

            diff = 0
            if y > y_prev:
                diff = y - y_prev
            else:
                diff = y_prev - y
            if diff < max(convergence_limit, y // 10**14):
                frac = y * 10**18 // D
                assert (frac > 10**16 - 1) and (
                    frac < 10**20 + 1
                )  # dev: unsafe value for y
                return y

        raise "Did not converge"

    @staticmethod
    def sort(A0, n_coins):
        """
        Insertion sort from high to low
        """
        A = copy.deepcopy(A0)
        for i in range(1, n_coins):
            x = A[i]
            cur = i
            for j in range(n_coins):
                y = A[cur - 1]
                if y > x:
                    break
                A[cur] = y
                cur -= 1
                if cur == 0:
                    break
            A[cur] = x
        return A

    @staticmethod
    def _fee(xp, fee_gamma, mid_fee, out_fee, n_coins):
        f = CurveThreeCryptoSwap._reduction_coefficient(xp, fee_gamma, n_coins)
        return (mid_fee * f + out_fee * (10**18 - f)) // 10**18

    @staticmethod
    def _reduction_coefficient(x, fee_gamma, n_coins):
        """
        fee_gamma / (fee_gamma + (1 - K))
        where
        K = prod(x) / (sum(x) / N)**N
        (all normalized to 1e18)
        """
        K = 10**18
        S = 0
        for x_i in x:
            S += x_i
        # Could be good to pre-sort x, but it is used only for dynamic fee,
        # so that is not so important
        for x_i in x:
            K = K * n_coins * x_i // S
        if fee_gamma > 0:
            K = fee_gamma * 10**18 // (fee_gamma + 10**18 - K)
        return K
