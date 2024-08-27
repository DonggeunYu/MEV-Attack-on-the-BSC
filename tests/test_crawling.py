import pytest
from src.crawling import get_pool_list_from_coinmarketcap


@pytest.mark.parametrize(
    "swap, min_txns24h",
    [("uniswap-v3-ethereum", 100), ("curve-ethereum", 0)],
)
def test_get_pool_list_from_coinmarketcap(swap, min_txns24h):
    pool_list = get_pool_list_from_coinmarketcap(swap, min_txns24h)
    assert len(pool_list) > 0
    for pool in pool_list:
        assert len(pool) > 0, f"pool: {pool}"
        assert pool.startswith("0x"), f"pool: {pool}"
        assert len(pool) == 42, f"pool: {pool}"
