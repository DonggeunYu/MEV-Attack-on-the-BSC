import math
from typing import List, Dict, Union
from ..utils import multicall_by_chunk
from web3 import Web3
from ..config import Config
from ..utils import eq_address, error_handling_decorator, get_provider, sort_token, \
    is_in_address_list
from eth_typing import ChecksumAddress
from ..multicall import Call, Multicall
from src.dex import DEX2AMM, ID2DEX
from ..types import Path


def get_decimals_by_token_address(
        http_endpoint, token_addresses: List[str]
) -> Dict[str, Dict[str, Union[str, int]]]:
    symbol_signature = "symbol()(string)"
    decimals_signature = "decimals()(uint8)"
    calls = []
    for address in token_addresses:
        if eq_address(address, "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"):
            continue
        symbol_call = Call(address, symbol_signature, [(address + "_s", lambda x: x)])
        decimals_call = Call(
            address, decimals_signature, [(address + "_d", lambda x: x)]
        )
        calls.extend([symbol_call, decimals_call])

    result = multicall_by_chunk(http_endpoint, calls)
    formatted_result = {
        "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee": {"symbol": "ETH", "decimals": 18}
    }
    for k, v in result.items():
        address = k[:-2]
        if address not in formatted_result:
            formatted_result[address] = {}
        if k.endswith("_s"):
            formatted_result[address]["symbol"] = v
        else:
            formatted_result[address]["decimals"] = v

    return formatted_result


def get_token_price(cfg: Config, token0_address, token1_address):
    w3 = Web3(Web3.HTTPProvider(cfg.http_endpoint))
    if eq_address(token0_address, token1_address):
        return 1

    token0 = Web3.to_checksum_address(token0_address)
    token1 = Web3.to_checksum_address(token1_address)

    not_reverse = True if sort_token(token0, token1)[0] == token0 else False

    uniswap_v2_factory_abi = [
        {
            "constant": True,
            "inputs": [
                {"internalType": "address", "name": "", "type": "address"},
                {"internalType": "address", "name": "", "type": "address"},
            ],
            "name": "getPair",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    ]
    if cfg.factory_config["getPair"]["PANCAKESWAP_V2"]:
        uniswap_v2_factory_contract = w3.eth.contract(
            address=cfg.factory_config["getPair"]["PANCAKESWAP_V2"][0],
            abi=uniswap_v2_factory_abi,
        )
        pool_address = uniswap_v2_factory_contract.functions.getPair(
            token0, token1
        ).call()

        uniswap_v2_pair_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                    {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                    {
                        "internalType": "uint32",
                        "name": "_blockTimestampLast",
                        "type": "uint32",
                    },
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            }
        ]
        if pool_address != "0x0000000000000000000000000000000000000000":
            uniswap_v2_pair_contract = w3.eth.contract(
                address=pool_address, abi=uniswap_v2_pair_abi
            )
            reserves = uniswap_v2_pair_contract.functions.getReserves().call()
            if not_reverse:
                return reserves[1] / reserves[0]
            else:
                return reserves[0] / reserves[1]
    else:
        uniswap_v3_factory_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "", "type": "address"},
                    {"internalType": "address", "name": "", "type": "address"},
                    {"internalType": "uint24", "name": "", "type": "uint24"},
                ],
                "name": "getPool",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function",
            }
        ]
        uniswap_v3_factory_contract = w3.eth.contract(
            address=cfg.factory_config["getPool"]["PANCAKESWAP_V3"][0],
            abi=uniswap_v3_factory_abi,
        )
        pool_address = "0x0000000000000000000000000000000000000000"
        uniswap_v3_fee_tiers = [100, 500, 3000, 10000]
        for fee_tier in uniswap_v3_fee_tiers:
            pool_address = uniswap_v3_factory_contract.functions.getPool(
                token0, token1, fee_tier
            ).call()
            if pool_address != "0x0000000000000000000000000000000000000000":
                break

        if pool_address != "0x0000000000000000000000000000000000000000":
            uniswap_v3_pool_abi = [
                {
                    "inputs": [],
                    "name": "slot0",
                    "outputs": [
                        {
                            "internalType": "uint160",
                            "name": "sqrtPriceX96",
                            "type": "uint160",
                        },
                        {"internalType": "int24", "name": "tick", "type": "int24"},
                        {
                            "internalType": "uint16",
                            "name": "observationIndex",
                            "type": "uint16",
                        },
                        {
                            "internalType": "uint16",
                            "name": "observationCardinality",
                            "type": "uint16",
                        },
                        {
                            "internalType": "uint16",
                            "name": "observationCardinalityNext",
                            "type": "uint16",
                        },
                        {
                            "internalType": "uint8",
                            "name": "feeProtocol",
                            "type": "uint8",
                        },
                        {"internalType": "bool", "name": "unlocked", "type": "bool"},
                    ],
                    "stateMutability": "view",
                    "type": "function",
                },
            ]
            pool_address = Web3.to_checksum_address(pool_address)
            uniswap_v3_pool_contract = w3.eth.contract(
                address=pool_address, abi=uniswap_v3_pool_abi
            )
            slot0 = uniswap_v3_pool_contract.functions.slot0().call()
            sqrtPriceX96 = slot0[0]
            price = (sqrtPriceX96 / (2 ** 96)) ** 2
            if not_reverse:
                return price
            else:
                return 1 / price
    return 0


