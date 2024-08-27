import pytest
import time
from src.multicall import Call
from src.utils import memoize, multicall_by_chunk
from src.types import PoolInfo


@pytest.mark.parametrize("execution_number", range(10))
def test_memoize(execution_number):
    @memoize(maxsize=1)
    def add(self, pool_info, a, b):
        time.sleep(1e-3)
        return a + b

    mock_pool_info = PoolInfo(dex_name="uniswap_v2", address="0x")

    # Test cache
    now = time.time()
    assert add(None, mock_pool_info, 1, 2) == 3
    first_call_time = time.time() - now

    now = time.time()
    assert add(None, mock_pool_info, 1, 2) == 3
    second_call_time = time.time() - now

    assert second_call_time < first_call_time

    # Test maxsize
    now = time.time()
    assert add(None, mock_pool_info, 1, 3) == 4
    third_call_time = time.time() - now

    assert third_call_time > second_call_time


def test_multicall_by_chunk(http_endpoint):
    uniswap_v2_pool_addresses = [
        "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852",
        "0x7f095edd7745fa3c471736dae4874211dea9ed35",
    ]
    signature = "getReserves()((uint112,uint112,uint32))"

    calls = []
    for address in uniswap_v2_pool_addresses:
        call = Call(address, signature, [(address, lambda x: x)])
        calls.append(call)

    result = multicall_by_chunk(http_endpoint, calls, 1)
    assert len(result) == 2
