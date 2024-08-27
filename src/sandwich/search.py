import time
from loguru import logger
from itertools import permutations
from typing import List
from ..types import SandwichAttack, DexInfos, Transaction, Path, SwapEvent, ArbitrageAttack
from ..evm import EVM
from ..dex import DEX2ID
from .optimization import optimize_sandwich_contract
from .simulation import simulate_sandwich, calculate_uniswap_v2_sandwich
from ..config import Config
from ..utils import eq_address, is_in_address_list
from ..apis.contract import (get_pool_from_token_pair, get_addresses_balance_by_token_address,
                             get_reserve_by_pool_address, get_maximum_rate_between_pool)
from ..dex import ID2DEX, DEX2AMM
from src.apis.transaction import contract_abi
from src.arbitrage.search import search_arbitrage

def search_sandwich_candidate_path(
        cfg: Config, victim_tx: Transaction, block_number
):
    find_link_pool_candidate = []
    native_token_swap_events = []
    not_native_token_swap_events = []
    for swap_event in victim_tx.swap_events:
        if eq_address(cfg.wrapped_native_token_address, swap_event.token_in):
            native_token_swap_events.append(swap_event)
        else:
            not_native_token_swap_events.append(swap_event)
            find_link_pool_candidate.append([cfg.wrapped_native_token_address,
                                             swap_event.token_in])
    token_pair_pools = get_pool_from_token_pair(cfg, find_link_pool_candidate)
    addresses_by_token_address = {}
    for token_pair_pool in token_pair_pools:
        if token_pair_pool["token0"] not in addresses_by_token_address:
            addresses_by_token_address[token_pair_pool["token0"]] = []
        addresses_by_token_address[token_pair_pool["token0"]].append(token_pair_pool["address"])
    token_balance_pools = get_addresses_balance_by_token_address(cfg.http_endpoint,
                                                                 addresses_by_token_address,
                                                                 block_number)

    candidate_paths = {}
    for swap_event in native_token_swap_events:
        path = Path(
            amount_in=swap_event.amount_in,
            exchanges=[DEX2ID[swap_event.dex]],
            pool_addresses=[swap_event.address],
            token_addresses=[swap_event.token_in, swap_event.token_out],
        )
        candidate_paths[swap_event] = path

    for swap_event in not_native_token_swap_events:
        front_balance = 0
        front_pool_dex = None
        front_pool_address = None

        for token_pair_pool in token_pair_pools:
            if eq_address(swap_event.address, token_pair_pool["address"]):
                continue

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
                    front_balance = found_token_balance_pool["balance"]
                    front_pool_dex = token_pair_pool["dex"]
                    front_pool_address = token_pair_pool["address"]

        if front_pool_address:
            path = Path(
                amount_in=0,
                exchanges=[DEX2ID[front_pool_dex], DEX2ID[swap_event.dex]],
                pool_addresses=[front_pool_address, swap_event.address],
                token_addresses=[cfg.wrapped_native_token_address,
                                 swap_event.token_in, swap_event.token_out],
            )
            candidate_paths[swap_event] = path

    return candidate_paths

def check_only_uniswap_v2_in_path(path):
    for exchange in path.exchanges:
        amm = DEX2AMM[ID2DEX[exchange]]
        if amm != "UNISWAP_V2_AMM":
            return False
    return True

def get_only_uniswap_v2_path(path):
    if len(path.pool_addresses) == 1:
        amm = DEX2AMM[ID2DEX[path.exchanges[0]]]
        if amm != "UNISWAP_V2_AMM":
            return None
        return path.pool_addresses[0]
    elif len(path.pool_addresses) == 2:
        amm = DEX2AMM[ID2DEX[path.exchanges[1]]]
        if amm != "UNISWAP_V2_AMM":
            return None
        return path.pool_addresses[1]

def is_only_uniswap_v2_path(path):
    for exchange in path.exchanges:
        amm = DEX2AMM[ID2DEX[exchange]]
        if amm != "UNISWAP_V2_AMM":
            return False
    return True

def _get_reserve_by_pool_address_from_path(cfg, paths: List[Path], block_number):
    pool_address = set()
    for path in paths:
        r = get_only_uniswap_v2_path(path)
        if r:
            pool_address.update([r])
    return get_reserve_by_pool_address(cfg.http_endpoint, list(pool_address), block_number)