def get_pool_price(cfg: Config, dex_id, pool_address: str, token0, token1, block_number=None):
    pool_address = Web3.to_checksum_address(pool_address)

    not_reverse = True if sort_token(token0, token1)[0] == token0 else False

    if DEX2AMM[ID2DEX[dex_id]] == "UNISWAP_V2_AMM":
        uniswap_v2_pair_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                    {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                    {
                        "internalType": "uint32",
                        "name": "_blockTimestampLast",
                        "type": "uint32",
                    },
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            }
        ]
        w3 = Web3(Web3.HTTPProvider(cfg.http_endpoint))
        uniswap_v2_pair_contract = w3.eth.contract(
            address=pool_address, abi=uniswap_v2_pair_abi
        )
        reserves = uniswap_v2_pair_contract.functions.getReserves().call(
            block_identifier=block_number)
        if not_reverse:
            return reserves[1] / reserves[0]
        else:
            return reserves[0] / reserves[1]
    elif DEX2AMM[dex_id] == "UNISWAP_V3_AMM":
        uniswap_v3_pool_abi = [
            {
                "inputs": [],
                "name": "slot0",
                "outputs": [
                    {
                        "internalType": "uint160",
                        "name": "sqrtPriceX96",
                        "type": "uint160",
                    },
                    {"internalType": "int24", "name": "tick", "type": "int24"},
                    {
                        "internalType": "uint16",
                        "name": "observationIndex",
                        "type": "uint16",
                    },
                    {
                        "internalType": "uint16",
                        "name": "observationCardinality",
                        "type": "uint16",
                    },
                    {
                        "internalType": "uint16",
                        "name": "observationCardinalityNext",
                        "type": "uint16",
                    },
                    {
                        "internalType": "uint8",
                        "name": "feeProtocol",
                        "type": "uint8",
                    },
                    {"internalType": "bool", "name": "unlocked", "type": "bool"},
                ],
                "stateMutability": "view",
                "type": "function",
            },
        ]
        w3 = Web3(Web3.HTTPProvider(cfg.http_endpoint))
        uniswap_v3_pool_contract = w3.eth.contract(
            address=pool_address, abi=uniswap_v3_pool_abi
        )
        slot0 = uniswap_v3_pool_contract.functions.slot0().call(block_identifier=block_number)
        sqrtPriceX96 = slot0[0]
        price = (sqrtPriceX96 / (2 ** 96)) ** 2
        if not_reverse:
            return price
        else:
            return 1 / price
    else:
        raise ValueError(f"Unknown AMM: {dex_id, DEX2AMM[dex_id], pool_address, token0, token1}")


