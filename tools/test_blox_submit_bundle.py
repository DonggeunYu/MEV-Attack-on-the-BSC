import json
import ssl
import asyncio
import time

import websockets
from web3 import Web3
from src.config import bsc_local_to_gcp_config


async def send_bundle(cfg):
    provider = Web3(
        Web3.HTTPProvider(
            "http://107.23.123.88:8545",
        )
    )
    nonce = provider.eth.get_transaction_count(cfg.account_address)
    raw_tx = {
        "from": cfg.account_address,
        "to": "0x965Df5Ff6116C395187E288e5C87fb96CfB8141c",
        "value": 4 * 10**12,
        "gas": 21022,
        "gasPrice": 1 * 10**9,
        "nonce": nonce + 1,
        "chainId": 56,
    }
    signed_tx = provider.eth.account.sign_transaction(raw_tx, cfg.account_private_key)
    raw_tx = signed_tx.rawTransaction.hex()

    raw_victim_tx = {
        "from": cfg.account_address,
        "to": "0x965Df5Ff6116C395187E288e5C87fb96CfB8141c",
        "value": 0,
        "gas": 21001,
        "gasPrice": 1 * 10**9,
        "nonce": nonce,
        "chainId": 56,
    }
    signed_victim_tx = provider.eth.account.sign_transaction(
        raw_victim_tx, cfg.account_private_key
    )
    raw_victim_tx = signed_victim_tx.rawTransaction.hex()



    before_block_number = 0
    while True:
        block_number = provider.eth.get_block_number()
        if before_block_number == block_number:
            await asyncio.sleep(0.26)
            continue
        next_block_number = hex(block_number + 1)

        async with websockets.connect(
            "wss://mev.api.blxrbdn.com/ws",
            extra_headers=[("Authorization", cfg.bloxroute_authorization)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE),
        ) as ws:
            request = json.dumps(
                {
                    "id": 1,
                    "method": "blxr_simulate_bundle",
                    "params": {
                        "blockchain_network": "BSC-Mainnet",
                        "transaction": [raw_victim_tx, raw_tx],
                        "block_number": next_block_number,
                        "state_block_number": "latest",
                        #"mev_builders": {"bloxroute": "", "all": ""},
                    },
                }
            )
            await ws.send(request)
            response = await ws.recv()
            response = json.loads(response)
            if "error" in response:
                print(f"Failed to simulate arbitrage attack: {response}")
                return None
            print(f"Simulated arbitrage attack: {response}")

        async with websockets.connect(
            "wss://mev.api.blxrbdn.com/ws",
            extra_headers=[("Authorization", cfg.bloxroute_authorization)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE),
        ) as ws:
            request = json.dumps(
                {
                    "id": 1,
                    "method": "blxr_submit_bundle",
                    "params": {
                        "blockchain_network": "BSC-Mainnet",
                        "transaction": [raw_victim_tx, raw_tx],
                        "block_number": next_block_number,
                        #"mev_builders": {"bloxroute": "", "all": ""},
                    },
                }
            )
            await ws.send(request)
            response = await ws.recv()
            response = json.loads(response)
            if "error" in response:
                print(f"Failed to send arbitrage attack: {response}")
                return None
            tx_hash = response["result"]["bundleHash"]
            print(f"Arbitrage attack bundle hash: {tx_hash}")
            print(
                f"Arbitrage attack transaction hash: {signed_tx.hash.hex()}"
            )
            #time.sleep(0.3)
        break

if __name__ == "__main__":
    cfg = bsc_local_to_gcp_config
    tx_hash = asyncio.run(send_bundle(cfg))
    print(f"Bundle transaction hash: {tx_hash}")
