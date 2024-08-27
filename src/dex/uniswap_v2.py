import math
from typing import Dict, List, Tuple
from ..multicall import Call
from ..utils import multicall_by_chunk
from .dex import DexBase
from ..types import PoolInfo
from ..utils import memoize


class UniswapV2(DexBase):
    def __init__(self, http_endpoint: str):
        super().__init__(http_endpoint)

    def fetch_pools_reserve_info(self, pool_addresses: List[str], block_number=None):
        signature = "getReserves()((uint112,uint112,uint32))"
        calls = []
        for address in pool_addresses:
            call = Call(address, signature, [(address, lambda x: x)], block_number)
            calls.append(call)
        result = multicall_by_chunk(self.http_endpoint, calls)
        for k, v in result.items():
            if v:
                result[k] = (v[0], v[1])
            else:
                # KyberDMM doesn't have getReserves()((uint112,uint112,uint32))
                # like 0xec303ce1edbebf7e71fc7b350341bb6a6a7a6381
                signature = "getReserves()((uint112,uint112))"
                call = Call(k, signature, [(k, lambda x: x)], block_number)
                result[k] = multicall_by_chunk(self.http_endpoint, [call])[k]

        return result

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        signature0 = "token0()(address)"
        signature1 = "token1()(address)"
        calls = []
        for address in pool_addresses:
            call0 = Call(address, signature0, [(address + "_0", lambda x: x)])
            call1 = Call(address, signature1, [(address + "_1", lambda x: x)])
            calls.extend([call0, call1])
        result = multicall_by_chunk(self.http_endpoint, calls)

        formatted_result = {}
        for k, v in result.items():
            address = k[:-2]
            if address not in formatted_result:
                formatted_result[address] = []
            if k.endswith("_0"):
                formatted_result[address] = [v] + formatted_result[address]
            else:
                formatted_result[address].append(v)

        for k, v in formatted_result.items():
            formatted_result[k] = tuple(v)

        return formatted_result

    def fetch_pools_fee(self, addresses: List[str]):
        result = {}
        for address in addresses:
            result[address] = 3000  # 0.3%
        return result

    @memoize(maxsize=512)
    def calculate_price(
        self,
        pool_info: PoolInfo,
        token0: str,
        token1: str,
        decimals0: int,
        decimals1: int,
    ):
        reserve_info = pool_info.reserve_info
        token0_reserve, token1_reserve = reserve_info
        if token0 == pool_info.token_addresses[0]:
            price = token1_reserve / token0_reserve
        else:
            price = token0_reserve / token1_reserve

        return price * (1 - pool_info.fee * 1e-6)

    @staticmethod
    def calculate_amount_in_by_slippage(
        pool_reserve_info, slippage=0.005, reverse=False
    ):
        token_reserve0, token_reserve1 = pool_reserve_info
        # price = token_reserve1 / (token_reserve0 + amount_in)
        # amount_in = (token_reserve1 / price) - token_reserve0
        if reverse:
            price = token_reserve0 / token_reserve1 * (1 - slippage)
            return math.floor(token_reserve0 / price - token_reserve1)
        else:
            price = token_reserve1 / token_reserve0 * (1 - slippage)
            return math.floor(token_reserve1 / price - token_reserve0)

    def calculate_slippage(
        self,
        pool_info: PoolInfo,
        amount_in: int,
        token0: str,
        token1: str,
        decimals0: int,
        decimals1: int,
    ) -> float:
        token_reserve0, token_reserve1 = pool_info.reserve_info

        reverse = token0 == pool_info.token_addresses[1]

        if reverse:
            return 1 - (token_reserve0 / (token_reserve1 + amount_in)) / (
                token_reserve0 / token_reserve1
            )

        else:
            return 1 - (token_reserve1 / (token_reserve0 + amount_in)) / (
                token_reserve1 / token_reserve0
            )

    def calculate_amount_out(
        self,
        pool_info: PoolInfo,
        amount_in: int,
        token0: str,
        token1: str,
        reflect=False,
        **kwargs,
    ):
        """
        amount_out = amount_in * reserve1 / (reserve0 + amount_in)

        Args:
            amount_in: amount of token0
            reserve_info: (reserve0, reserve1)
            fee: fee
            reverse: if True, calculate amount_in given amount_out

        Returns: amount_out has the same decimals as token1

        """
        reserve_info = pool_info.reserve_info

        token0_reserve, token1_reserve = reserve_info
        reverse = not (token0 < token1)

        reserve_in, reserve_out = (
            (token0_reserve, token1_reserve)
            if not reverse
            else (token1_reserve, token0_reserve)
        )

        amount_in_with_fee = amount_in * 997
        numerator = amount_in_with_fee * reserve_out
        denominator = reserve_in * 1000 + amount_in_with_fee
        amount_out = numerator // denominator

        if reflect:
            pool_info.reserve_info = (
                pool_info.reserve_info[0] + (-amount_out if reverse else amount_in),
                pool_info.reserve_info[1] + (amount_in if reverse else -amount_out),
            )

        return amount_out

        abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "payable": False,
                "type": "function",
            }
        ]
        from web3 import Web3

        provider = Web3.HTTPProvider(self.http_endpoint)
        w3 = Web3(provider)
        pool_address = Web3.to_checksum_address(pool_info.address)
        token1 = Web3.to_checksum_address(pool_info.token_addresses[1])
        balance_token1 = (
            w3.eth.contract(token1, abi=abi).functions.balanceOf(pool_address).call()
        )

        token0 = Web3.to_checksum_address(pool_info.token_addresses[0])
        balance_token0 = (
            w3.eth.contract(token0, abi=abi).functions.balanceOf(pool_address).call()
        )
        balance_token0 = token0_reserve
        balance_token1 = token1_reserve

        if reverse:
            amount0_out = amount_out
            amount1_out = 0
            balance_token0 = balance_token0 - amount0_out
            balance_token1 = balance_token1 + amount_in
        else:
            amount0_out = 0
            amount1_out = amount_out
            balance_token0 = balance_token0 + amount_in
            balance_token1 = balance_token1 - amount1_out
        assert amount0_out < token0_reserve and amount1_out < token1_reserve
        if balance_token0 > token0_reserve - amount0_out:
            _amount0_in = balance_token0 - (token0_reserve - amount0_out)
        else:
            _amount0_in = 0
        if balance_token1 > token1_reserve - amount1_out:
            _amount1_in = balance_token1 - (token1_reserve - amount1_out)
        else:
            _amount1_in = 0

        balance_0_adjusted = (balance_token0 * 1000) - (_amount0_in * 3)
        balance_1_adjusted = (balance_token1 * 1000) - (_amount1_in * 3)
        print(
            amount_in,
            amount0_out,
            balance_0_adjusted * balance_1_adjusted,
            token0_reserve * token1_reserve * (1000**2),
            _amount0_in,
            balance_0_adjusted,
            balance_1_adjusted,
        )
        if balance_0_adjusted * balance_1_adjusted < token0_reserve * token1_reserve * (
            1000**2
        ):
            amount_out = 0
        else:
            amount_out = max(amount0_out, amount1_out)
        return amount_out
