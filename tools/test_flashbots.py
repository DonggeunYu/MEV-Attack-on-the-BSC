import time

import requests
from web3 import Web3
from src.types import SandwichAttack
from src.apis.transaction import send_mev_bundle
from src.config import sepolia_config
from src.utils import calculate_next_block_base_fee
from src.apis.flashbots import generate_header
from web3.exceptions import TransactionNotFound


# @pytest.mark.skip(reason="no way of currently testing this")
async def main():
    http_provider = Web3(Web3.HTTPProvider(sepolia_config.http_endpoint))
    before_block_number = 0
    bundle_reached = False
    bundles = []
    while True:
        block = http_provider.eth.get_block("latest")
        block_number = block.number
        if block_number == before_block_number:
            time.sleep(1)
            continue
        before_block_number = block_number
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

        sandwich_attack = SandwichAttack(
            block_number=victim_txs[0].blockNumber,
            block_timestamp=block_timestamp,
            txs=victim_txs,
            revenue=0,
            front_run_function_name="multiHopSwap",
            front_run_data=[[], [], [], [], [], []],
            front_run_gas_used=100000,
            back_run_function_name="multiHopSwap",
            back_run_data=[[], [], [], [], [], []],
            back_run_gas_used=100000,
            next_block_base_fee=next_block_base_fee,
            max_priority_fee_per_gas=10**9,
            max_fee_per_gas=next_block_base_fee + 10**9,
        )

        result = await send_mev_bundle(
            cfg=sepolia_config, sandwich_attack=sandwich_attack
        )
        assert (
            "flashbots" in result["bundle_has_by_builder"].keys()
        ), "Flashbots key is not in the result"

        count = 0
        while True:
            data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "flashbots_getBundleStatsV2",
                "params": [
                    {
                        "bundleHash": result["bundle_has_by_builder"]["flashbots"],
                        "blockNumber": hex(sandwich_attack.block_number),
                    }
                ],
            }

            header = generate_header(sepolia_config, data)
            response = requests.post(
                sepolia_config.builder_config.builders["flashbots"],
                json=data,
                headers=header,
            ).json()

            if (
                response["result"]["isSimulated"]
                and response["result"]["isHighPriority"]
            ):
                print("Bundle is simulated and high priority")
                break
            elif count > 30:
                print(response)
                assert False, "Bundle is not simulated and high priority"

            count += 1
            time.sleep(1)
        print(result["bundle_has_by_builder"]["flashbots"])
        bundles.append(result)

        for bundle in bundles:
            try:
                http_provider.eth.get_transaction_receipt(
                    bundle["bundle_has_by_builder"]["flashbots"]
                )
                bundle_reached = True
                print("Bundle reached")
                print(bundle)
                break
            except TransactionNotFound:
                continue

        if bundle_reached:
            break


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
