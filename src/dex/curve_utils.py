import copy
from .curve_pool_info import INFORMATION_FOR_POOL

PRECISION = 10**18
FEE_DENOMINATOR = 10**10


def calc_withdraw_one_coin(
    _token_amount, i, reserve_info, base_pool_address, base_pool_n_coins
):
    _precision_mul = copy.deepcopy(
        INFORMATION_FOR_POOL[base_pool_address]["PRECISION_MUL"]
    )
    amp = reserve_info["base_pool_A"]
    _fee = (
        reserve_info["base_pool_fee"]
        * base_pool_n_coins
        // (4 * (base_pool_n_coins - 1))
    )
    total_supply = reserve_info["base_pool_lp_total_supply"]

    xp = copy.deepcopy(INFORMATION_FOR_POOL[base_pool_address]["PRECISION_MUL"])
    xp = [x * PRECISION for x in xp]
    for _i in range(base_pool_n_coins):
        xp[_i] = xp[_i] * reserve_info["base_pool_balances"][_i] // PRECISION

    D0 = get_D(xp, amp, None, base_pool_n_coins)

    D1 = D0 - _token_amount * D0 // total_supply
    xp_reduced = xp.copy()

    new_y = get_y_D(amp, i, xp, D1, base_pool_n_coins)
    dy_0 = (xp[i] - new_y) // _precision_mul[i]

    for j in range(base_pool_n_coins):
        if j == i:
            dx_expected = xp[j] * D1 // D0 - new_y
        else:
            dx_expected = xp[j] - xp[j] * D1 // D0
        xp_reduced[j] -= _fee * dx_expected // FEE_DENOMINATOR

    dy = xp_reduced[i] - get_y_D(amp, i, xp_reduced, D1, base_pool_n_coins)
    dy = (dy - 1) // _precision_mul[i]

    return dy, dy_0 - dy


def get_y_D(A_, i, xp, D, base_pool_n_coins):
    assert i >= 0
    assert i < base_pool_n_coins
    c = D
    S_ = 0
    Ann = A_ * base_pool_n_coins

    _x = 0
    for _i in range(base_pool_n_coins):
        if _i != i:
            _x = xp[_i]
        else:
            continue
        S_ += _x
        c = c * D // (_x * base_pool_n_coins)
    c = c * D // (Ann * base_pool_n_coins)
    b = S_ + D // Ann
    y_prev = 0
    y = D
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


def get_D(xp, amp, a_precision=None, n_coins=None, plus_one=False) -> int:
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
            D_P = D_P * D // (_x * n_coins + (1 if plus_one else 0))
        Dprev = D
        if a_precision:
            D = (
                (Ann * S // a_precision + D_P * n_coins)
                * D
                // ((Ann - a_precision) * D // a_precision + (n_coins + 1) * D_P)
            )
        else:
            D = (Ann * S + D_P * n_coins) * D // ((Ann - 1) * D + (n_coins + 1) * D_P)
        if D > Dprev:
            if D - Dprev <= 1:
                break
        else:
            if Dprev - D <= 1:
                break

    return D


def get_y(A, i, j, x, xp_, a_precision=None, n_coins=None, plus_one=False):
    xp_ = copy.deepcopy(xp_)
    n_coins = n_coins if n_coins else len(xp_)
    assert i >= 0
    assert i < n_coins

    amp = A
    D = get_D(xp_, amp, a_precision, n_coins, plus_one)
    c = D
    S_ = 0
    Ann = amp * n_coins

    _x = 0
    for _i in range(n_coins):
        if _i == i:
            _x = x
        elif _i != j:
            _x = xp_[_i]
        else:
            continue
        S_ += _x
        c = c * D // (_x * n_coins)
    if a_precision:
        c = c * D * a_precision // (Ann * n_coins)
        b = S_ + D * a_precision // Ann
    else:
        c = c * D // (Ann * n_coins)
        b = S_ + D // Ann  # - D
    y_prev = 0
    y = D
    for _i in range(255):
        y_prev = y
        y = (y * y + c) // (2 * y + b - D)
        # Equality with the precision of 1
        if y > y_prev:
            if y - y_prev <= 1:
                break
        else:
            if y_prev - y <= 1:
                break
    return y
