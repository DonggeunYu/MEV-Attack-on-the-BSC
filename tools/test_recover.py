from src.utils import get_provider
from src.types import Transaction
from src.apis.transaction import recover_raw_transaction

ws = get_provider("https://bsc-mainnet.core.chainstack.com/8b86535e4243bdf9a37eea574a6f3ae3")
local_ws = get_provider("http://107.23.123.88:8545")
print(local_ws.eth.block_number)

victim_tx_hash = "0xe9e2612b7df8b8f719d9b63c4d11c9f84a9b7cc0f4a34bd9507e616ee8ce2f66"
tx_detail = local_ws.eth.get_transaction(victim_tx_hash)
print(tx_detail)
print(ws.eth.get_raw_transaction(victim_tx_hash).hex())
tx = Transaction(
        chain_id=tx_detail["chainId"] if "chainId" in tx_detail else None,
        tx_hash=tx_detail["hash"].hex(),
        gas=tx_detail["gas"],
        gas_price=tx_detail["gasPrice"] if "gasPrice" in tx_detail else None,
        maxFeePerGas=tx_detail["maxFeePerGas"] if "maxFeePerGas" in tx_detail else None,
        maxPriorityFeePerGas=tx_detail["maxPriorityFeePerGas"] if "maxPriorityFeePerGas" in tx_detail else None,
        caller=tx_detail["from"],
        receiver=tx_detail["to"],
        value=tx_detail["value"],
        data=tx_detail["input"],
        nonce=tx_detail["nonce"],
        r=tx_detail["r"].hex(),
        s=tx_detail["s"].hex(),
        v=tx_detail["v"],
        access_list=tx_detail["accessList"] if "accessList" in tx_detail else None,
        swap_events=None,
    )
raw_tx = recover_raw_transaction(tx)
print(raw_tx)