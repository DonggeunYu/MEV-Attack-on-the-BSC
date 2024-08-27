import math
from typing import Dict, List
from src.types import Path, Transaction, DexInfos, ArbitrageAttack, SwapEvent
from src.config import Config
from src.apis.contract import (
    get_pool_from_token_pair,
    get_addresses_balance_by_token_address,
get_reserve_by_pool_address,
get_n_and_s_by_pool_address
)
from ..dex import DEX2ID
from ..utils import eq_address, is_in_address_list, sort_reserve, find_value_by_address_key
from .simulation import simulate_arbitrage
from ..evm import EVM
from loguru import logger
from ..dex import DEX2CLASS, ID2DEX, DEX2AMM
from ..formula import get_multi_hop_optimal_amount_in, get_multi_hop_amount_out

def search_arbitrage_candidate_path(
        cfg: Config, victim_tx: Transaction
):
    find_link_pool_candidate = []
    native_token_swap_events = []
    not_native_token_swap_events = []
    for swap_event in victim_tx.swap_events:
        if is_in_address_list(cfg.wrapped_native_token_address,
                              [swap_event.token_in, swap_event.token_out]):
            native_token_swap_events.append(swap_event)
            find_link_pool_candidate.append([swap_event.token_in, swap_event.token_out])
        else:
            not_native_token_swap_events.append(swap_event)
            find_link_pool_candidate.append([cfg.wrapped_native_token_address,
                                             swap_event.token_out])
            find_link_pool_candidate.append([swap_event.token_in, cfg.wrapped_native_token_address])

            find_link_pool_candidate.append([swap_event.token_in, swap_event.token_out])
            find_link_pool_candidate.append([cfg.wrapped_native_token_address, swap_event.token_out])

    token_pair_pools = get_pool_from_token_pair(cfg, find_link_pool_candidate)

    addresses_by_token_address = {}
    for token_pair_pool in token_pair_pools:
        if token_pair_pool["token0"] not in addresses_by_token_address:
            addresses_by_token_address[token_pair_pool["token0"]] = []
        addresses_by_token_address[token_pair_pool["token0"]].append(token_pair_pool["address"])
    token_balance_pools = get_addresses_balance_by_token_address(cfg.http_endpoint,
                                                                 addresses_by_token_address)

    candidate_paths = {}
    for swap_event in native_token_swap_events:
        pool_dex = None
        pool_address = None
        balance = 0

        for token_pair_pool in token_pair_pools:
            if eq_address(token_pair_pool["address"], swap_event.address):
                continue
            if (eq_address(token_pair_pool["token0"], swap_event.token_in) and
                    eq_address(token_pair_pool["token1"], swap_event.token_out)):

                found_token_balance_pool = None
                for token_balance_pool in token_balance_pools:
                    if (eq_address(token_pair_pool['address'], token_balance_pool["address"]) and
                            eq_address(token_balance_pool["token_address"], swap_event.token_in)):
                                found_token_balance_pool = token_balance_pool
                if found_token_balance_pool["balance"] > balance:
                    balance = found_token_balance_pool["balance"]
                    pool_dex = token_pair_pool["dex"]
                    pool_address = token_pair_pool["address"]


        if pool_address:
            if eq_address(cfg.wrapped_native_token_address, swap_event.token_in):
                path = Path(
                    amount_in=swap_event.amount_in,
                    exchanges=[DEX2ID[pool_dex], DEX2ID[swap_event.dex]],
                    pool_addresses=[pool_address, swap_event.address],
                    token_addresses=[swap_event.token_in, swap_event.token_out, swap_event.token_in],
                )
            else:
                path = Path(
                    amount_in=0,
                    exchanges=[DEX2ID[swap_event.dex], DEX2ID[pool_dex]],
                    pool_addresses=[swap_event.address, pool_address],
                    token_addresses=[swap_event.token_out, swap_event.token_in, swap_event.token_out],
                )
            candidate_paths[swap_event] = path

    for swap_event in not_native_token_swap_events:
        front_balance = 0
        front_pool_dex = None
        front_pool_address = None

        for token_pair_pool in token_pair_pools:
            if ((eq_address(token_pair_pool["token0"], cfg.wrapped_native_token_address) and
                eq_address(token_pair_pool["token1"], swap_event.token_out)) or
                    (eq_address(token_pair_pool["token1"], cfg.wrapped_native_token_address) and
                eq_address(token_pair_pool["token0"], swap_event.token_out))):

                found_token_balance_pool = None
                for token_balance_pool in token_balance_pools:
                    if (eq_address(token_pair_pool['address'], token_balance_pool["address"]) and
                            eq_address(token_balance_pool["token_address"], token_pair_pool[
                                "token0"])):
                        found_token_balance_pool = token_balance_pool

                if found_token_balance_pool["balance"] > front_balance:
                    front_balance = found_token_balance_pool["balance"]
                    front_pool_dex = token_pair_pool["dex"]
                    front_pool_address = token_pair_pool["address"]

        back_balance = 0
        back_pool_dex = None
        back_pool_address = None
        for token_pair_pool in token_pair_pools:
            if ((eq_address(token_pair_pool["token0"], swap_event.token_in) and
                    eq_address(token_pair_pool["token1"], cfg.wrapped_native_token_address)) or
                    (eq_address(token_pair_pool["token1"], swap_event.token_in) and
                    eq_address(token_pair_pool["token0"], cfg.wrapped_native_token_address))):

                found_token_balance_pool = None
                for token_balance_pool in token_balance_pools:
                    if (eq_address(token_pair_pool['address'], token_balance_pool["address"]) and
                            eq_address(token_balance_pool["token_address"], token_pair_pool[
                                "token0"])):
                        found_token_balance_pool = token_balance_pool

                if found_token_balance_pool["balance"] > back_balance:
                    back_balance = found_token_balance_pool["balance"]
                    back_pool_dex = token_pair_pool["dex"]
                    back_pool_address = token_pair_pool["address"]

        if front_pool_address and back_pool_address:
            path = Path(
                amount_in=0,
                exchanges=[DEX2ID[front_pool_dex], DEX2ID[swap_event.dex], DEX2ID[back_pool_dex]],
                pool_addresses=[front_pool_address, swap_event.address, back_pool_address],
                token_addresses=[cfg.wrapped_native_token_address, swap_event.token_out,
                                 swap_event.token_in, cfg.wrapped_native_token_address],
            )
            candidate_paths[swap_event] = path

        front_balance = 0
        front_pool_dex = None
        front_pool_address = None
        front_second_pool_dex = None
        front_second_pool_address = None

        for token_pair_pool in token_pair_pools:
            if ((eq_address(token_pair_pool["token0"], cfg.wrapped_native_token_address) and
                eq_address(token_pair_pool["token1"], swap_event.token_in)) or
                    (eq_address(token_pair_pool["token1"], cfg.wrapped_native_token_address) and
                eq_address(token_pair_pool["token0"], swap_event.token_in))):

                found_token_balance_pool = None
                for token_balance_pool in token_balance_pools:
                    if (eq_address(token_pair_pool['address'], token_balance_pool["address"]) and
                            eq_address(token_balance_pool["token_address"], token_pair_pool[
                                "token0"])):
                        found_token_balance_pool = token_balance_pool

                if found_token_balance_pool["balance"] > front_balance:
                    front_second_pool_dex = front_pool_dex
                    front_second_pool_address = front_pool_address

                    front_balance = found_token_balance_pool["balance"]
                    front_pool_dex = token_pair_pool["dex"]
                    front_pool_address = token_pair_pool["address"]

        middle_balance = 0
        middle_pool_dex = None
        middle_pool_address = None

        for token_pair_pool in token_pair_pools:
            if ((eq_address(token_pair_pool["token0"], swap_event.token_in) and
                eq_address(token_pair_pool["token1"], swap_event.token_out)) or
                    (eq_address(token_pair_pool["token1"], swap_event.token_in) and
                eq_address(token_pair_pool["token0"], swap_event.token_out))):

                found_token_balance_pool = None
                for token_balance_pool in token_balance_pools:
                    if (eq_address(token_pair_pool['address'], token_balance_pool["address"]) and
                            eq_address(token_balance_pool["token_address"], token_pair_pool[
                                "token0"])):
                        found_token_balance_pool = token_balance_pool

                if found_token_balance_pool["balance"] > middle_balance:
                    middle_balance = found_token_balance_pool["balance"]
                    middle_pool_dex = token_pair_pool["dex"]
                    middle_pool_address = token_pair_pool["address"]

        if front_pool_address and middle_pool_address and front_second_pool_dex:
            path = Path(
                amount_in=0,
                exchanges=[DEX2ID[front_pool_dex], DEX2ID[middle_pool_dex], DEX2ID[swap_event.dex], DEX2ID[front_second_pool_dex]],
                pool_addresses=[front_pool_address, middle_pool_address, swap_event.address,
                                front_second_pool_address],
                token_addresses=[cfg.wrapped_native_token_address, swap_event.token_in,
                                 swap_event.token_out,
                                 swap_event.token_in, cfg.wrapped_native_token_address],
            )
            candidate_paths[swap_event] = path

    return candidate_paths

