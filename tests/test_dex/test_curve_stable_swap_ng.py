import pytest
from web3 import Web3
from src.multicall import Multicall, Call
from base import DexClassBase
from src.dex import (
    CurveStableSwapNGPlain,
    CurveStableSwapNGMeta,
    CurveStableSwapNGMetaUnderlying,
)
from src.types import PoolInfo


def get_dy(address, i, j, dx, http_endpoint) -> int:
    http_provider = Web3(Web3.HTTPProvider(http_endpoint))
    get_dy_signature = "get_dy(int128,int128,uint256)(uint256)"
    call = Call(
        address,
        [get_dy_signature, i, j, dx],
        [(address, lambda x: x)],
    )
    multicall = Multicall([call], _w3=http_provider)
    result = multicall()
    return result[address]


def get_dy_underlying(address, i, j, dx, http_endpoint) -> int:
    http_provider = Web3(Web3.HTTPProvider(http_endpoint))
    get_dy_signature = "get_dy_underlying(int128,int128,uint256)(uint256)"
    call = Call(
        address,
        [get_dy_signature, i, j, dx],
        [(address, lambda x: x)],
    )
    multicall = Multicall([call], _w3=http_provider)
    result = multicall()
    return result[address]


class TestCurveStableSwapNGPlain(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveStableSwapNGPlain(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveStableSwapNGPlain",
                "0xa5588f7cdf560811710a2d82d3c9c99769db1dcb",
                (
                    "0x853d955aCEf822Db058eb8505911ED77F175b99e",
                    "0x6c3ea9036406852006290770BEdFcAbA0e23A0e8",
                ),
                1000000,
            ),
            PoolInfo(
                "CurveStableSwapNGPlain",
                "0xce6431d21e3fb1036ce9973a3312368ed96f5ce7",
                (
                    "0x853d955aCEf822Db058eb8505911ED77F175b99e",
                    "0x83F20F44975D03b1b09e64809B757c47f942BEeA",
                ),
                1000000,
            ),
        ]

        # Set reserve info
        result = dex_instance.fetch_pools_reserve_info(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        for pool_info in list_of_pool_info:
            pool_info.set_reserve_info(result[pool_info.address])

        # Call for Rates
        dex_instance.fetch_pools_token_addresses(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        return list_of_pool_info

    def test_calculate_amount_out(
        self, list_of_pool_info, dex_instance, token_decimals, http_endpoint
    ):
        for pool_info, _token_decimals in zip(list_of_pool_info, token_decimals):
            x = 10 ** _token_decimals[0]
            result = dex_instance.calculate_amount_out(
                pool_info, x, pool_info.token_addresses[0], pool_info.token_addresses[1]
            )
            assert result == get_dy(pool_info.address, 0, 1, x, http_endpoint)

    @pytest.fixture(scope="class")
    def expect_fee(self):
        return [1000000, 1000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [5, 5]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (18, 6)]


class TestCurveStableSwapNGMeta(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveStableSwapNGMeta(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveStableSwapNGMeta",
                "0x00e6fd108c4640d21b40d02f18dd6fe7c7f725ca",
                (
                    "0x0E573Ce2736Dd9637A0b21058352e1667925C7a8",
                    "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
                ),
                1000000,
            ),
            PoolInfo(
                "CurveStableSwapNGMeta",
                "0xc83b79c07ece44b8b99ffa0e235c00add9124f9e",
                (
                    "0x59D9356E565Ab3A36dD77763Fc0d87fEaf85508C",
                    "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
                ),
                1000000,
            ),
        ]

        # Set reserve info
        result = dex_instance.fetch_pools_reserve_info(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        for pool_info in list_of_pool_info:
            pool_info.set_reserve_info(result[pool_info.address])

        # Call for Rates
        dex_instance.fetch_pools_token_addresses(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        return list_of_pool_info

    def test_calculate_amount_out(
        self, list_of_pool_info, dex_instance, token_decimals, http_endpoint
    ):
        for pool_info, _token_decimals in zip(list_of_pool_info, token_decimals):
            x = 10 ** _token_decimals[0]
            result = dex_instance.calculate_amount_out(
                pool_info, x, pool_info.token_addresses[0], pool_info.token_addresses[1]
            )
            assert result == get_dy(pool_info.address, 0, 1, x, http_endpoint)

    @pytest.fixture(scope="class")
    def expect_fee(self):
        return [1000000, 1000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [9, 9]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(6, 8), (18, 8)]


class TestCurveStableSwapNGMetaUnderlying(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveStableSwapNGMetaUnderlying(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveStableSwapNGMetaUnderlying",
                "0x00e6fd108c4640d21b40d02f18dd6fe7c7f725ca",
                (
                    "0x0E573Ce2736Dd9637A0b21058352e1667925C7a8",
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                1000000,
            ),
            PoolInfo(
                "CurveStableSwapNGMetaUnderlying",
                "0xc83b79c07ece44b8b99ffa0e235c00add9124f9e",
                (
                    "0x59D9356E565Ab3A36dD77763Fc0d87fEaf85508C",
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                1000000,
            ),
        ]

        # Set reserve info
        result = dex_instance.fetch_pools_reserve_info(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        for pool_info in list_of_pool_info:
            pool_info.set_reserve_info(result[pool_info.address])

        # Call for Rates
        dex_instance.fetch_pools_token_addresses(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        return list_of_pool_info

    def test_calculate_amount_out(
        self, list_of_pool_info, dex_instance, token_decimals, http_endpoint
    ):
        for pool_info, _token_decimals in zip(list_of_pool_info, token_decimals):
            x = 10 ** _token_decimals[0]
            result = dex_instance.calculate_amount_out(
                pool_info, x, pool_info.token_addresses[0], pool_info.token_addresses[1]
            )
            assert result == get_dy_underlying(
                pool_info.address, 0, 1, x, http_endpoint
            )

    @pytest.fixture(scope="class")
    def expect_fee(self):
        return [1000000, 1000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [9, 9]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [4, 4]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(6, 18), (18, 18)]
