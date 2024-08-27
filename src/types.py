from typing import Any, List, Union, Tuple
from web3 import Web3


# Config
class TokenDict(dict):
    symbol: str
    address: str
    decimals: int


class TokenInfo:
    def __init__(self, name: str, address: str, decimals: int):
        self.symbol = name
        self.address = address
        self.decimals = decimals


class TokenInfos:
    def __init__(self, list_of_token_info: List[TokenInfo] = None):
        self.list_of_token_info: List[TokenInfo] = []
        if isinstance(list_of_token_info, list):
            self.list_of_token_info = list_of_token_info

    def append(self, token_info: TokenInfo):
        self.list_of_token_info.append(token_info)

    def get_token_by_symbol(self, symbol: str) -> TokenInfo:
        for token in self.list_of_token_info:
            if token.symbol == symbol:
                return token
        raise ValueError(f"Token {symbol} not found")

    def get_token_by_address(self, address: str) -> TokenInfo:
        for token in self.list_of_token_info:
            if token.address == address:
                return token
        raise ValueError(f"Token {address} not found")

    def __iter__(self):
        return iter(self.list_of_token_info)

    def __len__(self):
        return len(self.list_of_token_info)

    def __str__(self):
        result = ""
        for token in self.list_of_token_info:
            result += f"{token.symbol} {token.address}\n"
        return result


class PoolInfo:
    def __init__(
            self,
            dex_name: str,
            address: str,
            token_addresses: Tuple[str, ...] = None,
            fee: int = None,
    ):
        self.dex_name = dex_name
        self.address = address
        self.token_addresses = token_addresses
        self.price: float
        self.fee = fee
        self.reserve_info: Any
        self.fee: int

    def __eq__(self, other):
        if isinstance(other, str):
            return self.address == other
        elif isinstance(other, PoolInfo):
            return self.address == other.address
        else:
            raise ValueError(f"Cannot compare PoolInfo with {type(other)}")

    def set_reserve_info(self, reserve_info: Any):
        self.reserve_info = reserve_info

    def set_fee(self, fee: float):
        self.fee = fee

    def __str__(self):
        return f"Pool: {self.dex_name} {self.address} {self.token_addresses} {self.fee}"


class DexInfo:
    def __init__(
            self,
            dex: str,
            list_of_pool_address: Union[List[str], List[PoolInfo]],
    ):
        self.dex = dex
        if isinstance(list_of_pool_address[0], PoolInfo):
            self.list_of_pool_info = list_of_pool_address
        else:
            self.list_of_pool_info = [
                PoolInfo(dex, address) for address in list_of_pool_address
            ]

    def get_all_pool_address(self) -> List[str]:
        return [pool_info.address for pool_info in self.list_of_pool_info]

    def update_pool_tokens_by_address(
            self, address: str, token_addresses: Tuple[str, ...]
    ):
        for i in range(len(self.list_of_pool_info)):
            if self.list_of_pool_info[i].address == address:
                self.list_of_pool_info[i].token_addresses = token_addresses

    def get_pool_by_address(self, address: str) -> PoolInfo:
        for pool in self.list_of_pool_info:
            if pool.address == address:
                return pool
        raise ValueError(f"Pool {address} not found")

    def __iter__(self):
        return iter(self.list_of_pool_info)

    def __len__(self):
        return len(self.list_of_pool_info)


class DexInfos:
    def __init__(self, list_of_dex: List[DexInfo]):
        self.list_of_dex_info: List[DexInfo] = list_of_dex

    def get_dex_by_name(self, name: str) -> DexInfo:
        for dex in self.list_of_dex_info:
            if dex.name == name:
                return dex
        raise ValueError(f"Dex {name} not found")

    def __iter__(self):
        return iter(self.list_of_dex_info)

    def __len__(self):
        return len(self.list_of_dex_info)


# Path
class Path:
    def __init__(self, amount_in, exchanges, pool_addresses, token_addresses):
        self.amount_in = amount_in
        self.exchanges = exchanges
        self.pool_addresses = [
            Web3.to_checksum_address(address) for address in pool_addresses
        ]
        self.token_addresses = [
            Web3.to_checksum_address(address) for address in token_addresses
        ]

    def __str__(self):
        output = ""
        for idx in range(len(self.exchanges)):
            from .dex import ID2NAME

            exchange_name = ID2NAME[self.exchanges[idx]]
            output += f"[{exchange_name}] {self.pool_addresses[idx]} ({self.token_addresses[idx]}, {self.token_addresses[idx + 1]})\n"
        return output

    def __eq__(self, other):
        if isinstance(other, Path):
            return (
                    self.exchanges == other.exchanges
                    and self.pool_addresses == other.pool_addresses
                    and self.token_addresses == other.token_addresses
            )
        else:
            return False