def get_pool_from_token_pair(cfg: Config, tokens: List[List[str]]):
    w3 = Web3(Web3.HTTPProvider(cfg.http_endpoint))

    calls = []
    for token0, token1 in tokens:
        token0 = Web3.to_checksum_address(token0)
        token1 = Web3.to_checksum_address(token1)

        for type_, factory_address_by_dex in cfg.factory_config.items():
            if type_ == "getPair":
                signature = "getPair(address,address)(address)"
            elif type_ == "getPairWithBool":
                signature = "getPair(address,address,bool)(address)"
            elif type_ == "getPool":
                signature = "getPool(address,address,uint24)(address)"
            elif type_ == "poolByPair":
                signature = "poolByPair(address,address)(address)"
            else:
                raise ValueError(f"Unknown type: {type_}")

            for dex, factory_addresses in factory_address_by_dex.items():
                if isinstance(factory_addresses, str):
                    factory_addresses = [factory_addresses]
                for idx, factory_address in enumerate(factory_addresses):
                    factory_address: ChecksumAddress

                    if type_ == "getPair":
                        name = f"getPair_{token0}_{token1}_{dex}_{idx}"
                        calls.append(
                            Call(
                                factory_address,
                                [signature, token0, token1],
                                [(name, lambda x: x)],
                            )
                        )
                    elif type_ == "getPairWithBool":
                        name = f"getPairWithBool_{token0}_{token1}_{dex}_{idx}"
                        calls.append(
                            Call(
                                factory_address,
                                [signature, token0, token1, False],
                                [(name, lambda x: x)],
                            )
                        )
                    elif type_ == "getPool":
                        uniswap_v3_fee_tiers = [100, 500, 2500, 3000, 10000]
                        for fee_tier in uniswap_v3_fee_tiers:
                            name = f"getPool_{token0}_{token1}_{fee_tier}_{dex}_{idx}"
                            calls.append(
                                Call(
                                    factory_address,
                                    [signature, token0, token1, fee_tier],
                                    [(name, lambda x: x)],
                                )
                            )
                    elif type_ == "poolByPair":
                        name = f"poolByPair_{token0}_{token1}_{dex}_{idx}"
                        calls.append(
                            Call(
                                factory_address,
                                [signature, token0, token1],
                                [(name, lambda x: x)],
                            )
                        )
                    else:
                        raise ValueError(f"Unknown type: {type_}")

    result = Multicall(calls, _w3=w3)()

    results = []
    for k, v in result.items():
        tmp = k.split("_")
        function_name = tmp[0]
        token0 = tmp[1]
        token1 = tmp[2]
        if "getPair" == function_name:
            dex = "_".join(k.split("_")[3:-1])
        elif "getPairWithBool" == function_name:
            dex = "_".join(k.split("_")[3:-1])
        elif "getPool" == function_name:
            dex = "_".join(k.split("_")[4:-1])
        elif "poolByPair" == function_name:
            dex = "_".join(k.split("_")[3:-1])
        else:
            raise ValueError(f"Unknown type: {k}")

        if v != "0x0000000000000000000000000000000000000000":
            pool = {"dex": dex, "address": v, "token0": token0, "token1": token1}
            results.append(pool)
    return results


@error_handling_decorator
def get_addresses_balance_by_token_address(
        http_endpoint, addresses_by_token_address: Dict[str, List[str]], block_number=None
):
    balance_signature = "balanceOf(address)(uint256)"
    calls = []
    for token_address, addresses in addresses_by_token_address.items():
        for address in addresses:
            call = Call(
                token_address, [balance_signature, address],
                [(f"{token_address}_{address}", lambda x: x)]
            )
            calls.append(call)

    result = multicall_by_chunk(http_endpoint, calls, block_number=block_number)

    formatted_result = []
    for k, v in result.items():
        formatted_result.append({
            "token_address": k.split("_")[0],
            "address": k.split("_")[1],
            "balance": v
        })

    return formatted_result


