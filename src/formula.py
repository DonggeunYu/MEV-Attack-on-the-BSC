import math
from typing import List, Tuple


def get_uniswa_v2_amount_out(amount_in, reserve_in, reserve_out):
    """
    amount_in: int
    reserve_in: int
    reserve_out: int

    """
    return _get_optimal_amount_out(amount_in, 1000, 3, reserve_in, reserve_out)

def _get_optimal_amount_out(amount_in, n, s, reserve_in, reserve_out):
    try:
        return reserve_out - ((reserve_in * reserve_out * n) // (n *(reserve_in + amount_in) - s * amount_in))
    except ZeroDivisionError:
        return 0

def get_multi_hop_amount_out(amount_in, data):
    for N, S, reserve_in, reserve_out in data:
        amount_in = _get_optimal_amount_out(amount_in, N, S, reserve_in, reserve_out)
    return amount_in

def get_multi_hop_optimal_amount_in(data: List[Tuple[int, int, int, int]]):
    """
    Get optimal amount in for multi-hop swap.

    - $h$ = hops
    - $k = (n - s)n^h \prod_{i=2}^{h} R_{i, in} + \sum_{j=2}^{h} [ (n - s)^{j}n^{h-j} \prod_{i=1}^{j - 1} R_{i, out} \prod_{i=1}^{h-j} R_{i + j, in} ]$
    - $a = k^2$
    - $b = 2n^{h} \prod_{i=1}^{h} R_{i, in} k$
    - $c = (n^{h} \prod_{i=1}^{h} R_{i, in})^2 - (n - s)^{h}n^{h} \prod_{i=1}^{h} R_{i, in} \prod_{i=1}^{h} R_{i, out}$
    - $x^* = \frac {-b + \sqrt {b^2 - 4ac}} {2a}$

    Args:
        data: list of tuple of (N, S, reserve_in, reserve_out)

    Returns:
        int: optimal amount in
    """
    h = len(data)
    n = 0
    s = 0
    prod_reserve_in_from_second = 1
    prod_reserve_in_all = 1
    prod_reserve_out_all = 1
    for idx, (N, S, reserve_in, reserve_out) in enumerate(data):
        if S > s:
          n = N
          s = S

        if idx > 0:
          prod_reserve_in_from_second *= reserve_in

        prod_reserve_in_all *= reserve_in
        prod_reserve_out_all *= reserve_out

    sum_k_value = 0
    for j in range(1, h):
      prod_reserve_out_without_latest = prod([r[3] for r in data[:-1]])
      prod_reserve_in_ = 1
      for i in range(0, h-j - 1):
        prod_reserve_in_ *= data[i + j + 1][2]
      sum_k_value += (n - s) ** (j + 1) * n ** (h - j - 1) * prod_reserve_out_without_latest * prod_reserve_in_
    k = (n - s) * n ** (h - 1) * prod_reserve_in_from_second + sum_k_value

    a = k ** 2
    b = 2 * n ** h * prod_reserve_in_all * k
    c = (n ** h * prod_reserve_in_all ) ** 2 - (n - s) ** h * n ** h * prod_reserve_in_all * prod_reserve_out_all

    numerator = -b + math.sqrt(b ** 2 - 4 * a * c)
    denominator = 2 * a
    return math.floor(numerator / denominator)
