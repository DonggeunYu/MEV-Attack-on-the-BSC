import asyncio
from loguru import logger
from aioprocessing import AioQueue
from src.config import bsc_local_to_gcp_config
from src.apis.subscribe import stream_new_block_and_pending_txs


async def main(tx_queue):
    while True:
        tx = await tx_queue.coro_get()
        logger.info(f"{tx}")


if __name__ == "__main__":
    logger.add(
        "logs/mempool.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )
    cfg = bsc_local_to_gcp_config

    tx_queue = AioQueue(maxsize=3)
    stream_new_block_and_pending_txs = stream_new_block_and_pending_txs(cfg, tx_queue)

    loop = asyncio.get_event_loop()

    tasks = [
        stream_new_block_and_pending_txs,
        main(tx_queue),
    ]

    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
