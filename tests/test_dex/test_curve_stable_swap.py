import pytest
from web3 import Web3
from src.multicall import Multicall, Call
from base import DexClassBase
from src.dex import (
    CurveStableSwapInterface1,
    CurveStableSwapInterface1Underlying,
    CurveStableSwapInterface2,
    CurveStableSwapInterface2Underlying,
    CurveStableSwapMeta,
    CurveSTableSwapMetaUnderlying,
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


class TestCurveStableSwapInterface1Underlying(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveStableSwapInterface1Underlying(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveStableSwapInterface1Underlying",
                "0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56",
                (
                    "0x6b175474e89094c44da98b954eedeac495271d0f",
                    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                ),
                4000000,
            ),
            PoolInfo(
                "CurveStableSwapInterface1Underlying",
                "0x06364f10B501e868329afBc005b3492902d6C763",
                (
                    "0x6b175474e89094c44da98b954eedeac495271d0f",
                    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "0x8e870d67f660d95d5be530380d0ec0bd388289e1",
                ),
                4000000,
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
        return [4000000, 4000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [5, 3]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 4]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (18, 6)]


class TestCurveStableSwapMeta(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveStableSwapMeta(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveStableSwapMeta",
                "0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1",
                (
                    "0x674C6Ad92Fd080e4004b2312b45f796a192D27a0",
                    "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
                ),
                4000000,
            ),
            PoolInfo(
                "CurveStableSwapMeta",
                "0x4f062658EaAF2C1ccf8C8e36D6824CDf41167956",
                (
                    "0x056Fd409E1d7A124BD7017459dFEa2F387b6d5Cd",
                    "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
                ),
                4000000,
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
        return [4000000, 4000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [9, 9]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 18), (2, 18)]


class TestCurveStableSwapMetaUnderlying(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveSTableSwapMetaUnderlying(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveSTableSwapMetaUnderlying",
                "0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1",
                (
                    "0x674C6Ad92Fd080e4004b2312b45f796a192D27a0",  # COINS
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                4000000,
            ),
            PoolInfo(
                "CurveSTableSwapMetaUnderlying",
                "0x4f062658EaAF2C1ccf8C8e36D6824CDf41167956",
                (
                    "0x056Fd409E1d7A124BD7017459dFEa2F387b6d5Cd",
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                4000000,
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
        return [4000000, 4000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [9, 9]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [4, 4]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 18), (2, 18)]


class TestCurveStableSwapInterface2(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveStableSwapInterface2(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveStableSwapInterface2",
                "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7",
                (
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                1000000,
            )
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
        return [1000000, 4000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [2, 3]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [3, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (2, 18)]


class TestCurveStableSwapInterface2Underlying(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveStableSwapInterface2Underlying(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveStableSwapInterface2Underlying",
                "0xDeBF20617708857ebe4F679508E7b7863a8A8EeE",
                (
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                4000000,
            ),
            PoolInfo(
                "CurveStableSwapInterface2Underlying",
                "0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF",
                (
                    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                6000000,
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
        return [4000000, 6000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [3, 5]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [3, 3]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (18, 6)]


class TestCurveStableSwapInterface1(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveStableSwapInterface1(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveStableSwapInterface1",
                "0xA5407eAE9Ba41422680e2e00537571bcC53efBfD",
                (
                    "0x6b175474e89094c44da98b954eedeac495271d0f",
                    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "0x57Ab1ec28D129707052df4dF418D58a2D46d5f51",
                ),
                2000000,
            ),
            PoolInfo(
                "CurveStableSwapInterface1",
                "0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C",
                (
                    "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
                    "0x39AA39c021dfbaE8faC545936693aC917d5E7563",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                ),
                4000000,
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
        return [2000000, 4000000]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [2, 5]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [4, 3]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 6), (8, 8)]
