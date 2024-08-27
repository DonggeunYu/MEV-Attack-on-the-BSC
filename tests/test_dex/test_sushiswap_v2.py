import pytest
from base import DexClassBase
from src.dex.sushiswap_v2 import SushiswapV2
from src.types import PoolInfo


class TestSushiswapV2(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return SushiswapV2(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "SushiswapV2",
                "0x06da0fd433c1a5d7a4faa01111c044910a184553",
                (
                    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "0xdac17f958d2ee523a2206206994597c13d831ec7",
                ),
                3000,
            ),
            PoolInfo(
                "SushiswapV2",
                "0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f",
                (
                    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "0x6b175474e89094c44da98b954eedeac495271d0f",
                ),
                3000,
            ),
        ]
        # Set reserve info
        result = dex_instance.fetch_pools_reserve_info(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        for pool_info in list_of_pool_info:
            pool_info.set_reserve_info(result[pool_info.address])
        return list_of_pool_info

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def expect_fee(self):
        return [3000, 3000]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (6, 18)]