def search_sandwich(cfg: Config, victim_tx: Transaction, block_number="pending") -> (
        SandwichAttack, ArbitrageAttack):
    logger.info(f"[{victim_tx.tx_hash}] Search sandwich attack")

    evm = EVM(
        http_endpoint=cfg.http_endpoint,
        account_address=cfg.account_address,
        contract_address=cfg.contract_address,
    )
    evm.set(block_number)
    block_number = evm.block_number

    paths = search_sandwich_candidate_path(cfg, victim_tx, block_number)
    if not paths:
        logger.info(f"[{victim_tx.tx_hash}] Not found sandwich attack path")
        del evm
        return None, None, block_number
    logger.info(f"[{victim_tx.tx_hash}] Found {len(paths)} sandwich attack paths")

    reserve_by_pools = _get_reserve_by_pool_address_from_path(cfg, list(paths.values()),
                                                              block_number)
    for swap_event, path in paths.items():
        print(path)
        maximum_rates = get_maximum_rate_between_pool(cfg, path, block_number)
        if all([maximum_rate > 1 for maximum_rate in maximum_rates]):
            logger.info(f"[{victim_tx.tx_hash}] Invalid maximum rate {maximum_rates}")
        amount_in = 0
        if is_only_uniswap_v2_path(path):
            amount_in, expected_revenue = calculate_uniswap_v2_sandwich(cfg, reserve_by_pools,
                                                                       swap_event, path,
                                                            0.01, block_number)
            if expected_revenue < 1e9 * 100000 * 2: # 100000 gas * 2tx * 1e9 wei
                continue

        (front_run_amount_in, back_run_amount_in, front_run_gas_used, back_run_gas_used,
         revenue_based_on_eth) = simulate_sandwich(cfg, evm, victim_tx, path, amount_in, maximum_rates)
        if revenue_based_on_eth == 0:
            logger.info(f"[{victim_tx.tx_hash}] Not possible to make profit")
        else:
            evm.revert()
            pool_balance = evm.balance_of(path.pool_addresses[-1], path.token_addresses[-1])
            swap_event = [
                    SwapEvent(
                        dex=ID2DEX[path.exchanges[0]],
                        address=path.pool_addresses[0],
                        token_in=path.token_addresses[0],
                        token_out=path.token_addresses[1],
                        amount_in=front_run_amount_in,
                        amount_out=back_run_amount_in,
                    )
                ]
            if len(path.pool_addresses) == 2:
                swap_event.append(
                        SwapEvent(
                            dex=ID2DEX[path.exchanges[1]],
                            address=path.pool_addresses[1],
                            token_in=path.token_addresses[1],
                            token_out=path.token_addresses[2],
                            amount_in=0,
                            amount_out=0,
                        ))

            front_run = Transaction(
                chain_id=victim_tx.chain_id,
                tx_hash=victim_tx.tx_hash,
                gas=front_run_gas_used * 2,
                gas_price=victim_tx.gas_price + 1,
                maxFeePerGas=None,
                maxPriorityFeePerGas=None,
                value=0,
                data="0x" + evm.encode_function_input_data(
                    "sandwichFrontRun",
                    [front_run_amount_in, path.exchanges, path.pool_addresses,
                                path.token_addresses],
                    abi=contract_abi,
                ).hex(),
                caller=evm.account_address,
                receiver=evm.contract_address,
                swap_events=swap_event,
                access_list=None,
                nonce=victim_tx.nonce,
                r=1,
                s=1,
                v=1,
            )
            #arbitrage_attack = search_arbitrage(cfg, front_run, evm=evm)

            del evm
            return SandwichAttack(
                front_run_function_name="sandwichFrontRun",
                front_run_data=[front_run_amount_in, path.exchanges, path.pool_addresses,
                                path.token_addresses, back_run_amount_in, pool_balance],
                front_run_gas_used=front_run_gas_used,
                back_run_function_name="sandwichBackRunWithBloxroute",
                back_run_data=[back_run_amount_in, path.exchanges, path.pool_addresses,
                               path.token_addresses],
                back_run_gas_used=back_run_gas_used,
                revenue_based_on_eth=revenue_based_on_eth
            ), None, block_number

    return None, None, block_number