def calculate_arbitrage_uniswap_v2_optimal_amount_in(tx: Transaction, path: Path,
                                                                 reserve_by_pools,
                                                     n_and_s_by_pools):
    data = []
    for idx, pool_address in enumerate(path.pool_addresses):
        n, s = find_value_by_address_key(pool_address, n_and_s_by_pools)
        reserves = find_value_by_address_key(pool_address, reserve_by_pools)
        reserve_in, reserve_out = sort_reserve(path.token_addresses[idx],
                                          path.token_addresses[idx + 1],
                                          reserves[0], reserves[1])
        for swap_event in tx.swap_events:
            if eq_address(pool_address, swap_event.address):
                if eq_address(path.token_addresses[idx], swap_event.token_in):
                    reserve_in += swap_event.amount_in
                    reserve_out -= swap_event.amount_out
                else:
                    reserve_in -= swap_event.amount_out
                    reserve_out += swap_event.amount_in

        data.append((n, s, reserve_in, reserve_out))
    try:
        amount_in = get_multi_hop_optimal_amount_in(data)
    except:
        logger.error(f"Error calculating optimal amount in: {data}")
        return 0, 0
    if amount_in < 0:
        return 0, 0
    amount_out = get_multi_hop_amount_out(amount_in, data)
    return amount_in, amount_out - amount_in