class SwapEvent:
    def __init__(self, dex=None, address=None, token_in=None, token_out=None, amount_in=0,
                 amount_out=0):
        self.dex = dex
        self.address = address
        self.token_in = token_in
        self.token_out = token_out
        self.amount_in = amount_in
        self.amount_out = amount_out

    def __str__(self):
        return f"{self.dex} {self.address} {self.token_in} {self.token_out} {self.amount_in} {self.amount_out}"

    def is_valid(self):
        valid = True
        valid &= self.dex is not None
        valid &= self.address is not None
        valid &= self.token_in is not None
        valid &= self.token_out is not None
        valid &= self.amount_in > 0
        valid &= self.amount_out > 0
        return valid


class Transaction:
    def __init__(
            self,
            chain_id,
            tx_hash,
            gas,
            gas_price,
            maxFeePerGas,
            maxPriorityFeePerGas,
            caller,
            receiver,
            value,
            data,
            nonce,
            r,
            s,
            v,
            access_list,
            swap_events: List[SwapEvent],
    ):
        self.chain_id = chain_id if chain_id is None or isinstance(chain_id, int) else int(chain_id,
                                                                                        16)
        self.tx_hash = tx_hash
        self.gas = gas if isinstance(gas, int) else int(gas, 16)
        if gas_price is None or isinstance(gas_price, int):
            self.gas_price = gas_price
        else:
            self.gas_price = int(gas_price, 16)
        if maxFeePerGas is None or isinstance(maxFeePerGas, int):
            self.maxFeePerGas = maxFeePerGas
        else:
            self.maxFeePerGas = int(maxFeePerGas, 16)
        if maxPriorityFeePerGas is None or isinstance(maxPriorityFeePerGas, int):
            self.maxPriorityFeePerGas = maxPriorityFeePerGas
        else:
            self.maxPriorityFeePerGas = int(maxPriorityFeePerGas, 16)
        self.caller = caller
        self.receiver = receiver
        self.value = value if isinstance(value, int) else int(value, 16)
        self.data = data
        self.nonce = nonce if isinstance(nonce, int) else int(nonce, 16)
        self.r = r if isinstance(r, int) else int(r, 16)
        self.s = s if isinstance(s, int) else int(s, 16)
        self.v = v if isinstance(v, int) else int(v, 16)
        self.access_list = access_list
        self.swap_events = swap_events

    def __str__(self):
        text = f"Tx: {self.tx_hash}"
        for event in self.swap_events:
            text += f"\n{event}"
        return text


class ArbitrageAttack:
    def __init__(
            self,
            function_name: str,
            data: List[Any],
            revenue_based_on_eth: int,
            gas_used: int,
    ):
        self.function_name = function_name
        self.data = data
        self.revenue_based_on_eth = revenue_based_on_eth
        self.gas_used = gas_used

    def __str__(self):
        text = f"Function: {self.function_name}, Revenue: {self.revenue_based_on_eth}, Gas used: {self.gas_used}\n"
        if self.function_name == "multipleArbitrage":
            for i in range(len(self.data[0]) - 1):
                left = self.data[0][i]
                right = self.data[0][i + 1]
                text += (
                    f"Stage {i}: {self.data[1][i]} {self.data[2][left:right]} "
                    f"{self.data[3][left:right]} {self.data[4][left * 2:right * 2]}\n"
                )
        else:
            text += f"{self.data}"
        return text


class SandwichAttack:
    def __init__(
            self,
            front_run_function_name: str,
            front_run_data: List[Any],
            front_run_gas_used: int,
            back_run_function_name: str,
            back_run_data: List[Any],
            back_run_gas_used: int,
            revenue_based_on_eth: int
    ):
        self.front_run_function_name = front_run_function_name
        self.front_run_data = front_run_data
        self.front_run_gas_used = front_run_gas_used
        self.back_run_function_name = back_run_function_name
        self.back_run_data = back_run_data
        self.back_run_gas_used = back_run_gas_used
        self.revenue_based_on_eth = revenue_based_on_eth

    def __str__(self):
        text = f"Front Run Function: {self.front_run_function_name}\n"
        text += f"Front Run Data: {self.front_run_data}\n"
        text += f"Front Run Gas Used: {self.front_run_gas_used}\n"
        text += f"Back Run Function: {self.back_run_function_name}\n"
        text += f"Back Run Data: {self.back_run_data}\n"
        text += f"Back Run Gas Used: {self.back_run_gas_used}\n"
        text += f"Revenue: {self.revenue_based_on_eth}\n"
        return text