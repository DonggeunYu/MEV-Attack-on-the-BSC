import time
from pyrevm.pyrevm import EVM, Env, BlockEnv
from web3 import Web3
import eth_utils
import eth_abi

to_ca = Web3.to_checksum_address

provider = Web3(Web3.HTTPProvider("http://34.22.99.244:8545"))
transaction_hash = "0x1da6263075696f0d57b31fe327acc6213eac6a5156438462eea38e20cc8216ad"
transaction = provider.eth.get_transaction(transaction_hash)
print(transaction)
sender = to_ca(transaction["from"])
receiver = to_ca(transaction["to"])
input = transaction["input"]
value = transaction["value"]

evm = EVM(
    # can fork from a remote node
    fork_url="http://34.22.99.244:8545",
    fork_block_number=19369397,
    # can set tracing to true/false
    tracing=True,
    # can configure the environment
    env=Env(
        block=BlockEnv(
            number=19369397, timestamp=1709646911, prevrandao=bytes([0] * 32)
        )
    ),
)


def get_function_signature(abi, function_name):
    for item in abi:
        if item["name"] == function_name:
            return item


# generate abi for the calldata from the human readable interface
abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [],
        "name": "sync",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"internalType": "uint256", "name": "amount0Out", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1Out", "type": "uint256"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
        ],
        "name": "swap",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


now = time.time()

# encode the function signature
fn_abi = get_function_signature(abi, "getReserves")
input_args_types = [x["type"] for x in fn_abi["inputs"]]
output_args_types = [x["type"] for x in fn_abi["outputs"]]
calldata = eth_utils.function_abi_to_4byte_selector(fn_abi)
calldata += eth_abi.encode(input_args_types, [])
result, _ = evm.call_raw(
    caller="0xdF3504E9d05E54197F5d6Db864194b199258571D",
    to="0x60a39010e4892b862d1bb6bdde908215ac5af6f3",
    data=calldata,
)
hex_string = "".join([format(byte, "02x") for byte in result])
result = bytes.fromhex(hex_string)

print(eth_abi.decode(output_args_types, result))


result, _ = evm.call_raw_committing(
    caller=sender,
    to=receiver,
    value=value,
    data=bytes.fromhex(input[2:]),
)

# encode the function signature
fn_abi = get_function_signature(abi, "getReserves")
input_args_types = [x["type"] for x in fn_abi["inputs"]]
output_args_types = [x["type"] for x in fn_abi["outputs"]]
calldata = eth_utils.function_abi_to_4byte_selector(fn_abi)
calldata += eth_abi.encode(input_args_types, [])
result, _ = evm.call_raw(
    caller="0xdF3504E9d05E54197F5d6Db864194b199258571D",
    to="0x60a39010e4892b862d1bb6bdde908215ac5af6f3",
    data=calldata,
)
hex_string = "".join([format(byte, "02x") for byte in result])
result = bytes.fromhex(hex_string)

print(eth_abi.decode(output_args_types, result))

print(time.time() - now)
