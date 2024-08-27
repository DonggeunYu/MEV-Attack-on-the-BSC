import copy
import time

from tqdm import tqdm
from typing import Dict, List, Tuple
from loguru import logger
from .utils import debug_mode
from .dex import DexBase, DEX_CONTRACT_MAP
from .types import (
    TokenInfo,
    TokenInfos,
    DexInfo,
    DexInfos,
    NHopsOfPaths,
    PoolInfo,
    Path,
)
from itertools import permutations

from .api_utils import (
    get_block_number,
    get_decimals_by_token_address,
    subscribe_new_blocks,
    get_gas_price,
    get_arbitrage_estimated_gas,
    send_arbitrage,
    get_eth_based_price_by_token,
)


class Arb:
    def __init__(
        self,
        rpc_endpoint: Dict[str, str],
        flash_loan_token_address_list: List[str],
        pool_address_for_token_price: Dict[str, Tuple[str, bool]],
        dex_infos: DexInfos,
        min_nhops: int,
        max_nhops: int,
        block_number_threshold: int,
        account_address: str,
        account_private_key: str,
        contract_address: str,
        target_profit: float,
    ):
        self.http_endpoint = rpc_endpoint["http_endpoint"]
        self.wss_endpoint = rpc_endpoint["wss_endpoint"]

        self.flash_loan_token_address_list = flash_loan_token_address_list
        self.pool_address_for_token_price = pool_address_for_token_price
        self.min_nhops = min_nhops
        self.max_nhops = max_nhops
        self.block_number_threshold = block_number_threshold
        self.account_address = account_address
        self.account_private_key = account_private_key
        self.contract_address = contract_address
        self.target_profit = target_profit

        dex_infos: DexInfos = self._add_token_address_of_pool(dex_infos)
        self.token_infos = self._get_token_infos_from_dex_infos(dex_infos)
        self.nhops_of_paths = self._generate_nhops_of_paths(dex_infos)
        self.token_infos = self._filter_token_infos_by_nhops_of_paths(
            self.token_infos, self.nhops_of_paths
        )
        self.dex_infos = self._filter_dex_infos_by_paths(dex_infos)

    def _add_token_address_of_pool(self, dex_infos: DexInfos) -> DexInfos:
        for dex_info in dex_infos:
            dex_name = dex_info.name
            list_of_pool_address = dex_info.get_all_pool_address()
            dex_instance = self._dex_name_to_instance(dex_name)
            list_of_pool_address_of_token_addresses = (
                dex_instance.fetch_pools_token_addresses(list_of_pool_address)
            )
            for (
                pool_address,
                token_addresses,
            ) in list_of_pool_address_of_token_addresses.items():
                dex_info.update_pool_tokens_by_address(
                    address=pool_address, token_addresses=token_addresses
                )

        return dex_infos

    def _generate_nhops_of_paths(self, dex_infos: DexInfos) -> NHopsOfPaths:
        logger.info("Start generating paths")

        always_first_paths = []
        candidate_last_pools = []
        candidate_addresses_of_last_pool = []
        for dex_info in dex_infos:
            for pool_info in dex_info.list_of_pool_info:
                permutations_of_token_addresses = list(
                    permutations(pool_info.token_addresses, 2)
                )
                for token0_address, token1_address in permutations_of_token_addresses:
                    if token0_address in self.flash_loan_token_address_list:
                        path = Path(
                            token0_address,
                            first_pool_info=pool_info,
                            first_pool_token_address=(
                                token0_address,
                                token1_address,
                            ),
                        )
                        always_first_paths.append(path)

                        if pool_info.address not in candidate_addresses_of_last_pool:
                            candidate_last_pools.append(pool_info)
                            candidate_addresses_of_last_pool.append(pool_info.address)

        del candidate_addresses_of_last_pool

        nhops_of_paths = NHopsOfPaths()
        for i in tqdm(range(self.min_nhops, self.max_nhops + 1), desc="Generate paths"):
            nhops_of_paths.add_n(i)
            candidate_paths = copy.deepcopy(always_first_paths)

            for n in tqdm(range(1, i), desc=f"n={i}"):
                new_candidate_paths = []

                if n < i - 1:
                    for dex_info in dex_infos:
                        for pool_info in dex_info.list_of_pool_info:
                            pool_info: PoolInfo

                            # Middle nhops can be any token
                            for candidate_path in candidate_paths:
                                permutations_of_token_addresses = list(
                                    permutations(pool_info.token_addresses, 2)
                                )
                                latest_pool = candidate_path[-1]
                                for (
                                    token0_address,
                                    token1_address,
                                ) in permutations_of_token_addresses:
                                    lowered_latest_pool_token_addresses = [
                                        token.lower()
                                        for token in latest_pool.token_addresses
                                    ]
                                    if (
                                        latest_pool.address == pool_info.address
                                        and token0_address.lower()
                                        in lowered_latest_pool_token_addresses
                                        and token1_address
                                        in lowered_latest_pool_token_addresses
                                    ):
                                        continue
                                    if candidate_path.validate_token_address_is_final(
                                        token0_address
                                    ):
                                        new_candidate_path = copy.deepcopy(
                                            candidate_path
                                        )
                                        new_candidate_path.append(
                                            pool_info, (token0_address, token1_address)
                                        )
                                        new_candidate_paths.append(new_candidate_path)
                else:
                    for candidate_path in candidate_paths:
                        latest_pool = candidate_path[-1]
                        for candidate_last_pool in candidate_last_pools:
                            permutations_of_token_addresses = list(
                                permutations(candidate_last_pool.token_addresses, 2)
                            )

                            for (
                                token0_address,
                                token1_address,
                            ) in permutations_of_token_addresses:
                                lowered_latest_pool_token_addresses = [
                                    token.lower()
                                    for token in latest_pool.token_addresses
                                ]
                                if (
                                    latest_pool.address == candidate_last_pool.address
                                    and token0_address.lower()
                                    in lowered_latest_pool_token_addresses
                                    and token1_address
                                    in lowered_latest_pool_token_addresses
                                ):
                                    continue
                                if (
                                    candidate_path.validate_token_address_is_final(
                                        token0_address
                                    )
                                    and candidate_path.validate_token_address_is_flash_loan_token(
                                        token1_address
                                    )
                                ):
                                    new_candidate_path = copy.deepcopy(candidate_path)
                                    new_candidate_path.append(
                                        candidate_last_pool,
                                        (token0_address, token1_address),
                                    )
                                    new_candidate_paths.append(new_candidate_path)

                candidate_paths = new_candidate_paths
            nhops_of_paths.set_paths(i, candidate_paths)

            for n, paths in nhops_of_paths.items():
                logger.info(f"n: {n}, paths: {len(paths)}")
                for path in paths:
                    line = str(path)
                    logger.debug(line)

        logger.info("Finish generating paths")
        return nhops_of_paths

    def _get_token_infos_from_dex_infos(self, dex_infos: DexInfos) -> TokenInfos:
        token_addresses = []
        for dex_info in dex_infos:
            for pool_info in dex_info.list_of_pool_info:
                for token_address in pool_info.token_addresses:
                    if token_address not in token_addresses:
                        token_addresses.append(token_address)

        token_dicimal_by_address = get_decimals_by_token_address(
            self.http_endpoint, token_addresses
        )

        token_infos = TokenInfos()
        for token_address, value in token_dicimal_by_address.items():
            token_infos.append(
                TokenInfo(value["symbol"], token_address, value["decimals"])
            )

        return token_infos

    def _filter_token_infos_by_nhops_of_paths(
        self, token_infos: TokenInfos, nhops_of_paths: NHopsOfPaths
    ) -> TokenInfos:
        """
        Filter tokens that are not needed in the path

        Returns:
            List[Dict[str, str]]: chain => tokens
        """
        logger.info("Start filtering tokens")
        filtered_tokens = []
        for token_info in token_infos:
            need = False
            for paths in nhops_of_paths.values():
                for path in paths:
                    for pool_info in path:
                        if token_info.address in pool_info.token_addresses:
                            filtered_tokens.append(token_info)
                            need = True
                            break
                    if need:
                        break
                if need:
                    break

        token_infos = TokenInfos(filtered_tokens)

        logger.debug(f"tokens: {len(token_infos)}")
        for token in token_infos:
            logger.debug(f"{token.symbol}({token.address})")

        logger.info("Finish filtering tokens")
        return token_infos

    def _filter_dex_infos_by_paths(self, dex_infos: DexInfos) -> DexInfos:
        logger.info("Start filtering dex pool")

        filtered_list_of_dex_info = []
        for dex_info in dex_infos:
            filtered_list_of_pool_info = []
            for pool_info in dex_info:
                need = False
                for paths in self.nhops_of_paths.values():
                    for path in paths:
                        if pool_info.address in [pool.address for pool in path]:
                            filtered_list_of_pool_info.append(pool_info)
                            need = True
                            break
                    if need:
                        break

            if len(filtered_list_of_pool_info) > 0:
                filtered_dex_info = DexInfo(
                    dex_info.name, dex_info.address, filtered_list_of_pool_info
                )
                filtered_list_of_dex_info.append(filtered_dex_info)

        dex_infos = DexInfos(filtered_list_of_dex_info)

        logger.info(f"dex: {len(dex_infos)}")
        for dex_info in dex_infos:
            dex_name = dex_info.name
            dex_info_length = len(dex_info)
            logger.info(f"{dex_name}: {dex_info_length}")

        logger.info("Finish filtering dex pool")
        return dex_infos

    def _dex_name_to_instance(self, dex: str):
        from .dex import DEX_MAP

        try:
            return DEX_MAP[dex](self.http_endpoint)
        except KeyError:
            raise ValueError(f"Dex {dex} not supported")

    async def run(self):
        logger.info("Start running")

        # Prepare dex
        def get_dex_instances():
            dex_instances: Dict[str, DexBase] = {}
            for dex_info in self.dex_infos:
                dex_name = dex_info.name
                dex_instances[dex_name] = self._dex_name_to_instance(dex_name)
            return dex_instances

        def update_fee_info(dex_instances):
            for dex_name, dex_instance in tqdm(
                dex_instances.items(), desc="Update fee info"
            ):
                dex_info = self.dex_infos.get_dex_by_name(dex_name)
                pool_addresses = dex_info.get_all_pool_address()
                fee = dex_instance.fetch_pools_fee(pool_addresses)
                list_of_pool_info = dex_info.list_of_pool_info
                for pool_info in list_of_pool_info:
                    pool_info.set_fee(fee[pool_info.address])

        def update_reserve_info(dex_instances):
            for dex_name, dex_instance in tqdm(
                dex_instances.items(), desc="Update reserve info"
            ):
                dex_info = self.dex_infos.get_dex_by_name(dex_name)
                pool_addresses = dex_info.get_all_pool_address()
                pools_reserve_info = dex_instance.fetch_pools_reserve_info(
                    pool_addresses
                )

                list_of_pool_info = dex_info.list_of_pool_info
                for pool_info in list_of_pool_info:
                    pool_info.set_reserve_info(pools_reserve_info[pool_info.address])

        def simple_calculate_profit(nhops_of_paths, target_profit):
            target_profit = 1 + target_profit
            profitable_nhops_paths = NHopsOfPaths()
            for n, paths in tqdm(
                nhops_of_paths.items(), desc="Simple calculate profit"
            ):
                profitable_paths = []
                for path in tqdm(paths, desc=f"n={n}"):
                    profit = 1
                    for i in range(n):
                        pool_info = path[i]
                        dex_name = pool_info.dex_name
                        pool_address = pool_info.address
                        token0, token1 = path.list_of_token_address[i]
                        decimals0 = self.token_infos.get_token_by_address(
                            token0
                        ).decimals
                        decimals1 = self.token_infos.get_token_by_address(
                            token1
                        ).decimals
                        origin_pool_info = self.dex_infos.get_dex_by_name(
                            dex_name
                        ).get_pool_by_address(pool_address)
                        price = dex_instances[dex_name].calculate_price(
                            origin_pool_info, token0, token1, decimals0, decimals1
                        )

                        profit *= price

                    if profit > target_profit:
                        path.set_simple_calculated_price(profit)
                        profitable_paths.append(path)

                if profitable_paths:
                    profitable_nhops_paths.add_n(n)
                    profitable_nhops_paths.set_paths(n, profitable_paths)

            return profitable_nhops_paths

        def simulate_amount_of_maximal_profit(profitable_paths):
            logger.info("Start simulating amount of maximal profit")
            block_number = get_block_number(self.http_endpoint)

            simulated_profitable_paths = NHopsOfPaths()
            max_count = 100
            count = 0

            now = time.time()
            for n, paths in profitable_paths.items():
                simulated_profitable_paths.add_n(n)
                simulated_paths = []

                for path in paths:
                    path: Path
                    # Initialize amount of token0
                    flash_loan_token_address = path.flash_loan_token_address
                    flash_loan_token_decimals = self.token_infos.get_token_by_address(
                        flash_loan_token_address
                    ).decimals
                    amount_in = 10 ** (max(flash_loan_token_decimals, 2))
                    alpha = 2
                    to_right = True
                    maximized_amount_in = amount_in
                    maximized_amount_flash_swap = 0
                    maximized_profit = 0
                    before_profit = 0

                    same_maximized_profit = 0

                    while True:
                        amount = amount_in

                        amount_flash_swap = 0
                        found_flash_swap_dex = False
                        for i in range(n):
                            pool_address = path[i].address
                            dex_name = path[i].dex_name
                            if not found_flash_swap_dex and (
                                dex_name == "UniswapV3" or dex_name == "SushiswapV3"
                            ):
                                amount_flash_swap = amount
                                found_flash_swap_dex = True

                            (
                                token_0_address,
                                token_1_address,
                            ) = path.list_of_token_address[i]
                            dex_info = self.dex_infos.get_dex_by_name(dex_name)

                            origin_pool_info = dex_info.get_pool_by_address(
                                pool_address
                            )
                            amount = dex_instances[dex_name].calculate_amount_out(
                                origin_pool_info,
                                amount,
                                token_0_address,
                                token_1_address,
                                block_number=block_number,
                            )

                        if (amount - amount_in) > maximized_profit:
                            maximized_amount_flash_swap = amount_flash_swap
                            maximized_amount_in = amount_in
                            maximized_profit = amount - amount_in
                        else:
                            same_maximized_profit += 1
                            if same_maximized_profit >= 100:
                                break

                        if before_profit > amount - amount_in:
                            to_right = not to_right
                            if alpha < 1.1:
                                alpha *= 1.02
                            else:
                                alpha *= 0.98

                        before_profit = amount - amount_in

                        if to_right:
                            amount_in *= alpha
                        else:
                            amount_in /= alpha
                        amount_in = int(amount_in)

                    if time.time() - now > 5 or maximized_profit > 0:
                        path.set_amount_in(maximized_amount_in)
                        path.set_amount_flash_swap(maximized_amount_flash_swap)
                        path.expected_profit = maximized_profit
                        simulated_paths.append(path)
                        count += 1
                        if count >= max_count:
                            break

                simulated_profitable_paths.set_paths(n, simulated_paths)
                if time.time() - now > 5 or count >= max_count:
                    break

            return simulated_profitable_paths

        # Once
        dex_instances = get_dex_instances()
        update_fee_info(dex_instances)

        # Stream
        before_block_number = 0

        if debug_mode():

            async def new_blocks_callback():
                yield {"params": {"result": {"number": hex(int(time.time()))}}}

            new_blocks_callback = new_blocks_callback()
        else:
            new_blocks_callback = subscribe_new_blocks(self.wss_endpoint)

        async for result in new_blocks_callback:
            block_number = int(result["params"]["result"]["number"], 16)
            if block_number == before_block_number:
                continue
            before_block_number = block_number
            gas_price = get_gas_price(self.http_endpoint)
            logger.info(f"block_number: {block_number}, gas_price: {gas_price}")

            dex_instances = get_dex_instances()
            update_reserve_info(dex_instances)
            profitable_paths = simple_calculate_profit(
                self.nhops_of_paths, self.target_profit
            )

            profit_calculated_paths = simulate_amount_of_maximal_profit(
                profitable_paths
            )

            found_profitable_paths = False
            eth_based_token_price_map = {}
            for token in self.flash_loan_token_address_list:
                price = get_eth_based_price_by_token(
                    self.http_endpoint, self.pool_address_for_token_price, token
                )
                eth_based_token_price_map[token] = price

            found_profitable_path_count = 0
            for n, paths in profit_calculated_paths.items():
                for path in paths:
                    if path.expected_profit > 0:
                        found_profitable_path_count += 1
            logger.info(f"Found profitable paths: {found_profitable_path_count}")

            for n, paths in profit_calculated_paths.items():
                for path in paths:
                    if path.expected_profit > 0:
                        exchanges = [DEX_CONTRACT_MAP[dex.dex_name] for dex in path]
                        pool_addresses = [pool.address for pool in path]
                        token_addresses = []
                        for token in path.list_of_token_address:
                            token_addresses.extend(token)

                        try:
                            estimated_gas = get_arbitrage_estimated_gas(
                                self.http_endpoint,
                                self.account_address,
                                self.contract_address,
                                gas_price,
                                path.amount_in,
                                path.amount_flash_swap,
                                exchanges,
                                pool_addresses,
                                token_addresses,
                            )
                        except Exception as e:
                            logger.error(
                                f"Error: {self.account_address}, {self.contract_address}, {gas_price}, {path.amount_in}, {(path.expected_profit / 1e18):.8f}, {exchanges}, {pool_addresses}, {token_addresses}"
                            )
                            if (path.expected_profit / 1e18) > 0.02:
                                logger.error("AAAAAAAAAAA")
                            logger.error(f"Error: {e}")
                            continue

                        eth_based_expected_profit = (
                            path.expected_profit
                            * eth_based_token_price_map[path.flash_loan_token_address]
                        )
                        cost = estimated_gas * gas_price
                        print(
                            path.expected_profit,
                            eth_based_expected_profit,
                            cost,
                            estimated_gas,
                        )
                        if eth_based_expected_profit > cost:
                            logger.info(f"Profitable path: {path}")
                            logger.info(f"Estimated gas: {estimated_gas}")
                            logger.info(
                                f"Expected profit: {eth_based_expected_profit} "
                                f"({(eth_based_expected_profit / 1e18):.8f} ETH)"
                            )
                            logger.info(f"Cost: {cost} ({(cost / 1e18):.8f} ETH)")

                            tx_hash = send_arbitrage(
                                self.http_endpoint,
                                self.account_address,
                                self.account_private_key,
                                self.contract_address,
                                gas_price,
                                path.amount_in,
                                path.amount_flash_swap,
                                exchanges,
                                pool_addresses,
                                token_addresses,
                                estimated_gas,
                            )
                            logger.info(f"Transaction hash: {tx_hash.hex()}")
                            found_profitable_paths = True

                for path in paths:
                    path.set_amount_in(0)
                    path.set_amount_flash_swap(0)
                    path.expected_profit = 0

            if not found_profitable_paths:
                logger.info("No profitable paths")

            if debug_mode():
                break
