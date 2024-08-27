import pytest
from base import DexClassBase
from src.dex.uniswap_v2 import UniswapV2
from src.types import PoolInfo


class TestUniswapV2(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return UniswapV2(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "UniswapV2",
                "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852",
                (
                    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "0xdac17f958d2ee523a2206206994597c13d831ec7",
                ),
                3000,
            ),
            PoolInfo(
                "UniswapV2",
                "0xa478c2975ab1ea89e8196811f51a7b7ade33eb11",
                (
                    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
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
    def expect_fee(self):
        return [3000, 3000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (6, 18)]