def get_reserve_by_pool_address(
        http_endpoint, pool_addresses: List[str], block_number=None
):
    reserve_signature = "getReserves()((uint112,uint112,uint32))"
    calls = []
    for address in pool_addresses:
        call = Call(
            address, [reserve_signature],
            [(f"{address}", lambda x: x)]
        )
        calls.append(call)

    result = multicall_by_chunk(http_endpoint, calls, block_number=block_number)

    formatted_result = {}
    diff_interface_pool = []
    for k, v in result.items():
        if v is None:
            diff_interface_pool.append(k)
        else:
            formatted_result[k] = (v[0], v[1])

    if diff_interface_pool:
        reserve_signature = "getReserves()((uint256,uint256))"
        calls = []
        for address in pool_addresses:
            call = Call(
                address, [reserve_signature],
                [(f"{address}", lambda x: x)]
            )
            calls.append(call)

        result = multicall_by_chunk(http_endpoint, calls, block_number=block_number)
        for k, v in result.items():
            formatted_result[k] = (v[0], v[1])

    return formatted_result


def get_n_and_s_by_pool_address(
        http_endpoint, pool_addresses: List[str], block_number=None
):
    get_factory_signature = "factory()(address)"

    calls = []
    for address in pool_addresses:
        call = Call(
            address, [get_factory_signature],
            [(f"{address}", lambda x: x)]
        )
        calls.append(call)
    try:
        result = multicall_by_chunk(http_endpoint, calls, block_number=block_number)
    except Exception as e:
        result = {}
        for address in pool_addresses:
            call = Call(
                address, [get_factory_signature],
                [(f"{address}", lambda x: x)]
            )
            try:
                r = multicall_by_chunk(http_endpoint, [call], block_number=block_number)
                result.update(r)
            except Exception as e:
                result[address] = None

    formatted_result = {}
    for k, v in result.items():
        if v is None:
            r = (1000, 3)
        else:
            if eq_address(v, "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6"):  # UniswapV2
                r = (1000, 3)
            elif eq_address(v, "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"):  # SushiSwapV2
                r = (1000, 3)
            elif eq_address(v, "0xBCfCcbde45cE874adCB698cC183deBcF17952812"):  # PancakeSwapV1
                r = (1000, 2)
            elif eq_address(v, "0xca143ce32fe78f1f7019d7d551a6402fc5350c73"):  # PancakeSwapV2
                r = (10000, 25)
            elif eq_address(v, "0x858E3312ed3A876947EA49d572A7C42DE08af7EE"):  # BiswapV2
                signature = "swapFee()(uint32)"
                call = Call(
                    k, [signature],
                    [(f"{k}", lambda x: x)]
                )
                result = multicall_by_chunk(http_endpoint, [call], block_number=block_number)
                r = (1000, result[k])
            elif eq_address(v, "0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6"):  # ApeSwap
                r = (1000, 2)
            elif eq_address(v, "0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8"):  # MDEX
                signature = "getPairFees(address)(uint256)"
                call = Call(
                    "0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8", [signature, k],
                    [(f"{k}", lambda x: x)]
                )
                result = multicall_by_chunk(http_endpoint, [call], block_number=block_number)
                r = (1000, result[k])
            elif eq_address(v, "0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da"):  # BabySwap
                r = (1000, 2)
            elif eq_address(v, "0xd6715A8be3944ec72738F0BFDC739d48C3c29349"):  # NomiSwap
                signature = "swapFee()(uint32)"
                call = Call(
                    k, [signature],
                    [(f"{k}", lambda x: x)]
                )
                result = multicall_by_chunk(http_endpoint, [call], block_number=block_number)
                r = (1000, result[k])
            elif eq_address(v, "0xB42E3FE71b7E0673335b3331B3e1053BD9822570"):  # WaultSwap
                r = (1000, 2)
            elif eq_address(v, "0x97bCD9BB482144291D77ee53bFa99317A82066E8"):
                r = (1000, 3)
            else:
                r = (1000, 3)

        formatted_result[k] = r

    return formatted_result


