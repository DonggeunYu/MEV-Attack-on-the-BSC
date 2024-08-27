import os
from collections import OrderedDict
from web3 import Web3
from .multicall import Multicall, Call
from typing import Any, Dict, List, Tuple
from .types import DexInfo, DexInfos
from .crawling import get_pool_list_from_coinmarketcap
from web3.middleware import geth_poa_middleware
import sys
import traceback
import functools
from loguru import logger


def debug_mode():
    return os.environ.get("DEBUG", False)


def memoize(maxsize=None):
    cache = OrderedDict()

    def decorator(func):
        def memoized_func(*args):
            pool_addresss = args[1].address
            hashable_args = tuple([pool_addresss] + list(args[2:]))

            if hashable_args in cache:
                value = cache[hashable_args]
                cache[hashable_args] = value
            else:
                value = func(*args)
                if maxsize is not None and len(cache) >= maxsize:
                    cache.popitem(last=False)  # 오래된 항목 삭제
                cache[hashable_args] = value
            return value

        return memoized_func

    return decorator


def load_config_file(
    chain: str,
) -> Tuple[Dict[str, str], List[str], Dict[str, Tuple[str, bool]], DexInfos]:
    """
    Load python config file

    Args:
        chain (str): Chain name

    Returns:
        Tuple[Dict[str, str], AllToken, List[str], AllDex]: RPC endpoint, token info, flash loan token list, dex info
    """
    if chain == "ethereum":
        from config.ethereum_config import (
            RPC_ENDPOINT,
            FLASH_LOAN_TOKEN_ADDRESS_LIST,
            POOL_ADDRESS_FOR_TOKEN_PRICE,
            DEX_TO_ADDRESS_AND_POOL,
        )
    elif chain == "test":
        from config.test_config import (
            RPC_ENDPOINT,
            FLASH_LOAN_TOKEN_ADDRESS_LIST,
            POOL_ADDRESS_FOR_TOKEN_PRICE,
            DEX_TO_ADDRESS_AND_POOL,
        )
    else:
        raise ValueError(f"Chain {chain} not supported")

    list_of_dex_info = []
    for dex_name, value in DEX_TO_ADDRESS_AND_POOL.items():
        if isinstance(value["pool_address"], tuple):
            value["pool_address"] = get_pool_list_from_coinmarketcap(
                *value["pool_address"]
            )

        dex_info = DexInfo(dex_name, value["address"], value["pool_address"])
        list_of_dex_info.append(dex_info)
    dex_infos: DexInfos = DexInfos(list_of_dex_info)
    return (
        RPC_ENDPOINT,
        FLASH_LOAN_TOKEN_ADDRESS_LIST,
        POOL_ADDRESS_FOR_TOKEN_PRICE,
        dex_infos,
    )


def multicall_by_chunk(
    http_endpoint: str, calls: List[Call], chunk_size: int = 100,
        block_number: int = None
) -> Dict[str, Any]:
    http_provider = Web3(Web3.HTTPProvider(http_endpoint))
    result = {}
    for chunk in range(0, len(calls), chunk_size):
        multicall = Multicall(calls[chunk : chunk + chunk_size], _w3=http_provider, block_id=block_number)
        result.update(multicall())
    return result


def calculate_next_block_base_fee(gas_used, gas_limit, base_fee_per_gas):
    target_gas_used = gas_limit // 2
    target_gas_used = max(target_gas_used, 1)

    if gas_used > target_gas_used:
        new_base_fee = (
            base_fee_per_gas
            + (base_fee_per_gas * ((gas_used - target_gas_used) // target_gas_used))
            // 8
        )
    else:
        new_base_fee = (
            base_fee_per_gas
            - (base_fee_per_gas * ((target_gas_used - gas_used) // target_gas_used))
            // 8
        )
    return new_base_fee


def eq_address(a, b):
    return a.lower() == b.lower()

def is_in_address_list(address: str, address_list: List[str]) -> bool:
    for addr in address_list:
        if eq_address(address, addr):
            return True
    return False

def find_value_by_address_key(address: str, address_key_dict: Dict[str, Any]) -> Any:
    for key, value in address_key_dict.items():
        if eq_address(address, key):
            return value
    return None

def sort_reserve(token0: str, token1: str, reserve0, reserve1) -> Tuple[int, int]:
    token0 = Web3.to_checksum_address(token0)
    token1 = Web3.to_checksum_address(token1)
    if int(token0, 16) < int(token1, 16):
        return (reserve0, reserve1)
    else:
        return (reserve1, reserve0)

def sort_token(token0: str, token1: str) -> Tuple[str, str]:
    token0 = Web3.to_checksum_address(token0)
    token1 = Web3.to_checksum_address(token1)
    if int(token0, 16) < int(token1, 16):
        return (token0, token1)
    else:
        return (token1, token0)

def get_provider(ws_endpoint):
    w3 = Web3(Web3.HTTPProvider(ws_endpoint, request_kwargs={"timeout": 60}))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def error_handling_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(exc_type)
            logger.error(fname)
            logger.error(exc_tb.tb_lineno)
            logger.error(e)
            logger.error(traceback.format_exc())
    return wrapper