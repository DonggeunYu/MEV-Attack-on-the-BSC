import pytest
from base import DexClassBase
from src.dex.uniswap_v3 import UniswapV3
from src.types import PoolInfo


class TestUniswapV3(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return UniswapV3(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "UniswapV3",
                "0x48da0965ab2d2cbf1c17c09cfb5cbe67ad5b1406",
                (
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                100,
            ),
            PoolInfo(
                "UniswapV3",
                "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                (
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                ),
                500,
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
        return [100, 500]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [8, 8]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (6, 18)]
