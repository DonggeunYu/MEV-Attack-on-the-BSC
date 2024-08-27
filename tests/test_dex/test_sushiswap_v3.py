import pytest
from base import DexClassBase
from src.dex.sushiswap_v3 import SushiswapV3
from src.types import PoolInfo


class TestSushiswapV3(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return SushiswapV3(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "SushiswapV3",
                "0x87c7056bbe6084f03304196be51c6b90b6d85aa2",
                (
                    "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2",
                    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                ),
                3000,
            ),
            PoolInfo(
                "SushiswapV3",
                "0xc5e0a6a1fe4b128c342702ca96346f8846493924",
                (
                    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "0x8c223a82e07fecb49d602150d7c2b3a4c9630310",
                ),
                10000,
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
        return [3000, 10000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [8, 8]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (6, 18)]
