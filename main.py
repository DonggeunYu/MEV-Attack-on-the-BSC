import asyncio
import time
import os
import sys
import random
import traceback
from loguru import logger
from src.apis.subscribe import stream_new_block_and_pending_txs, stream_new_future_accessible_block_number
from src.crawling import get_pool_list_from_coinmarketcap
from src.types import DexInfos, DexInfo,  Transaction
from src.dex import DEX2CLASS
from src.arbitrage.search import search_arbitrage
from src.apis.transaction import send_arbitrage_attack, send_arbitrage_attack_single
from src.apis.simple import is_pending_tx

def get_dex_infos_from_pool_list(pool_list_by_dex):
    logger.info("Get dex infos from pool list")
    dex_infos = []
    for dex, pool_list in pool_list_by_dex.items():
        dex_infos.append(DexInfo(dex, pool_list))

    return DexInfos(dex_infos)


def set_token_addresses_to_dex_infos(http_endpoint, dex_infos):
    logger.info("Set token addresses to dex infos")
    for dex_info in dex_infos:
        dex_instance = DEX2CLASS[dex_info.dex](http_endpoint)
        token_addresses = dex_instance.fetch_pools_token_addresses(
            dex_info.get_all_pool_address()
        )
        for pool_info in dex_info:
            pool_info.token_addresses = token_addresses[pool_info.address]

    return dex_infos


def main(cfg, tx_queue, accessible_block_number):
    logger.add(
        "logs/arbitrage_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )
    logger.info("Main")
    pool_list_by_dex = asyncio.run(
            get_pool_list_from_coinmarketcap(cfg.coinmarketcap_config)
        )
    dex_infos = get_dex_infos_from_pool_list(pool_list_by_dex)
    dex_infos = set_token_addresses_to_dex_infos(cfg.http_endpoint, dex_infos)
    while True:
        try:
            if tx_queue.empty():
                time.sleep(0.001)
                continue
            tx: Transaction = tx_queue.get()
            now = time.time()
            """
            next_block_base_fee = calculate_next_block_base_fee(
                int(block["gasUsed"], 16),
                int(block["gasLimit"], 16),
                int(block["baseFeePerGas"], 16),
            )
            """
            arbitrage_attack = search_arbitrage(cfg, tx)

            if arbitrage_attack is None:
                logger.info(f"[{tx.tx_hash}] No arbitrage attack found")
                continue

            if not is_pending_tx(cfg.http_endpoint, tx.tx_hash):
                logger.info(f"[{tx.tx_hash}] Transaction is not pending")
                continue

            gas_price = tx.gas_price if tx.gas_price else tx.maxFeePerGas
            if arbitrage_attack.gas_used * gas_price * 1.5 < arbitrage_attack.revenue_based_on_eth:
                if accessible_block_number.value == 0:
                    logger.info("[{tx.tx_hash}] Accessible block number is not set yet")
                    asyncio.run(send_arbitrage_attack_single(cfg, arbitrage_attack, gas_price))
                    logger.info(f"[{tx.tx_hash}][{time.time() - now:.4f}] Arbitrage attack: {arbitrage_attack}")
                    logger.info(f"[{tx.tx_hash}]Victim transaction hash: {tx.tx_hash}")
                    continue
            else:
                logger.info(f"[{tx.tx_hash}][{time.time() - now:.4f}] Arbitrage attack is not profitable")
                continue

            bundle_fee = 0.0004 * 10**18
            min_gas_price_by_fee = int((tx.gas + arbitrage_attack.gas_used) /
                             arbitrage_attack.gas_used * 10 ** 9)
            max_gas_price_by_tx = int(((arbitrage_attack.revenue_based_on_eth - bundle_fee) / 1.5 /
                                 arbitrage_attack.gas_used) * 9 / 10)
            if min_gas_price_by_fee > max_gas_price_by_tx:
                logger.info(f"[{tx.tx_hash}][{time.time() - now:.4f}] Arbitrage attack is not profitable")
                continue
            rand_gas_price = random.randint(35 * 10**9, 45 * 10**9)
            gas_price = max_gas_price_by_tx
            #gas_price = rand_gas_price if rand_gas_price < max_gas_price_by_tx else max_gas_price_by_tx
            if (
                arbitrage_attack.gas_used * gas_price * 1.5 + bundle_fee
                > arbitrage_attack.revenue_based_on_eth
            ):
                logger.info(f"[{tx.tx_hash}][{time.time() - now:.4f}] Arbitrage attack is not profitable")
                continue

            asyncio.run(send_arbitrage_attack(cfg, tx, arbitrage_attack, gas_price, accessible_block_number.value))

            logger.info(f"[{tx.tx_hash}] Accessible block number: {accessible_block_number.value}")
            logger.info(f"{tx.gas} {arbitrage_attack.gas_used} {gas_price} "
                        f"{arbitrage_attack.revenue_based_on_eth}, {arbitrage_attack.gas_used}")
            logger.info(f"[{tx.tx_hash}][{time.time() - now:.4f}] Arbitrage attack: {arbitrage_attack}")
            logger.info(f"[{tx.tx_hash}]Victim transaction hash: {tx.tx_hash}")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(exc_type)
            logger.error(fname)
            logger.error(exc_tb.tb_lineno)
            logger.error(e)
            logger.error(traceback.format_exc())


def stream_new_block_and_pending_txs_runner(cfg, queue):
    logger.add(
        "logs/arbitrage_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )
    async_coro = stream_new_block_and_pending_txs(cfg, queue)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_coro)


def stream_new_future_accessible_block_number_runner(cfg, accessible_block_number):
    logger.add(
        "logs/arbitrage_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )
    async_coro = stream_new_future_accessible_block_number(cfg, accessible_block_number)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_coro)


if __name__ == "__main__":
    import multiprocessing

    from src.config import bsc_local_to_gcp_config

    cfg = bsc_local_to_gcp_config
    # local_config.http_endpoint =
    # "https://rpc.ankr.com/eth/e890114d9658d479611923cae6286ad0de6bc32dba1c1bbeae69c0e394f3a9f3"
    # local_config.ws_endpoint =
    # "wss://rpc.ankr.com/eth/ws/e890114d9658d479611923cae6286ad0de6bc32dba1c1bbeae69c0e394f3a9f3"

    queue = multiprocessing.Queue(maxsize=30)
    future_accessible_block_number = multiprocessing.Value("i", 0)
    worker_num = 6
    main_processes = []
    for _ in range(worker_num):
        main_processes.append(
            multiprocessing.Process(target=main, args=(cfg, queue, future_accessible_block_number))
        )
    stream_new_block_and_pending_txs_process = multiprocessing.Process(
        target=stream_new_block_and_pending_txs_runner, args=(cfg, queue)
    )
    stream_new_future_accessible_block_number_process = multiprocessing.Process(
        target=stream_new_future_accessible_block_number_runner, args=(cfg, future_accessible_block_number)
    )

    for main_process in main_processes:
        main_process.start()
    stream_new_block_and_pending_txs_process.start()
    stream_new_future_accessible_block_number_process.start()
    for main_process in main_processes:
        main_process.join()
    stream_new_block_and_pending_txs_process.join()
    stream_new_future_accessible_block_number_process.join()