import time

import requests
import pytest
from web3 import Web3
from src.types import SandwichAttack
from src.apis.transaction import send_mev_bundle
from src.utils import calculate_next_block_base_fee

sepolia_config = None


@pytest.mark.skip(reason="no way of currently testing this")
async def test_send_mev_bundle():
    http_provider = Web3(Web3.HTTPProvider(sepolia_config.http_endpoint))
    block = http_provider.eth.get_block("latest")
    block_number = block.number
    block_timestamp = block.timestamp
    next_block_base_fee = calculate_next_block_base_fee(
        block.gasUsed, block.gasLimit, block.baseFeePerGas
    )

    pending_txs = http_provider.eth.get_block("pending", full_transactions=True)
    victim_txs = []
    for tx in pending_txs["transactions"]:
        if tx.to is None or tx.input == "0x":
            continue
        victim_txs.append(tx)
        if len(victim_txs) == 2:
            break

    assert block_number + 1 == victim_txs[0].blockNumber, "Block number is not the same"

    sandwich_attack = SandwichAttack(
        block_number=victim_txs[0].blockNumber,
        block_timestamp=block_timestamp + 120,
        txs=victim_txs,
        revenue=0,
        front_run_function_name="multiHopSwap",
        front_run_data=[[], [], [], [], [], []],
        front_run_gas_used=100000,
        back_run_function_name="multiHopSwap",
        back_run_data=[[], [], [], [], [], []],
        back_run_gas_used=100000,
        next_block_base_fee=next_block_base_fee,
        max_priority_fee_per_gas=10e9,
        max_fee_per_gas=next_block_base_fee + 10e9,
    )

    result = await send_mev_bundle(cfg=sepolia_config, sandwich_attack=sandwich_attack)

    assert "flashbots" in result.keys(), "Flashbots key is not in the result"

    """
    {
  "jsonrpc": "2.0",
  "id": 1,
  "method": "flashbots_getBundleStatsV2",
  "params": [
    {
      bundleHash,       // String, returned by the flashbots api when calling eth_sendBundle
      blockNumber,       // String, the block number the bundle was targeting (hex encoded)
    }
  ]
}
    """
    while True:
        response = requests.post(
            sepolia_config.flashbots_rpc_endpoint,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "flashbots_getBundleStatsV2",
                "params": [result["flashbots"], hex(sandwich_attack.block_number + 1)],
            },
        )
        print(response)
        time.sleep(1)
