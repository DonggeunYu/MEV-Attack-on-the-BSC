import time
from loguru import logger
import websockets
import asyncio
import json
import ssl
from aioprocessing import AioQueue
from web3.exceptions import TransactionNotFound
from src.utils import get_provider

bio_ws_endpoint = "wss://germany.bsc.blxrbdn.com/ws"
http_endpoint = "http://34.22.99.244:8545"
ws_endpoint = "ws://34.22.99.244:8546"
ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
authorization_header = "ZGViNzE1MTgtOTFkOC00NjRlLWEzNDctZDZkZGU5ZThmYjdhOmNjYjZjN2E5ZmVhOGVlYWNlMTYyNDRlYmY3YTQxYTZi"


async def check_pending_txs(queue):
    w3 = get_provider(http_endpoint)
    from web3.middleware import geth_poa_middleware

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    total_time = 0
    total_avg_count = 0
    window_time = []

    tx_hashes = {}
    while True:
        delay_time = time.time()
        tx_hash, got_time = await queue.coro_get()
        tx_hashes[tx_hash] = got_time + time.time() - delay_time
        delete_tx_hashes = []
        for tx_hash, time_ in tx_hashes.items():
            if time.time() - time_ > 60:
                delete_tx_hashes.append(tx_hash)
                continue

            try:
                tx_block_number = w3.eth.get_transaction(tx_hash)["blockNumber"]
            except TransactionNotFound:
                delete_tx_hashes.append(tx_hash)
                continue
            if tx_block_number is not None:
                total_time += time.time() - time_
                total_avg_count += 1
                window_time.append(time.time() - time_)
                if len(window_time) > 100:
                    window_time.pop(0)
                delete_tx_hashes.append(tx_hash)
                logger.info(
                    f"Average time: {total_time / total_avg_count}, Window average time: {sum(window_time) / len(window_time)}"
                )
        for tx_hash in delete_tx_hashes:
            tx_hashes.pop(tx_hash)


async def bioxrouter(ws_endpoint: str, queue):
    async with websockets.connect(
        ws_endpoint,
        extra_headers={"Authorization": authorization_header},
        ssl=ssl_context,
    ) as ws:
        subscription_request = json.dumps(
            {
                "id": 1,
                "method": "subscribe",
                "params": [
                    "newTxs",
                    {
                        "blockchain_network": "BSC-Mainnet",
                        "include": [
                            "tx_hash",
                            # "tx_contents.chain_id",
                            "tx_contents.input",
                            "tx_contents.v",
                            "tx_contents.r",
                            "tx_contents.s",
                            "tx_contents.type",
                            "tx_contents.to",
                            "tx_contents.from",
                            "tx_contents.value",
                            "tx_contents.nonce",
                            "tx_contents.gas",
                            "tx_contents.gas_price",
                            "tx_contents.max_priority_fee_per_gas",
                            "tx_contents.max_fee_per_gas",
                            "tx_contents.max_fee_per_blob_gas",
                        ],
                    },
                ],
            }
        )
        await ws.send(subscription_request)

        _ = await ws.recv()

        while True:
            message = json.loads(await asyncio.wait_for(ws.recv(), timeout=18))
            tx_hash = message["params"]["result"]["txHash"]
            queue.put(["bio", tx_hash, time.time()])


async def my(ws_endpoint: str, queue):
    async with websockets.connect(ws_endpoint) as ws:
        subscription_request = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_subscribe",
                "params": ["newPendingTransactions"],
            }
        )
        await ws.send(subscription_request)

        _ = await ws.recv()

        while True:
            message = json.loads(await asyncio.wait_for(ws.recv(), timeout=18))
            tx_hash = message["params"]["result"]
            queue.put(["my", tx_hash, time.time()])


async def benchmark(queue):
    total_time = 0
    total_avg_count = 0
    window_time = []

    bio_win = []
    my_win = []
    bio_tx_hashes = {}
    my_tx_hashes = {}
    while True:
        name, tx_hash, got_time = await queue.coro_get()
        if name == "bio":
            if tx_hash in my_tx_hashes:
                my_win.append(got_time - my_tx_hashes[tx_hash])
                my_tx_hashes.pop(tx_hash)
            bio_tx_hashes[tx_hash] = got_time
        else:
            if tx_hash in bio_tx_hashes:
                bio_win.append(got_time - bio_tx_hashes[tx_hash])
                bio_tx_hashes.pop(tx_hash)
            my_tx_hashes[tx_hash] = got_time

        print(
            f"bio: {len(bio_win), sum(bio_win[:-50]) / len(bio_win[:-50]) if len(bio_win) > 50 else 0}"
        )
        print(
            f"my: {len(my_win), sum(my_win[:-50]) / len(my_win[:-50]) if len(my_win) > 50 else 0}"
        )


if __name__ == "__main__":
    tx_queue = AioQueue(maxsize=1024 * 4)
    tasks = [
        bioxrouter(bio_ws_endpoint, tx_queue),
        my(ws_endpoint, tx_queue),
        # check_pending_txs(tx_queue)
        benchmark(tx_queue),
    ]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
