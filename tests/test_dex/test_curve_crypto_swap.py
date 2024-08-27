import pytest
from web3 import Web3
from src.multicall import Multicall, Call
from base import DexClassBase
from src.dex import CurveCryptoSwap, CurveThreeCryptoSwap, CurveThreeCryptoSwapNG
from src.dex.curve_three_crypto_swap_ng import (
    unsafe_add,
    unsafe_sub,
    unsafe_mul,
    unsafe_div,
    isqrt,
    pow_mod256,
)
from src.types import PoolInfo


def test_unsafe_calculate_function():
    # Add
    assert unsafe_add(1, 1, "uint8") == 2
    assert unsafe_add(255, 255, "uint8") == 254
    assert unsafe_add(127, 127, "int8") == -2
    # Subtract
    assert unsafe_sub(4, 3, "uint8") == 1
    assert unsafe_sub(0, 1, "uint8") == 255
    assert unsafe_sub(-128, 1, "int8") == 127
    # Multiply
    assert unsafe_mul(1, 1, "uint8") == 1
    assert unsafe_mul(255, 255, "uint8") == 1
    assert unsafe_mul(-128, -128, "int8") == 0
    assert unsafe_mul(-127, 128, "int8") == -128
    # Divide
    assert unsafe_div(1, 1, "uint8") == 1
    assert unsafe_div(1, 0, "uint8") == 0
    assert unsafe_div(-128, -1, "int8") == -128

    # isqrt
    assert isqrt(101) == 10

    # pow_mod256
    assert pow_mod256(2, 3) == 8
    assert (
        pow_mod256(100, 100)
        == 59041770658110225754900818312084884949620587934026984283048776718299468660736
    )


def get_dy(address, i, j, dx, http_endpoint) -> int:
    http_provider = Web3(Web3.HTTPProvider(http_endpoint))
    get_dy_signature = "get_dy(uint256,uint256,uint256)(uint256)"
    call = Call(
        address,
        [get_dy_signature, i, j, dx],
        [(address, lambda x: x)],
    )
    multicall = Multicall([call], _w3=http_provider)
    result = multicall()
    return result[address]


class TestCurveCryptoSwap(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveCryptoSwap(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveCryptoSwap",
                "0x9409280dc1e6d33ab7a8c6ec03e5763fb61772b5",
                (
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32",
                ),
                0,
            ),
            PoolInfo(
                "CurveCryptoSwap",
                "0xb576491f1e6e5e62f1d8f26062ee822b40b0e0d4",
                (
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b",
                ),
                0,
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
        return [0, 0]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [9, 9]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [2, 2]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(18, 18), (18, 18)]


class TestCurveThreeCryptoSwap(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveThreeCryptoSwap(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveThreeCryptoSwap",
                "0xd51a44d3fae010294c616388b506acda1bfaae46",
                (
                    "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                ),
                0,
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
        return [0]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [8]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [3]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(6, 8)]


class TestCurveThreeCryptoSwapNG(DexClassBase):
    @pytest.fixture(scope="class")
    def dex_instance(self, http_endpoint):
        return CurveThreeCryptoSwapNG(http_endpoint)

    @pytest.fixture(scope="class")
    def list_of_pool_info(self, dex_instance):
        list_of_pool_info = [
            PoolInfo(
                "CurveThreeCryptoSwapNG",
                "0x7f86bf177dd4f3494b841a37e810a34dd56c829b",
                (
                    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                ),
                0,
            ),
            PoolInfo(
                "CurveThreeCryptoSwapNG",
                "0x2570f1bd5d2735314fc102eb12fc1afe9e6e7193",
                (
                    "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
                    "0xae78736Cd615f374D3085123A210448E74Fc6393",
                    "0xac3E018457B222d93114458476f3E3416Abbe38F",
                ),
                0,
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
        return [0, 0]

    @pytest.fixture(scope="class")
    def expect_reserve_count(self):
        return [10, 10]

    @pytest.fixture(scope="class")
    def expect_token_address_count(self):
        return [3, 3]

    @pytest.fixture(scope="class")
    def token_decimals(self):
        return [(6, 8), (18, 18)]
