import time
import eth_utils
import eth_abi
from src.apis.simple import get_timestamp, get_block_number
from typing import Optional, List, Dict
from pyrevm.pyrevm import EVM as _EVM
from pyrevm.pyrevm import Env, BlockEnv
from .types import Transaction
from src.apis.transaction import contract_abi
from web3.exceptions import BlockNotFound

token_abi = [
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "dst", "type": "address"},
            {"name": "wad", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "name": "approve",
        "outputs": [],
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
        ],
        "constant": False,
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def update_commit_count_decorator(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.commit_count += 1
        return result

    return wrapper


class EVM:
    def __init__(
            self,
            http_endpoint: str,
            account_address: str,
            contract_address: Optional[str] = None,
    ):
        self.http_endpoint = http_endpoint
        self.account_address = account_address
        self.__contract_address = contract_address
        self.contract_address_for_test = None
        self._evm = Optional[_EVM]
        self.fork_block_number = None
        self.block_timestamp = None

    @property
    def contract_address(self):
        if self.__contract_address is None:
            return self.__contract_address_for_test
        else:
            return self.__contract_address

    @property
    def latest_gas_used(self):
        return self._evm.result.gas_used

    @property
    def block_number(self):
        return self._evm.env.block.number

    def set(self, fork_block_number: str):
        self.fork_block_number = fork_block_number
        if self.fork_block_number in ["latest", "pending"]:
            self.block_timestamp = int(time.time())
        else:
            assert fork_block_number.startswith("0x")
            try:
                self.block_timestamp = (
                        get_timestamp(self.http_endpoint, fork_block_number) + 3
                )
            except BlockNotFound:
                self.block_timestamp = int(time.time())

        self._reset()
        self.snapshot = self._evm.snapshot()
        self.commit_count = 0

    def revert(self):
        if self.commit_count > 0:
            try:
                self._evm.revert(self.snapshot)
            except OverflowError:
                pass
            self.snapshot = self._evm.snapshot()
            self.commit_count = 0

    def put_balance(self, amount):
        self.transfer(
                "0x8894e0a0c962cb723c1976a4421c95949be2d4e3",
                self.contract_address,
                "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                amount,
            )

    def _reset(self):
        if self.fork_block_number in ["latest", "pending"]:
            block_hex_number = hex(get_block_number(self.http_endpoint))
        else:
            block_hex_number = self.fork_block_number
        self._evm = _EVM(
            # can fork from a remote node
            fork_url=self.http_endpoint,
            fork_block=block_hex_number,
            # can set tracing to true/false
            tracing=False,
            # can configure the environment
            # disable_eip3607=True for transaction from senders with deployed code
            # https://github.com/bluealloy/revm/blob/fe841be0ed2b01c3a1e34c7d45c0c8cf65808db2/crates/primitives/src/env.rs#L196-L200
            env=Env(
                block=BlockEnv(
                    number=int(block_hex_number, 16),
                    timestamp=self.block_timestamp,
                    prevrandao=bytes([0] * 32)
                ),
            ),
        )

        if self.__contract_address is None:
            file = open("contract/bytecode/contracts/BSC.sol/BSC.bin", "r")
            bytecode = file.read()
            file.close()
            self.__contract_address_for_test = self._evm.deploy(
                deployer=self.account_address, code=bytes.fromhex(bytecode)
            )
            assert isinstance(self.__contract_address_for_test, str)
            print(f"EVM: Deployed contract at {self.__contract_address_for_test}")

            # Set 100ETH to the contract for testing
            self.put_balance(1 * 10 ** 18)
    def print_logs(self):
        for log in self._evm.result.logs:
            print("--------------------")
            print("Address", log.address)
            data = []
            for data in log.data:
                if isinstance(data, bytes):
                    data = data.hex()
                else:
                    ds = []
                    for d in data:
                        ds.append(d.hex())
                    data.append(ds)
            print("data", data)
            print("topics", log.topics)

    def balance(self, address: str) -> int:
        return self._evm.get_balance(address)

    def balance_of(self, address: str, token: str) -> int:
        result = self.call_function(
            caller="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # vitalik.eth
            to=token,
            value=0,
            function_name="balanceOf",
            input=[address],
            abi=token_abi,
            is_static=True,
        )
        return result[0]

    def balance_of_contract(self, token: str) -> int:
        result = self.call_function(
            caller=self.account_address,
            to=token,
            value=0,
            function_name="balanceOf",
            input=[self.contract_address],
            abi=token_abi,
            is_static=True,
        )
        return result[0]

    def transfer(self, caller: str, to: str, token: str, value: int):
        result = self.call_function(
            caller=caller,
            to=token,
            value=0,
            function_name="balanceOf",
            input=[caller],
            abi=token_abi,
            is_static=True,
        )

        assert result[0] >= value, f"Insufficient balance: {result[0]} < {value}"
        result = self.call_function(
            caller=caller,
            to=token,
            value=0,
            function_name="transfer",
            input=[to, value],
            abi=token_abi,
        )
        assert result[0] is not False

    def get_uniswap_v2_amount_out(self, amount_in, pool_address, token0, token1):
        real_amount_in, _ = self.call_function(
            caller=self.account_address,
            to=self.contract_address,
            value=0,
            function_name="getUniswapV2AmountOut",
            input=[pool_address, token0, token1, amount_in],
            abi=contract_abi,
        )
        return real_amount_in[0]

    def get_uniswap_reserve(self, pool_address):
        _contract_abi = [
            {"constant": True, "inputs": [], "name": "getReserves",
             "outputs": [{"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                         {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                         {"internalType": "uint32", "name": "_blockTimestampLast",
                          "type": "uint32"}], "payable": False, "stateMutability": "view",
             "type": "function"}
        ]
        result = self.call_function(
            caller=self.account_address,
            to=pool_address,
            value=0,
            function_name="getReserves",
            input=[],
            abi=_contract_abi,
        )
        return result

    def encode_function_input_data(self, function_name, input, abi):
        # Find the function signature
        function_signature = None
        for item in abi:
            if item["name"] == function_name:
                function_signature = item
        assert (
                function_signature is not None
        ), f"Function {function_name} not found in ABI"

        input_args_types = [x["type"] for x in function_signature["inputs"]]
        output_args_types = [x["type"] for x in function_signature["outputs"]]

        calldata = eth_utils.function_abi_to_4byte_selector(function_signature)
        calldata += eth_abi.encode(input_args_types, input)
        return calldata

    def encode_function_output_data(self, function_name, bytes_result, abi):
        # Find the function signature
        function_signature = None
        for item in abi:
            if item["name"] == function_name:
                function_signature = item
        assert (
                function_signature is not None
        ), f"Function {function_name} not found in ABI"

        output_args_types = [x["type"] for x in function_signature["outputs"]]
        return eth_abi.decode(output_args_types, bytes_result)

    def call_function(
            self,
            caller: str,
            to: str,
            value,
            function_name,
            input,
            abi: List[Dict],
            is_static=False,
    ):
        assert isinstance(input, (list, tuple))
        # Find the function signature
        calldata = self.encode_function_input_data(function_name, input, abi)

        bytes_result = self._evm.message_call(
            caller=caller,
            to=to,
            value=value,
            calldata=calldata,
            is_static=is_static,
            # gas=None if is_static else 2 * 10 ** 6,
            # gas_price=None if is_static else 10 ** 9,
        )
        hex_string = "".join([format(byte, "02x") for byte in bytes_result])
        bytes_result = bytes.fromhex(hex_string)
        result = self.encode_function_output_data(function_name, bytes_result, abi)
        return result

    @update_commit_count_decorator
    def message_call_from_tx(self, tx: Transaction):
        result = self._evm.message_call(
            caller=tx.caller,
            to=tx.receiver,
            gas=tx.gas,
            gas_price=tx.gas_price,
            value=tx.value if isinstance(tx.value, int) else int(tx.value, 16),
            calldata=bytes.fromhex(tx.data[2:])
            if isinstance(tx.data, str)
            else tx.data,
        )
        return result

    """
    def send_multi_hop_swap(self, amounts_in, stages, exchanges, pool_addresses,
                            token_addresses, preserve_amounts):
        assert isinstance(amounts_in, list)
        assert isinstance(exchanges, list)
        assert isinstance(pool_addresses, list)
        assert isinstance(token_addresses, list)
        assert isinstance(preserve_amounts, list)

        result, gas_used = self.call_function(
            caller=self.account_address,
            to=self.get_contract_address(),
            value=0,
            function_name="multiHopSwap",
            input=[amounts_in, stages, exchanges, pool_addresses, token_addresses, preserve_amounts],
            abi=contract_abi,
            commit=True
        )
        return result[0], gas_used
    """

    @update_commit_count_decorator
    def send_multi_hop_swap(
            self,
            amounts_in,
            stages,
            exchanges,
            pool_addresses,
            token_addresses,
            preserve_amounts,
    ):
        assert isinstance(amounts_in, list)
        assert isinstance(exchanges, list)
        assert isinstance(pool_addresses, list)
        assert isinstance(token_addresses, list)
        assert isinstance(preserve_amounts, list)

        result, gas_used = self.call_function(
            caller=self.account_address,
            to=self.contract_address,
            value=0,
            function_name="multiHopSwap",
            input=[
                amounts_in,
                stages,
                exchanges,
                pool_addresses,
                token_addresses,
                preserve_amounts,
            ],
            abi=contract_abi,
        )
        return result[0], gas_used

    @update_commit_count_decorator
    def send_with_funtion_name(self, function_name, data):
        result = self.call_function(
            caller=self.account_address,
            to=self.contract_address,
            value=0,
            function_name=function_name,
            input=data,
            abi=contract_abi,
        )
        return result

    @update_commit_count_decorator
    def send_arbitrage(self, amount_in, exchanges, pool_addresses, token_addresses):
        function_name = "multiHopArbitrageWithoutRelay"
        result = self.call_function(
            caller=self.account_address,
            to=self.contract_address,
            value=0,
            function_name=function_name,
            input=[0, amount_in, exchanges, pool_addresses, token_addresses],
            abi=contract_abi,
        )
        return result

    @update_commit_count_decorator
    def call_sandwich_front_run(self, amount_in, exchanges, pool_addresses, token_addresses):
        function_name = "sandwichFrontRun"
        result = self.call_function(
            caller=self.account_address,
            to=self.contract_address,
            value=0,
            function_name=function_name,
            input=[amount_in, exchanges, pool_addresses, token_addresses],
            abi=contract_abi,
        )
        return result

    @update_commit_count_decorator
    def call_sandwich_back_run(self, amount_in, exchanges, pool_addresses, token_addresses):
        function_name = "sandwichBackRun"
        result = self.call_function(
            caller=self.account_address,
            to=self.contract_address,
            value=0,
            function_name=function_name,
            input=[amount_in, exchanges, pool_addresses, token_addresses],
            abi=contract_abi,
        )
        return result

    def call_deposit(self, caller, token, amount):
        function_name = "deposit"

        self.call_function(
            caller=caller,
            to=token,
            value=0,
            function_name="approve",
            input=[self.contract_address, amount],
            abi=token_abi,
        )

        self.call_function(
            caller=caller,
            to=self.contract_address,
            value=0,
            function_name=function_name,
            input=[token, amount],
            abi=contract_abi,
        )
