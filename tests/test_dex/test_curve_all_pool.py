from web3 import Web3
from src.multicall import Multicall, Call
from config.ethereum_config import DEX_TO_ADDRESS_AND_POOL
from src.dex.curve_pool_info import INFORMATION_FOR_POOL
from src.dex import *  # noqa
from src.types import PoolInfo
from itertools import permutations
from src.apis.contract import get_decimals_by_token_address


def get_xx(address, indices, list_of_dx, get_dy_signature, http_endpoint):
    http_provider = Web3(Web3.HTTPProvider(http_endpoint))
    calls = []
    for (i, j), dx in zip(indices, list_of_dx):
        call = Call(
            address,
            [get_dy_signature, i, j, dx],
            [(f"{i}_{j}", lambda x: x)],
        )
        calls.append(call)

    multicall = Multicall(calls, _w3=http_provider)
    result = multicall()

    formmated_result = {}
    for k, v in result.items():
        i, j = k.split("_")
        i = int(i)
        j = int(j)
        formmated_result[(i, j)] = v

    return formmated_result


def get_dy_int128(address, indices, list_of_dx, http_endpoint):
    get_dy_signature = "get_dy(int128,int128,uint256)(uint256)"
    return get_xx(address, indices, list_of_dx, get_dy_signature, http_endpoint)


def get_dy_underlying_int128(address, indices, list_of_dx, http_endpoint):
    get_dy_signature = "get_dy_underlying(int128,int128,uint256)(uint256)"
    return get_xx(address, indices, list_of_dx, get_dy_signature, http_endpoint)


def get_dy_uint256(address, indices, list_of_dx, http_endpoint):
    get_dy_signature = "get_dy(uint256,uint256,uint256)(uint256)"
    return get_xx(address, indices, list_of_dx, get_dy_signature, http_endpoint)


def get_dy_underlying_uint256(address, indices, list_of_dx, http_endpoint):
    get_dy_signature = "get_dy_underlying(uint256,uint256,uint256)(uint256)"
    return get_xx(address, indices, list_of_dx, get_dy_signature, http_endpoint)


def _test_calculate_amount_out(class_name, get_dy_function, http_endpoint):
    pool_address = DEX_TO_ADDRESS_AND_POOL[class_name]["pool_address"]
    for address in pool_address:
        assert (
            address.lower() in INFORMATION_FOR_POOL
        ), f"{address} is not in INFORMATION_FOR_POOL"

    dex = eval(class_name)(http_endpoint)

    for address in pool_address:
        token_address = dex.fetch_pools_token_addresses([address])[address]
        fee = dex.fetch_pools_fee([address])[address]
        reserve_info = dex.fetch_pools_reserve_info([address])[address]
        pool_info = PoolInfo(class_name, address, token_address, fee)
        pool_info.set_reserve_info(reserve_info)

        token_decimals = get_decimals_by_token_address(
            http_endpoint, pool_info.token_addresses
        )

        token_address_permutations = list(permutations(range(len(token_address)), 2))

        indicies = []
        list_of_dx = []
        for i, j in token_address_permutations:
            indicies.append((i, j))

            i_index_token = token_address[i]
            amount_in = 10 ** token_decimals[i_index_token]["decimals"]
            list_of_dx.append(amount_in)

        expected_value = get_dy_function(address, indicies, list_of_dx, http_endpoint)

        for i, j in token_address_permutations:
            i_index_token = token_address[i]
            j_index_token = token_address[j]

            input_token_decimals = token_decimals[i_index_token]["decimals"]
            amount_in = 10**input_token_decimals

            result = dex.calculate_amount_out(
                pool_info, amount_in, i_index_token, j_index_token
            )
            assert (
                result == expected_value[(i, j)]
            ), f"Address: {address}, Expected: {expected_value[(i, j)]}, Got: {result}"


def test_curve_stable_swap_interface1(http_endpoint):
    _test_calculate_amount_out(
        "CurveStableSwapInterface1", get_dy_int128, http_endpoint
    )


def test_curve_stable_swap_interface1_underlying(http_endpoint):
    _test_calculate_amount_out(
        "CurveStableSwapInterface1Underlying", get_dy_underlying_int128, http_endpoint
    )


def test_curve_stable_swap_interface2(http_endpoint):
    _test_calculate_amount_out(
        "CurveStableSwapInterface2", get_dy_int128, http_endpoint
    )


def test_curve_stable_swap_interface2_underlying(http_endpoint):
    _test_calculate_amount_out(
        "CurveStableSwapInterface2Underlying", get_dy_underlying_int128, http_endpoint
    )


def test_curve_stable_swap_meta(http_endpoint):
    _test_calculate_amount_out("CurveStableSwapMeta", get_dy_int128, http_endpoint)


def test_curve_stable_swap_meta_underlying(http_endpoint):
    _test_calculate_amount_out(
        "CurveSTableSwapMetaUnderlying", get_dy_underlying_int128, http_endpoint
    )


def test_calculate_amount_out_curve_stable_swap_ng_plain(http_endpoint):
    _test_calculate_amount_out("CurveStableSwapNGPlain", get_dy_int128, http_endpoint)


def test_calculate_amount_out_curve_stable_swap_ng_meta(http_endpoint):
    _test_calculate_amount_out("CurveStableSwapNGMeta", get_dy_int128, http_endpoint)


def test_calculate_amount_out_curve_stable_swap_ng_meta_underlying(http_endpoint):
    _test_calculate_amount_out(
        "CurveStableSwapNGMetaUnderlying", get_dy_underlying_int128, http_endpoint
    )


def test_calculate_amount_out_curve_crypto_swap(http_endpoint):
    _test_calculate_amount_out("CurveCryptoSwap", get_dy_uint256, http_endpoint)


def test_calculate_amount_out_curve_three_crypto_swap(http_endpoint):
    _test_calculate_amount_out("CurveThreeCryptoSwap", get_dy_uint256, http_endpoint)


def test_calculate_amount_out_curve_three_crypto_swap_ng(http_endpoint):
    _test_calculate_amount_out("CurveThreeCryptoSwapNG", get_dy_uint256, http_endpoint)
