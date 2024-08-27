import asyncio
import time
import os
import sys
import gc
import traceback
from loguru import logger
from src.apis.subscribe import stream_new_block_and_pending_txs, stream_new_future_accessible_block_number
from src.crawling import get_pool_list_from_coinmarketcap
from src.types import DexInfos, DexInfo
from src.dex import DEX2CLASS
from src.utils import eq_address
from src.sandwich.search import search_sandwich
from src.apis.transaction import (send_sandwich_attack_using_bloxroute,
                                  send_sandwich_attack_using_48club,
                                  get_48_club_minimum_gas_price,
                                  send_sandwich_attack_using_general,
                                  send_recover_sandwich_attack)
from src.apis.simple import is_pending_tx, is_successful_tx, get_block_number, delay_time, get_timestamp

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
        "logs/sandwich_{time:YYYY-MM-DD}.log",
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

    block_number = get_block_number(cfg.http_endpoint)
    timestamp = get_timestamp(cfg.http_endpoint, block_number)
    while True:
        try:
            if tx_queue.empty():
                time.sleep(0.0001)
                continue
            tx = tx_queue.get()

            if timestamp + 3 < time.time():
                updated_block = False
                while updated_block is False:
                    new_block_number = get_block_number(cfg.http_endpoint)
                    if new_block_number > block_number:
                        block_number = new_block_number
                        updated_block = True
                    else:
                        time.sleep(0.01)
                timestamp = get_timestamp(cfg.http_endpoint, block_number)

            sandwich_attack, arbitrage_attack, block_number = search_sandwich(cfg, tx)

            if block_number < get_block_number(cfg.http_endpoint):
                logger.info(f"[{tx.tx_hash}] Block number is too old: {block_number}")
                continue
            if sandwich_attack is None:
                logger.info("No sandwich attack found")
                continue

            if timestamp + 3 < time.time():
                logger.info(f"[{tx.tx_hash}] Timestamp is too old: {timestamp}")
                continue
            if not is_pending_tx(cfg.http_endpoint, tx.tx_hash):
                logger.info(f"[{tx.tx_hash}] Transaction is not pending")
                continue

            if accessible_block_number.value > 0:
                logger.info("Use bloXroute")

                back_run_gas_price = int((tx.gas + sandwich_attack.back_run_gas_used) /
                                      sandwich_attack.back_run_gas_used * 1e9)
                bundle_fee = int((sandwich_attack.revenue_based_on_eth -
                                1e9 * sandwich_attack.front_run_gas_used -
                                  back_run_gas_price * sandwich_attack.back_run_gas_used)
                                 * 98 / 100)
                if bundle_fee < 1e9:
                    logger.info(f"Bundle fee is too low: {bundle_fee}")
                    continue

                sandwich_attack.front_run_data = sandwich_attack.front_run_data[:4]
                sandwich_attack.back_run_function_name = "sandwichBackRunWithBloxroute"
                asyncio.run(send_sandwich_attack_using_bloxroute(cfg, tx, sandwich_attack,
                                                                 accessible_block_number.value, back_run_gas_price,
                            bundle_fee))
                logger.info(f"[{tx.tx_hash}] Gas price: {back_run_gas_price / 1e9}({back_run_gas_price})")
                logger.info(f"[{tx.tx_hash}] Bundle fee: {bundle_fee / 1e9}({bundle_fee})")
            elif accessible_block_number.value == -1:
                logger.info("Use 48club")
                gas_price = int((sandwich_attack.revenue_based_on_eth -
                                 ((tx.gas_price + 1) * sandwich_attack.front_run_gas_used +
                                   1e9 * sandwich_attack.back_run_gas_used)) /
                                21000 * 98 / 100)
                if gas_price < 1e9:
                    logger.info(f"Gas price is too low: {gas_price}")
                    continue
                minimum_gas_price = asyncio.run(get_48_club_minimum_gas_price())
                if gas_price < minimum_gas_price:
                    logger.info(f"48club gas price is too low: {gas_price} < {minimum_gas_price}")
                    continue

                sandwich_attack.front_run_data = sandwich_attack.front_run_data[:4]
                sandwich_attack.back_run_function_name = "sandwichBackRun"
                asyncio.run(send_sandwich_attack_using_48club(cfg, tx, sandwich_attack, gas_price))
                logger.info(f"[{tx.tx_hash}] Gas price: {gas_price / 1e9}({gas_price})")
            else:
                logger.info("Use General")
                if (arbitrage_attack is not None and arbitrage_attack.revenue_based_on_eth > 10 **
                        16):
                    logger.info(f"[{tx.tx_hash}] Arbitrage attack found")
                    continue

                expected_profit = sandwich_attack.revenue_based_on_eth - (((tx.gas_price + 1) *
                                                           sandwich_attack.front_run_gas_used + tx.gas_price *
                                                                   sandwich_attack.back_run_gas_used))
                if expected_profit < 10 ** 15:
                    logger.info(f"[{tx.tx_hash}] Not possible to make profit")
                    continue
                front_run_gas_price = max(tx.gas_price + 1, int(expected_profit * 0.3) //
                                          sandwich_attack.front_run_gas_used)
                #front_run_gas_price = tx.gas_price + 1

                sandwich_attack.front_run_function_name = "sandwichFrontRunDifficult"
                sandwich_attack.back_run_function_name = "sandwichBackRunDifficult"
                sandwich_attack.back_run_data += [block_number + 1]
                delay_time(cfg.http_endpoint, block_number)
                previous_front_run_tx, previous_back_run_tx = asyncio.run(
                send_sandwich_attack_using_general(cfg, tx, sandwich_attack, front_run_gas_price))

                while is_pending_tx(cfg.http_endpoint, previous_back_run_tx):
                    time.sleep(1)
                    logger.info(f"[{tx.tx_hash}] Previous sandwich attack is pending")
                if is_successful_tx(cfg.http_endpoint, previous_front_run_tx) and \
                    not is_successful_tx(cfg.http_endpoint, previous_back_run_tx):
                    if eq_address(sandwich_attack.front_run_data[3][-1], cfg.wrapped_native_token_address):
                        logger.info(f"[{tx.tx_hash}] Previous sandwich attack is failed (but same token)")
                        continue
                    logger.info(f"[{tx.tx_hash}] Previous sandwich attack is failed")

                    sandwich_attack.back_run_data = sandwich_attack.back_run_data[:4]
                    sandwich_attack.back_run_function_name = "sandwichBackRun"
                    recover_tx_hash = asyncio.run(send_recover_sandwich_attack(cfg,
                                                                                   sandwich_attack))
                    logger.info(f"[{tx.tx_hash}] Recovered sandwich attack {recover_tx_hash}")

            logger.info(f"[{tx.tx_hash}] Accessible block number: {accessible_block_number.value}")
            logger.info(f"Sandwich attack: {sandwich_attack}")
            logger.info(f"Victim transaction hash: {tx.tx_hash}")

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
        "logs/sandwich_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )
    async_coro = stream_new_block_and_pending_txs(cfg, queue)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_coro)

def stream_new_future_accessible_block_number_runner(cfg, accessible_block_number):
    logger.add(
        "logs/sandwich_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )
    async_coro = stream_new_future_accessible_block_number(cfg, accessible_block_number)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_coro)

if __name__ == "__main__":
    import multiprocessing

    from src.config import bsc_gcp_config

    cfg = bsc_gcp_config

    queue = multiprocessing.Queue(maxsize=40)
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