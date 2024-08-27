import time
import ssl
from typing import List, Callable
import asyncio
import traceback
from ..config import Config
from loguru import logger
import json
import websockets
from multiprocessing import Queue
from src.apis.trace_tx import trace_transaction
from ..utils import get_provider, is_in_address_list
from .contract import get_48club_validators
import aiohttp
TOP_BIT_256BIT_INT = 2**255
BIT_256BIT_INT = 2**256


async def subscribe_new_blocks(http_endpoint: str):
    w3 = get_provider(http_endpoint)
    before_block_number = 0
    while True:
        try:
            block_number = w3.eth.blockNumber
            if before_block_number == block_number:
                await asyncio.sleep(0.2)
                continue
            before_block_number = block_number
            block_data = w3.eth.getBlock(block_number)
            timestamp = block_data["timestamp"]
            gas_price = w3.eth.gas_price
            gas_used = block_data["gasUsed"]
            gas_limit = block_data["gasLimit"]
            yield {
                "params": {
                    "result": {
                        "number": hex(block_number),
                        "timestamp": hex(timestamp),
                        "baseFeePerGas": hex(gas_price),
                        "gasUsed": hex(gas_used),
                        "gasLimit": hex(gas_limit),
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error in subscribe_new_blocks: {e}")


def hex_to_uint256(hex_str):
    return int(hex_str, 16)


def hex_to_int256(hex_str):
    value = int(hex_str, 16)
    if value >= TOP_BIT_256BIT_INT:
        value -= BIT_256BIT_INT
    return value


class SwapEvent:
    def __init__(self, dex, address, amount0In, amount1In):
        self.dex = dex
        self.address = address
        self.amount0In = amount0In
        self.amount1In = amount1In
        self.token0 = None
        self.token1 = None

    def __str__(self):
        return f"{self.dex} {self.address} {self.amount0In}({self.token0}) {self.amount1In}({self.token1})"


class Transaction:
    def __init__(
        self,
        block_number,
        hash,
        gas_price,
        caller,
        receiver,
        value,
        data,
        raw_tx_data,
        swap_events: List[SwapEvent],
    ):
        self.block_number = block_number
        self.hash = hash
        self.gas_price = gas_price
        self.caller = caller
        self.receiver = receiver
        self.value = value
        self.data = data
        self.raw_tx_data = raw_tx_data
        self.swap_events = swap_events

    def __str__(self):
        text = f"Tx: {self.hash}"
        for event in self.swap_events:
            text += f"\n{event}"
        return text


def reconnecting_websocket_decorator(tag: str):
    def decorator(stream_fn: Callable):
        async def wrapper(*args, **kwargs):
            while True:
                try:
                    await stream_fn(*args, **kwargs)
                except (
                    websockets.ConnectionClosedError,
                    websockets.ConnectionClosedOK,
                ) as e:
                    import sys
                    import os

                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logger.error(exc_type)
                    logger.error(fname)
                    logger.error(exc_tb.tb_lineno)
                    logger.error(f"{tag} websocket connection closed: {e}")
                    logger.error("Reconnecting...")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"An error has occurred with {tag} websocket: {e}")
                    logger.error(traceback.format_exc())
                    await asyncio.sleep(0.1)

        return wrapper

    return decorator


@reconnecting_websocket_decorator("new block and pending txs")
async def stream_new_block_and_pending_txs(cfg: Config, tx_queue: Queue):
    logger.info(
        f"Stream new block and pending txs: {cfg.http_endpoint} {cfg.bloxroute_ws_endpoint}"
    )

    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with websockets.connect(
        cfg.bloxroute_ws_endpoint,
        extra_headers={"Authorization": cfg.bloxroute_authorization},
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
                            "tx_contents.chain_id",
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
            message = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            tx_detail = message["params"]["result"]
            if (
                "to" not in tx_detail["txContents"]
                or tx_detail["txContents"]["gas"] == "0x5208"
                or len(tx_detail["txContents"]["input"]) <= 10
            ):
                # Contract creation
                continue

            now = time.time()
            if not tx_queue.full():
                tx = trace_transaction(cfg, tx_detail)
                if tx is not None:
                    logger.info(f"[{time.time() - now:.4f}] New tx: {tx_detail['txHash']}")
                    tx_queue.put(tx)
            else:
                logger.warning(f"Loss tx: {tx_detail['txHash']}")


async def get_bloxroute_validators(bloxroute_authorization):
    """
    curl https://mev.api.blxrbdn.com \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: ZGViNzE1MTgtOTFkOC00NjRlLWEzNDctZDZkZGU5ZThmYjdhOmNjYjZjN2E5ZmVhOGVlYWNlMTYyNDRlYmY3YTQxYTZi" \
    -d '{
         "id": "1",
         "method": "bsc_mev_validators",
         "params": {
           "blockchain_network": "BSC-Mainnet"
         }
        }'
    """
    url = "https://mev.api.blxrbdn.com"
    headers = {
        "Content-Type": "application/json",
        "Authorization": bloxroute_authorization,
    }
    data = {
    "id": "1",
    "method": "bsc_mev_validators",
    "params": {
        "blockchain_network": "BSC-Mainnet"
    }
}
    async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                print(response)
                response = await response.json()
                validators = response["result"]["validators"]
                return validators


@reconnecting_websocket_decorator("new future accessible block")
async def stream_new_future_accessible_block_number(cfg, accessible_block_number: int):
    club_validators = get_48club_validators(cfg.http_endpoint)
    bloxroute_validators = asyncio.run(get_bloxroute_validators(cfg.bloxroute_authorization))

    async with websockets.connect(
            "wss://virginia.bsc.blxrbdn.com/ws",
            extra_headers=[("Authorization", cfg.bloxroute_authorization)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE)) as ws:
        # ETH Example
        subscribe_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "subscribe",
            "params": ["bdnBlocks", {"include": ["header","future_validator_info"]}, {"blockchain_network": "BSC-Mainnet"}]}

        await ws.send(json.dumps(subscribe_request))
        response = await ws.recv()
        subscription_id = json.loads(response)["result"]

        while True:
            next_notification = await ws.recv()
            next_notification = json.loads(next_notification)
            result = next_notification["params"]["result"]
            #block_number = result["header"]["number"]
            future_validator_info = result["future_validator_info"]

            if is_in_address_list(future_validator_info[0]["wallet_id"], club_validators):
                accessible_block_number.value = -1
            elif is_in_address_list(future_validator_info[0]["wallet_id"], bloxroute_validators):
                accessible_block_number.value = future_validator_info[0]["block_height"]
            else:
                accessible_block_number.value = 0