def check_only_uniswap_v2_in_path(path):
    for exchange in path.exchanges:
        amm = DEX2AMM[ID2DEX[exchange]]
        if amm != "UNISWAP_V2_AMM":
            return False
    return True

def _get_reserve_by_pool_address_from_path(cfg, paths: List[Path], block_number):
    pool_address = set()
    for path in paths:
        if check_only_uniswap_v2_in_path(path):
            pool_address.update(path.pool_addresses)

    return get_reserve_by_pool_address(cfg.http_endpoint, list(pool_address), block_number)

def _get_n_and_s_by_pool_address_from_path(cfg, paths: List[Path], block_number):
    pool_address = set()
    for path in paths:
        if check_only_uniswap_v2_in_path(path):
            pool_address.update(path.pool_addresses)

    return get_n_and_s_by_pool_address(cfg.http_endpoint, list(pool_address), block_number)

def search_arbitrage(
        cfg: Config, victim_tx: Transaction, block_number="latest", evm=None
) -> ArbitrageAttack:
    logger.info(f"[{victim_tx.tx_hash}] Search arbitrage")

    if evm is None:
        evm = EVM(
            http_endpoint=cfg.http_endpoint,
            account_address=cfg.account_address,
            contract_address=cfg.contract_address,
        )
        evm.set(block_number)
    block_number = evm.block_number

    candidate_paths = search_arbitrage_candidate_path(cfg, victim_tx)
    logger.info(f"[{victim_tx.tx_hash}] Found {len(candidate_paths)} candidate paths")

    if len(candidate_paths) == 0:
        del evm
        return None

    reserve_by_pools = _get_reserve_by_pool_address_from_path(cfg, list(candidate_paths.values()),
                                                              block_number)
    n_and_s_by_pools = _get_n_and_s_by_pool_address_from_path(cfg, list(candidate_paths.values()),
                                                              block_number)
    paths = []
    for event, path in candidate_paths.items():
        if check_only_uniswap_v2_in_path(path):
            amount_in, revenue = calculate_arbitrage_uniswap_v2_optimal_amount_in(victim_tx, path,
                                                                                    reserve_by_pools,
                                                                                    n_and_s_by_pools,
                                                                                  )
            if revenue < 1e9 * 100000 * 2: # 100000 gas * 2tx * 1e9 wei
                continue

        amount_in, revenue, gas_used = simulate_arbitrage(cfg, evm, victim_tx, path)
        if revenue > 10 ** 14:
            path.amount_in = amount_in
            paths.append(path)
            break

    if len(paths) == 0:
        del evm
        return None

    function_name = "multiHopArbitrageWithBloxroute"
    path = paths[0]

    return ArbitrageAttack(
        function_name=function_name,
        data=[
            0,
            path.amount_in,
            path.exchanges,
            path.pool_addresses,
            path.token_addresses,
        ],
        revenue_based_on_eth=revenue,
        gas_used=gas_used,
    )
