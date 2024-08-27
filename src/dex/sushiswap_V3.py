from typing import Any, Dict, List, Tuple
from .uniswap_v3 import UniswapV3
from ..multicall import Call
from ..utils import multicall_by_chunk


class SushiSwapV3(UniswapV3):
    def __init__(self, http_endpoint: str, word_cache_size=8):
        super().__init__(http_endpoint, word_cache_size)

    def fetch_pools_reserve_info(
        self, pool_addresses: List[str], block_number=None
    ) -> Dict[str, Tuple[Any]]:
        """
        Fetch reserve info from uniswap v3

        Args:
            pool_addresses:

        Returns:
            Dict[str, List[Any]]: {pool_address: [sqrt_price_x96, tick, observation_index, observation_cardinality,
                observation_cardinality_next, fee_protocol, unlocked]}

        """
        signature_slot0 = "slot0()((uint160,int24,uint16,uint16,uint16,uint32,bool))"
        signature_liquidity = "liquidity()(uint128)"
        calls = []
        for address in pool_addresses:
            call = Call(
                address, signature_slot0, [(address + "_s", lambda x: x)], block_number
            )
            calls.append(call)
            call = Call(
                address,
                signature_liquidity,
                [(address + "_l", lambda x: x)],
                block_number,
            )
            calls.append(call)
        result = multicall_by_chunk(self.http_endpoint, calls)

        formmatted_result = {}
        for k, v in result.items():
            address = k[:-2]
            type = k[-1]
            if address not in formmatted_result:
                formmatted_result[address] = []
            if type == "s":
                v = list(v)
                formmatted_result[address].extend(v)
            else:
                formmatted_result[address].append(v)

        for k, v in formmatted_result.items():
            formmatted_result[k] = tuple(v)

        return formmatted_result
