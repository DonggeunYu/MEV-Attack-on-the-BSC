import math
import time
import copy
import operator
from typing import Dict, List
from ..multicall import Call
from ..utils import multicall_by_chunk
from .curve_pool_info import INFORMATION_FOR_POOL
from ..types import PoolInfo
from .curve_three_crypto_swap import CurveThreeCryptoSwap

PRECISION = 10**18


def unsafe_overflow(x, _type):
    assert isinstance(x, int)
    assert _type in ["uint8", "int8", "uint256", "int256"]

    unsigned = _type.startswith("uint")
    bit = int(_type.lstrip("uint"))

    value = 2**bit
    max_value = value if unsigned else 2 ** (bit - 1)
    min_value = -max_value if not unsigned else 0

    while True:
        if min_value <= x < max_value:
            return x
        x -= value if x > 0 else -value


def unsafe_add(x, y, _type):
    res = operator.add(x, y)
    return unsafe_overflow(res, _type)


def unsafe_sub(x, y, _type):
    res = operator.sub(x, y)
    return unsafe_overflow(res, _type)


def unsafe_mul(x, y, _type):
    res = operator.mul(x, y)
    return unsafe_overflow(res, _type)


def unsafe_div(x, y, _type):
    # EVM div semantics as a python function
    if y == 0:
        return 0
    sign = -1 if (x * y) < 0 else 1
    res = sign * (abs(x) // abs(y))
    return unsafe_overflow(res, _type)


def isqrt(n):
    assert isinstance(n, int)
    return math.isqrt(n)


def pow_mod256(a, b):
    return pow(a, b, 2**256)


class CurveThreeCryptoSwapNG(CurveThreeCryptoSwap):
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
        future_A_gamma_time_signature = "future_A_gamma_time()(uint256)"

        address_length = len(pool_addresses[0])

        calls = []
        for address in pool_addresses:
            n_coins = INFORMATION_FOR_POOL[address]["N_COINS"]
            precisions_signature = f"precisions()(uint256[{n_coins}])"
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
                    Call(
                        address,
                        [precisions_signature],
                        [(address + "_precisions", lambda x: x)],
                    ),
                    Call(
                        address,
                        [future_A_gamma_time_signature],
                        [(address + "_future_A_gamma_time", lambda x: x)],
                    ),
                ]
            )

            for idx, i in enumerate(range(n_coins)):
                calls.append(
                    Call(
                        address,
                        [balances_signature, i],
                        [(address + f"_balance_{i}", lambda x: x)],
                    )
                )
                if idx < n_coins - 1:
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
        reserve_info = pool_info.reserve_info
        information_for_pool = INFORMATION_FOR_POOL[pool_info.address]
        n_coins = information_for_pool["N_COINS"]
        balances = reserve_info["balances"]
        price_scale = reserve_info["price_scale"]
        A = reserve_info["A"]
        gamma = reserve_info["gamma"]
        D = reserve_info["D"]
        fee_gamma = reserve_info["fee_gamma"]
        mid_fee = reserve_info["mid_fee"]
        out_fee = reserve_info["out_fee"]
        precisions = reserve_info["precisions"]
        future_A_gamma_time = reserve_info["future_A_gamma_time"]

        token0_index = pool_info.token_addresses.index(token0)
        token1_index = pool_info.token_addresses.index(token1)

        xp = copy.deepcopy(balances)
        D = self._calc_D_ramp(
            A,
            gamma,
            copy.deepcopy(xp),
            precisions,
            price_scale,
            D,
            future_A_gamma_time,
            n_coins,
        )

        xp[token0_index] += amount_in
        xp[0] *= precisions[0]
        for k in range(n_coins - 1):
            xp[k + 1] = xp[k + 1] * price_scale[k] * precisions[k + 1] // PRECISION

        y_out = self._get_y(A, gamma, xp, D, token1_index, n_coins)

        dy = xp[token1_index] - y_out[0] - 1
        xp[token1_index] = y_out[0]

        if token1_index > 0:
            dy = dy * PRECISION // price_scale[token1_index - 1]
        dy = dy // precisions[token1_index]

        dy -= self._fee(xp, fee_gamma, mid_fee, out_fee, n_coins) * dy // 10**10

        return dy

    @staticmethod
    def _fee(xp, fee_gamma, mid_fee, out_fee, n_coins):
        f = CurveThreeCryptoSwap._reduction_coefficient(xp, fee_gamma, n_coins)
        return unsafe_div(mid_fee * f + out_fee * (10**18 - f), 10**18, "uint256")

    @staticmethod
    def _calc_D_ramp(
        A, gamma, xp, precisions, price_scale, D, future_A_gamma_time, n_coins
    ):
        if future_A_gamma_time > time.time():
            _xp = xp
            _xp[0] *= precisions[0]
            for k in range(n_coins - 1):
                _xp[k + 1] = (
                    _xp[k + 1] * price_scale[k] * precisions[k + 1] // PRECISION
                )
            D = CurveThreeCryptoSwapNG._newton_D(A, gamma, _xp, 0, n_coins)

        return D

    @staticmethod
    def _get_y(_ANN, _gamma, x, _D, i, n_coins):
        x = copy.deepcopy(x)
        A_MULTIPLIER = 10000

        MIN_GAMMA = 10**10
        MAX_GAMMA = 5 * 10**16

        MIN_A = n_coins**n_coins * A_MULTIPLIER // 100
        MAX_A = n_coins**n_coins * A_MULTIPLIER * 1000
        # Safety checks
        assert _ANN > MIN_A - 1 and _ANN < MAX_A + 1  # dev: unsafe values A
        assert (
            _gamma > MIN_GAMMA - 1 and _gamma < MAX_GAMMA + 1
        )  # dev: unsafe values gamma
        assert _D > 10**17 - 1 and _D < 10**15 * 10**18 + 1  # dev: unsafe values D

        frac = 0
        for k in range(3):
            if k != i:
                frac = x[k] * 10**18 // _D
                assert frac > 10**16 - 1 and frac < 10**20 + 1, "Unsafe values x[i]"
                # if above conditions are met, x[k] > 0

        j = 0
        k = 0
        if i == 0:
            j = 1
            k = 2
        elif i == 1:
            j = 0
            k = 2
        elif i == 2:
            j = 0
            k = 1

        ANN = _ANN
        gamma = _gamma
        D = _D
        x_j = x[j]
        x_k = x[k]
        gamma2 = unsafe_mul(gamma, gamma, "int256")

        a = 10**36 // 27

        # 10**36/9 + 2*10**18*gamma/27 - D**2/x_j*gamma**2*ANN/27**2/convert(A_MULTIPLIER, int256)/x_k
        b = unsafe_add(
            10**36 // 9,
            unsafe_div(unsafe_mul(2 * 10**18, gamma, "int256"), 27, "int256"),
            "int256",
        ) - unsafe_div(
            unsafe_div(
                unsafe_div(
                    unsafe_mul(
                        unsafe_div(unsafe_mul(D, D, "int256"), x_j, "int256"),
                        gamma2,
                        "int256",
                    )
                    * ANN,
                    27**2,
                    "int256",
                ),
                A_MULTIPLIER,
                "int256",
            ),
            x_k,
            "int256",
        )  # <------- The first two expressions can be unsafe, and unsafely added.

        # 10**36/9 + gamma*(gamma + 4*10**18)/27 + gamma**2*(x_j+x_k-D)/D*ANN/27/convert(A_MULTIPLIER, int256)
        c = unsafe_add(
            10**36 // 9,
            unsafe_div(
                unsafe_mul(gamma, unsafe_add(gamma, 4 * 10**18, "int256"), "int256"),
                27,
                "int256",
            ),
            "int256",
        ) + unsafe_div(
            unsafe_div(
                unsafe_mul(
                    unsafe_div(
                        gamma2
                        * unsafe_sub(unsafe_add(x_j, x_k, "int256"), D, "int256"),
                        D,
                        "int256",
                    ),
                    ANN,
                    "int256",
                ),
                27,
                "int256",
            ),
            A_MULTIPLIER,
            "int256",
        )  # <--------- Same as above with the first two expressions. In the third
        #   expression, x_j + x_k will not overflow since we know their range from
        #                                              previous assert statements.

        # (10**18 + gamma)**2/27
        d = unsafe_div(unsafe_add(10**18, gamma, "int256") ** 2, 27, "int256")

        # abs(3*a*c/b - b)
        d0 = abs(unsafe_mul(3, a, "int256") * c // b - b)  # <------------ a is smol.

        divider = 0
        if d0 > 10**48:
            divider = 10**30
        elif d0 > 10**44:
            divider = 10**26
        elif d0 > 10**40:
            divider = 10**22
        elif d0 > 10**36:
            divider = 10**18
        elif d0 > 10**32:
            divider = 10**14
        elif d0 > 10**28:
            divider = 10**10
        elif d0 > 10**24:
            divider = 10**6
        elif d0 > 10**20:
            divider = 10**2
        else:
            divider = 1

        additional_prec = 0
        if abs(a) > abs(b):
            additional_prec = abs(unsafe_div(a, b, "int256"))
            a = unsafe_div(unsafe_mul(a, additional_prec, "int256"), divider, "int256")
            b = unsafe_div(b * additional_prec, divider, "int256")
            c = unsafe_div(c * additional_prec, divider, "int256")
            d = unsafe_div(d * additional_prec, divider, "int256")
        else:
            additional_prec = abs(unsafe_div(b, a, "int256"))
            a = unsafe_div(unsafe_div(a, additional_prec, "int256"), divider, "int256")
            b = unsafe_div(unsafe_div(b, additional_prec, "int256"), divider, "int256")
            c = unsafe_div(unsafe_div(c, additional_prec, "int256"), divider, "int256")
            d = unsafe_div(unsafe_div(d, additional_prec, "int256"), divider, "int256")

        # 3*a*c/b - b
        _3ac = unsafe_mul(3, a, "int256") * c
        delta0 = unsafe_div(_3ac, b, "int256") - b

        # 9*a*c/b - 2*b - 27*a**2/b*d/b
        delta1 = (
            unsafe_div(3 * _3ac, b, "int256")
            - unsafe_mul(2, b, "int256")
            - unsafe_div(unsafe_div(27 * a**2, b, "int256") * d, b, "int256")
        )

        # delta1**2 + 4*delta0**2/b*delta0
        sqrt_arg = delta1**2 + unsafe_div(4 * delta0**2, b, "int256") * delta0

        sqrt_val = 0
        if sqrt_arg > 0:
            sqrt_val = isqrt(sqrt_arg)
        else:
            return [
                CurveThreeCryptoSwapNG._newton_y(_ANN, _gamma, x, _D, i, n_coins),
                0,
            ]

        b_cbrt = 0
        if b >= 0:
            b_cbrt = CurveThreeCryptoSwapNG._cbrt(b)
        else:
            b_cbrt = -CurveThreeCryptoSwapNG._cbrt(-b)

        second_cbrt = 0
        if delta1 > 0:
            # convert(self._cbrt(convert((delta1 + sqrt_val), uint256)/2), int256)
            second_cbrt = CurveThreeCryptoSwapNG._cbrt(
                unsafe_div(delta1 + sqrt_val, 2, "uint256")
            )
        else:
            second_cbrt = -CurveThreeCryptoSwapNG._cbrt(
                unsafe_div(-(delta1 - sqrt_val), 2, "uint256")
            )

        # b_cbrt*b_cbrt/10**18*second_cbrt/10**18
        C1 = unsafe_div(
            unsafe_div(b_cbrt * b_cbrt, 10**18, "int256") * second_cbrt,
            10**18,
            "int256",
        )

        # (b + b*delta0/C1 - C1)/3
        root_K0 = unsafe_div(b + unsafe_div(b * delta0, C1, "int256") - C1, 3, "int256")

        # D*D/27/x_k*D/x_j*root_K0/a
        root = unsafe_div(
            unsafe_div(
                unsafe_div(unsafe_div(D * D, 27, "int256"), x_k, "int256") * D,
                x_j,
                "int256",
            )
            * root_K0,
            a,
            "int256",
        )

        out = [root, unsafe_div(10**18 * root_K0, a, "int256")]

        frac = unsafe_div(out[0] * 10**18, _D, "int256")
        assert frac >= 10**16 - 1 and frac < 10**20 + 1, "Unsafe value for y"
        # due to precision issues, get_y can be off by 2 wei or so wrt _newton_y

        return out

    @staticmethod
    def _geometric_mean(_x):
        prod = unsafe_div(
            unsafe_div(_x[0] * _x[1], 10**18, "uint256") * _x[2], 10**18, "uint256"
        )

        if prod == 0:
            return 0

        return CurveThreeCryptoSwapNG._cbrt(prod)

    @staticmethod
    def _newton_D(ANN, gamma, x_unsorted, K0_prev=0, n_coins=None):
        A_MULTIPLIER = 10000
        x = CurveThreeCryptoSwapNG._sort(x_unsorted)
        max_value_uint256 = 2**256 - 1
        assert (
            x[0] < max_value_uint256 // 10**18 * n_coins**n_coins
        )  # dev: out of limits
        assert x[0] > 0  # dev: empty pool

        # Safe to do unsafe add since we checked largest x's bounds previously
        S = unsafe_add(unsafe_add(x[0], x[1], "uint256"), x[2], "uint256")
        D = 0

        if K0_prev == 0:
            # Geometric mean of 3 numbers cannot be larger than the largest number
            # so the following is safe to do:
            D = unsafe_mul(
                n_coins, CurveThreeCryptoSwapNG._geometric_mean(x), "uint256"
            )
        else:
            if S > 10**36:
                D = CurveThreeCryptoSwapNG._cbrt(
                    unsafe_div(
                        unsafe_div(x[0] * x[1], 10**36, "uint256") * x[2],
                        K0_prev,
                        "uint256",
                    )
                    * 27
                    * 10**12
                )
            elif S > 10**24:
                D = CurveThreeCryptoSwapNG._cbrt(
                    unsafe_div(
                        unsafe_div(x[0] * x[1], 10**24, "uint256") * x[2],
                        K0_prev,
                        "uint256",
                    )
                    * 27
                    * 10**6
                )
            else:
                D = CurveThreeCryptoSwapNG._cbrt(
                    unsafe_div(
                        unsafe_div(x[0] * x[1], 10**18, "uint256") * x[2],
                        K0_prev,
                        "uint256",
                    )
                    * 27
                )

            # D not zero here if K0_prev > 0, and we checked if x[0] is gt 0.

        # initialise variables:
        K0 = 0
        _g1k0 = 0
        mul1 = 0
        mul2 = 0
        neg_fprime = 0
        D_plus = 0
        D_minus = 0
        D_prev = 0

        diff = 0
        frac = 0

        for i in range(255):
            D_prev = D

            # K0 = 10**18 * x[0] * N_COINS / D * x[1] * N_COINS / D * x[2] * N_COINS / D
            K0 = unsafe_div(
                unsafe_mul(
                    unsafe_mul(
                        unsafe_div(
                            unsafe_mul(
                                unsafe_mul(
                                    unsafe_div(
                                        unsafe_mul(
                                            unsafe_mul(10**18, x[0], "uint256"),
                                            n_coins,
                                            "uint256",
                                        ),
                                        D,
                                        "uint256",
                                    ),
                                    x[1],
                                    "uint256",
                                ),
                                n_coins,
                                "uint256",
                            ),
                            D,
                            "uint256",
                        ),
                        x[2],
                        "uint256",
                    ),
                    n_coins,
                    "uint256",
                ),
                D,
                "uint256",
            )  # <-------- We can convert the entire expression using unsafe math.
            #   since x_i is not too far from D, so overflow is not expected. Also
            #      D > 0, since we proved that already. unsafe_div is safe. K0 > 0
            #        since we can safely assume that D < 10**18 * x[0]. K0 is also
            #                            in the range of 10**18 (it's a property).

            _g1k0 = unsafe_add(
                gamma, 10**18, "uint256"
            )  # <--------- safe to do unsafe_add.

            if _g1k0 > K0:  # The following operations can safely be unsafe.
                _g1k0 = unsafe_add(unsafe_sub(_g1k0, K0, "uint256"), 1, "uint256")
            else:
                _g1k0 = unsafe_add(unsafe_sub(K0, _g1k0, "uint256"), 1, "uint256")

            # D / (A * N**N) * _g1k0**2 / gamma**2
            # mul1 = 10**18 * D / gamma * _g1k0 / gamma * _g1k0 * A_MULTIPLIER / ANN
            mul1 = unsafe_div(
                unsafe_mul(
                    unsafe_mul(
                        unsafe_div(
                            unsafe_mul(
                                unsafe_div(
                                    unsafe_mul(10**18, D, "uint256"), gamma, "uint256"
                                ),
                                _g1k0,
                                "uint256",
                            ),
                            gamma,
                            "uint256",
                        ),
                        _g1k0,
                        "uint256",
                    ),
                    A_MULTIPLIER,
                    "uint256",
                ),
                ANN,
                "uint256",
            )  # <------ Since D > 0, gamma is small, _g1k0 is small, the rest are
            #        non-zero and small constants, and D has a cap in this method,
            #                    we can safely convert everything to unsafe maths.

            # 2*N*K0 / _g1k0
            # mul2 = (2 * 10**18) * N_COINS * K0 / _g1k0
            mul2 = unsafe_div(
                unsafe_mul(2 * 10**18 * n_coins, K0, "uint256"), _g1k0, "uint256"
            )  # <--------------- K0 is approximately around D, which has a cap of
            #      10**15 * 10**18 + 1, since we get that in get_y which is called
            #    with newton_D. _g1k0 > 0, so the entire expression can be unsafe.

            # neg_fprime: uint256 = (S + S * mul2 / 10**18) + mul1 * N_COINS / K0 - mul2 * D / 10**18
            neg_fprime = unsafe_sub(
                unsafe_add(
                    unsafe_add(
                        S,
                        unsafe_div(unsafe_mul(S, mul2, "uint256"), 10**18, "uint256"),
                        "uint256",
                    ),
                    unsafe_div(unsafe_mul(mul1, n_coins, "uint256"), K0, "uint256"),
                    "uint256",
                ),
                unsafe_div(unsafe_mul(mul2, D, "uint256"), 10**18, "uint256"),
                "uint256",
            )  # <--- mul1 is a big number but not huge: safe to unsafely multiply
            # with N_coins. neg_fprime > 0 if this expression executes.
            # mul2 is in the range of 10**18, since K0 is in that range, S * mul2
            # is safe. The first three sums can be done using unsafe math safely
            # and since the final expression will be small since mul2 is small, we
            # can safely do the entire expression unsafely.

            # D -= f / fprime
            # D * (neg_fprime + S) / neg_fprime
            D_plus = unsafe_div(
                D * unsafe_add(neg_fprime, S, "uint256"), neg_fprime, "uint256"
            )

            # D*D / neg_fprime
            D_minus = unsafe_div(D * D, neg_fprime, "uint256")

            # Since we know K0 > 0, and neg_fprime > 0, several unsafe operations
            # are possible in the following. Also, (10**18 - K0) is safe to mul.
            # So the only expressions we keep safe are (D_minus + ...) and (D * ...)
            if 10**18 > K0:
                # D_minus += D * (mul1 / neg_fprime) / 10**18 * (10**18 - K0) / K0
                D_minus += unsafe_div(
                    unsafe_mul(
                        unsafe_div(
                            D * unsafe_div(mul1, neg_fprime, "uint256"),
                            10**18,
                            "uint256",
                        ),
                        unsafe_sub(10**18, K0, "uint256"),
                        "uint256",
                    ),
                    K0,
                    "uint256",
                )
            else:
                # D_minus -= D * (mul1 / neg_fprime) / 10**18 * (K0 - 10**18) / K0
                D_minus -= unsafe_div(
                    unsafe_mul(
                        unsafe_div(
                            D * unsafe_div(mul1, neg_fprime, "uint256"),
                            10**18,
                            "uint256",
                        ),
                        unsafe_sub(K0, 10**18, "uint256"),
                        "uint256",
                    ),
                    K0,
                    "uint256",
                )

            if D_plus > D_minus:
                D = unsafe_sub(
                    D_plus, D_minus, "uint256"
                )  # <--------- Safe since we check.
            else:
                D = unsafe_div(unsafe_sub(D_minus, D_plus, "uint256"), 2, "uint256")

            if D > D_prev:
                diff = unsafe_sub(D, D_prev, "uint256")
            else:
                diff = unsafe_sub(D_prev, D, "uint256")

            # Could reduce precision for gas efficiency here:
            if unsafe_mul(diff, 10**14, "uint256") < max(10**16, D):
                # Test that we are safe with the next get_y
                for _x in x:
                    frac = unsafe_div(unsafe_mul(_x, 10**18, "uint256"), D, "uint256")
                    assert (
                        frac >= 10**16 - 1 and frac < 10**20 + 1
                    ), "Unsafe values x[i]"

                return D
        raise "Did not converge"

    @staticmethod
    def _sort(unsorted_x):
        # Sorts a three-array number in a descending order:
        x = copy.deepcopy(unsorted_x)
        temp_var = x[0]
        if x[0] < x[1]:
            x[0] = x[1]
            x[1] = temp_var
        if x[0] < x[2]:
            temp_var = x[0]
            x[0] = x[2]
            x[2] = temp_var
        if x[1] < x[2]:
            temp_var = x[1]
            x[1] = x[2]
            x[2] = temp_var

        return x

    @staticmethod
    def _cbrt(x):
        xx = 0
        if x >= 115792089237316195423570985008687907853269 * 10**18:
            xx = x
        elif x >= 115792089237316195423570985008687907853269:
            xx = unsafe_mul(x, 10**18, "uint256")
        else:
            xx = unsafe_mul(x, 10**36, "uint256")

        log2x = CurveThreeCryptoSwapNG._snekmate_log_2(xx, False)

        # When we divide log2x by 3, the remainder is (log2x % 3).
        # So if we just multiply 2**(log2x/3) and discard the remainder to calculate our
        # guess, the newton method will need more iterations to converge to a solution,
        # since it is missing that precision. It's a few more calculations now to do less
        # calculations later:
        # pow = log2(x) // 3
        # remainder = log2(x) % 3
        # initial_guess = 2 ** pow * cbrt(2) ** remainder
        # substituting -> 2 = 1.26 ≈ 1260 / 1000, we get:
        #
        # initial_guess = 2 ** pow * 1260 ** remainder // 1000 ** remainder

        remainder = log2x % 3
        a = unsafe_div(
            unsafe_mul(
                pow_mod256(2, unsafe_div(log2x, 3, "uint256")),  # <- pow
                pow_mod256(1260, remainder),
                "uint256",
            ),
            pow_mod256(1000, remainder),
            "uint256",
        )

        # Because we chose good initial values for cube roots, 7 newton raphson iterations
        # are just about sufficient. 6 iterations would result in non-convergences, and 8
        # would be one too many iterations. Without initial values, the iteration count
        # can go up to 20 or greater. The iterations are unrolled. This reduces gas costs
        # but takes up more bytecode:
        a = unsafe_div(
            unsafe_add(
                unsafe_mul(2, a, "uint256"),
                unsafe_div(xx, unsafe_mul(a, a, "uint256"), "uint256"),
                "uint256",
            ),
            3,
            "uint256",
        )
        a = unsafe_div(
            unsafe_add(
                unsafe_mul(2, a, "uint256"),
                unsafe_div(xx, unsafe_mul(a, a, "uint256"), "uint256"),
                "uint256",
            ),
            3,
            "uint256",
        )
        a = unsafe_div(
            unsafe_add(
                unsafe_mul(2, a, "uint256"),
                unsafe_div(xx, unsafe_mul(a, a, "uint256"), "uint256"),
                "uint256",
            ),
            3,
            "uint256",
        )
        a = unsafe_div(
            unsafe_add(
                unsafe_mul(2, a, "uint256"),
                unsafe_div(xx, unsafe_mul(a, a, "uint256"), "uint256"),
                "uint256",
            ),
            3,
            "uint256",
        )
        a = unsafe_div(
            unsafe_add(
                unsafe_mul(2, a, "uint256"),
                unsafe_div(xx, unsafe_mul(a, a, "uint256"), "uint256"),
                "uint256",
            ),
            3,
            "uint256",
        )
        a = unsafe_div(
            unsafe_add(
                unsafe_mul(2, a, "uint256"),
                unsafe_div(xx, unsafe_mul(a, a, "uint256"), "uint256"),
                "uint256",
            ),
            3,
            "uint256",
        )
        a = unsafe_div(
            unsafe_add(
                unsafe_mul(2, a, "uint256"),
                unsafe_div(xx, unsafe_mul(a, a, "uint256"), "uint256"),
                "uint256",
            ),
            3,
            "uint256",
        )

        if x >= 115792089237316195423570985008687907853269 * 10**18:
            a = unsafe_mul(a, 10**12, "uint256")
        elif x >= 115792089237316195423570985008687907853269:
            a = unsafe_mul(a, 10**6, "uint256")

        return a

    @staticmethod
    def _snekmate_log_2(x, roundup: bool):
        value = x
        result = 0
        if x >> 128 != 0:
            value = x >> 128
            result = 128
        if value >> 64 != 0:
            value = value >> 64
            result = unsafe_add(result, 64, "uint256")
        if value >> 32 != 0:
            value = value >> 32
            result = unsafe_add(result, 32, "uint256")
        if value >> 16 != 0:
            value = value >> 16
            result = unsafe_add(result, 16, "uint256")
        if value >> 8 != 0:
            value = value >> 8
            result = unsafe_add(result, 8, "uint256")
        if value >> 4 != 0:
            value = value >> 4
            result = unsafe_add(result, 4, "uint256")
        if value >> 2 != 0:
            value = value >> 2
            result = unsafe_add(result, 2, "uint256")
        if value >> 1 != 0:
            result = unsafe_add(result, 1, "uint256")

        if roundup and (1 << result) < x:
            result = unsafe_add(result, 1, "uint256")

        return result
