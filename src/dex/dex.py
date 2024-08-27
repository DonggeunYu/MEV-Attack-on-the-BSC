from typing import Dict, List
from ..types import PoolInfo


class DexBase:
    def __init__(self, http_endpoint: str):
        self.http_endpoint = http_endpoint

    def fetch_pools_reserve_info(self, pool_addresses: List[str]):
        raise NotImplementedError

    def fetch_pools_fee(self, pools: List[Dict[str, str]]):
        raise NotImplementedError

    @staticmethod
    def calculate_price(
        pool_info: PoolInfo, token0: str, token1: str, decimals0: int, decimals1: int
    ):
        raise NotImplementedError

    @staticmethod
    def calculate_amount_in_by_slippage(
        pool_reserve_info, slippage=0.001, reverse=False
    ):
        raise NotImplementedError

    def calculate_slippage(
        self,
        pool_info: PoolInfo,
        amount_in: float,
        token0: str,
        token1: str,
        decimals0: int,
        decimals1: int,
    ) -> float:
        raise NotImplementedError

    def calculate_amount_out(
        self, pool_info: PoolInfo, amount_in: float, token0: str, token1: str, **kwargs
    ):
        raise NotImplementedError