def get_48club_validators(http_endpoint: str):
    address = "0x5cc05fde1d231a840061c1a2d7e913cedc8eabaf"

    signature = "getPuissants()(address[])"
    call = Call(
        address, [signature],
        [("getPuissants", lambda x: x)]
    )
    multicall = Multicall([call], _w3=get_provider(http_endpoint))
    result = multicall()
    return result["getPuissants"]


def get_maximum_rate_between_pool(cfg: Config, path: Path, block_number):
    base_tokens = [
        cfg.wrapped_native_token_address,
        "0x55d398326f99059ff775485246999027b3197955",  # USDT
        "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",  # USDC
        "0xe9e7cea3dedca5984780bafc599bd69add087d56",  # BUSD
        "0x2170ed0880ac9a755fd29b2688956bd959f933f8"  # ETH
    ]

    candidate_pair = []
    for idx in range(len(path.pool_addresses)):
        token0 = path.token_addresses[idx]
        token1 = path.token_addresses[idx + 1]

        if is_in_address_list(token0, base_tokens) and is_in_address_list(token1, base_tokens):
            continue
        for base_token in base_tokens:
            if eq_address(token0, base_token):
                candidate_pair.extend(
                    [
                        [token1, b] for b in base_tokens if [token1, b] not in candidate_pair
                    ]
                )
                break
            elif eq_address(token1, base_token):
                candidate_pair.extend(
                    [
                        [token0, b] for b in base_tokens if [token0, b] not in candidate_pair
                    ]
                )
                break

    pools = get_pool_from_token_pair(cfg, candidate_pair)
    candidate_balance_pool_by_swap_event = {}
    for pool in pools:
        if pool["token0"] not in candidate_balance_pool_by_swap_event:
            candidate_balance_pool_by_swap_event[pool["token0"]] = []
        candidate_balance_pool_by_swap_event[pool["token0"]].append(pool["address"])
    for idx in range(len(path.pool_addresses)):
        token0 = path.token_addresses[idx]
        token1 = path.token_addresses[idx + 1]
        if is_in_address_list(token0, base_tokens) and not is_in_address_list(token1, base_tokens):
            candidate_balance_pool_by_swap_event[token1].append(path.pool_addresses[idx])
        elif is_in_address_list(token1, base_tokens) and not is_in_address_list(token0, base_tokens):
            candidate_balance_pool_by_swap_event[token0].append(path.pool_addresses[idx])

    balance_pool = get_addresses_balance_by_token_address(cfg.http_endpoint,
                                                          candidate_balance_pool_by_swap_event,
                                                          block_number)
    maximum_rates = []
    for idx in range(len(path.pool_addresses)):
        token0 = path.token_addresses[idx]
        token1 = path.token_addresses[idx + 1]
        maximum_rate = 0.0
        swap_event_pool_balance = 0
        for pool in balance_pool:
            if (is_in_address_list(pool["token_address"], [token0, token1])
                    and eq_address(path.pool_addresses[idx], pool["address"])):
                swap_event_pool_balance = pool["balance"]
                break

        for pool in balance_pool:
            if (is_in_address_list(pool['token_address'], [token0, token1])
                    and not eq_address(pool["address"], path.pool_addresses[idx])):
                try:
                    maximum_rate = max(maximum_rate, pool["balance"] / swap_event_pool_balance)
                except ZeroDivisionError:
                    pass
        maximum_rates.append(maximum_rate)
    return maximum_rates
