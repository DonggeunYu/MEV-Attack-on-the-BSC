from loguru import logger
import math
from ..config import Config
from ..evm import EVM
from ..types import Transaction, Path, SwapEvent
from ..apis.contract import get_token_price, get_pool_price, get_reserve_by_pool_address
from ..utils import eq_address, sort_reserve, find_value_by_address_key
from ..formula import get_uniswa_v2_amount_out


class SimulationIterator:
    def __init__(
            self,
            amount_in,
            max_amount_in,
            break_count_if_zero=20,
            max_count=100,
            to_right=True,
            alpha=1,
            warmup=0,
            gamma=0.05,
    ):
        self.amount_in = amount_in

        self.max_amount_in = max_amount_in
        self.break_count_if_zero = break_count_if_zero
        self.max_count = max_count
        self.to_right = to_right
        self.alpha = alpha
        self.warmup = warmup
        self.gamma = gamma
        self.count = 0

        self.maximized_revenue = 0
        self.before_revenue = 0
        self.before_amount_in = 0

        self.revenue = 0

        self.first = True

    def __next__(self):
        if self.first:
            self.first = False
            self.count += 1
            return self.amount_in

        if (
                self.count >= self.break_count_if_zero and self.maximized_revenue == 0
        ) or self.count >= self.max_count:
            raise StopIteration
        self.count += 1
        if self.before_revenue < self.revenue:
            if self.to_right:
                self.alpha *= 1.0 + self.gamma
            else:
                self.to_right = True
                self.alpha = 1.0 + self.gamma
                if self.warmup > 3:
                    self.gamma *= 0.5
                else:
                    self.warmup += 1
        else:
            if not self.to_right:
                self.alpha *= 1.0 - self.gamma
            else:
                self.to_right = False
                self.alpha = 1.0 - self.gamma
                if self.warmup > 3:
                    self.gamma *= 0.5
                else:
                    self.warmup += 1

        self.before_revenue = self.revenue
        if self.before_amount_in == self.amount_in:  # Max amount in twice
            raise StopIteration
        # if self.maximized_revenue > 0 and self.revenue == 0:
        #    raise StopIteration
        self.before_amount_in = self.amount_in
        self.amount_in *= self.alpha
        self.amount_in = min(int(self.amount_in), self.max_amount_in)
        return self.amount_in

    def __iter__(self):
        return self


def simulate_sandwich(
        cfg: Config,
        evm: EVM,
        victim_tx: Transaction,
        path: Path,
        amount_in,
        maximum_rates
) -> (int, int, int):
    back_run_amount = 0
    front_run_gas_used = 0
    back_run_gas_used = 0
    evm.revert()
    balance_of_contract = evm.balance_of_contract(path.token_addresses[0])
    simulation_iterator = SimulationIterator(
        amount_in=amount_in if amount_in > 0 else balance_of_contract,
        max_amount_in=balance_of_contract
    )

    maximized_amount_in = 0
    maximized_back_run_amount_in = 0
    maximized_revenue = 0
    maximized_front_run_gas_used = 0
    maximized_back_run_gas_used = 0

    swap_event = None
    for event in victim_tx.swap_events:
        if eq_address(event.address, path.pool_addresses[-1]):
            swap_event = event
            break

    if swap_event is None:
        return 0, 0, 0, 0, 0

    for i, amount_in in enumerate(simulation_iterator):
        evm.revert()
        try:
            back_run_before_amount = evm.balance_of(evm.contract_address, path.token_addresses[-1])

            before_balance_of_pool = []
            for idx, pool_address in enumerate(path.pool_addresses):
                before_balance_of_pool.append(
                    evm.balance_of(pool_address, path.token_addresses[idx + 1])
                )
            evm.call_sandwich_front_run(amount_in, path.exchanges, path.pool_addresses,
                                        path.token_addresses)
            front_run_gas_used = evm.latest_gas_used
            for idx, pool_address in enumerate(path.pool_addresses):
                after_balance_of_pool = evm.balance_of(pool_address, path.token_addresses[idx + 1])
                if after_balance_of_pool / before_balance_of_pool[idx] < maximum_rates[idx]:
                    raise Exception("Invalid rate")

            evm.message_call_from_tx(victim_tx)

            if eq_address(path.token_addresses[0],path.token_addresses[-1]):
                back_run_amount_in = (evm.balance_of(evm.contract_address, path.token_addresses[-1]) +
                                   amount_in) - back_run_before_amount
            else:
                back_run_amount_in = evm.balance_of(evm.contract_address, path.token_addresses[-1]) - back_run_before_amount
            evm.call_sandwich_back_run(back_run_amount_in, path.exchanges, path.pool_addresses,
                                       path.token_addresses)
            back_run_gas_used = evm.latest_gas_used
            revenue = evm.balance_of_contract(path.token_addresses[0]) - balance_of_contract
        except Exception as e:
            back_run_amount_in = 0
            revenue = 0

        simulation_iterator.revenue = revenue
        if revenue > maximized_revenue:
            maximized_amount_in = amount_in
            maximized_back_run_amount_in = back_run_amount_in
            maximized_revenue = revenue
            maximized_front_run_gas_used = front_run_gas_used
            maximized_back_run_gas_used = back_run_gas_used
            simulation_iterator.maximized_revenue = revenue

    if maximized_revenue == 0:
        return 0, 0, 0, 0, 0

    token_price_based_on_eth = get_token_price(
        cfg, cfg.wrapped_native_token_address, path.token_addresses[0]
    )
    revenue_based_on_eth = (
            maximized_revenue * token_price_based_on_eth
    )
    return (maximized_amount_in, maximized_back_run_amount_in,
            maximized_front_run_gas_used,
            maximized_front_run_gas_used, revenue_based_on_eth)


def calculate_uniswap_v2_sandwich(cfg: Config, reserve_by_address, swap_event: SwapEvent,
                                  path: Path,
                                  slippage=0.01, block_number=None):
    if len(path.pool_addresses) == 1:
        reserve0, reserve1 = find_value_by_address_key(path.pool_addresses[0], reserve_by_address)
        token0, token1 = path.token_addresses[0], path.token_addresses[1]
    elif len(path.pool_addresses) == 2:
        reserve0, reserve1 = find_value_by_address_key(path.pool_addresses[1], reserve_by_address)
        token0, token1 = path.token_addresses[1], path.token_addresses[2]
    else:
        raise ValueError(f"Invalid path length, {swap_event, path}")

    reserve_in, reserve_out = sort_reserve(token0, token1, reserve0, reserve1)

    victim_amount_in = swap_event.amount_in
    victim_amount_out = swap_event.amount_out

    victim_minimum_amount_out = math.floor(victim_amount_out * (1 - slippage))
    a = 997000 * victim_minimum_amount_out
    b = (1997000 * reserve_in + 997000 * victim_amount_in) * victim_minimum_amount_out
    c = (1000000 * reserve_in * reserve_in * victim_minimum_amount_out + 997000 * reserve_in *
         victim_amount_in * victim_minimum_amount_out - 997000 * reserve_in * reserve_out * victim_amount_in)
    amount_in = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
    if amount_in < 0:
        return 0, 0

    amount_out = get_uniswa_v2_amount_out(amount_in, reserve_in, reserve_out)
    reserve_in += amount_in
    reserve_out -= amount_out

    victim_amount_out = get_uniswa_v2_amount_out(victim_amount_in, reserve_in, reserve_out)
    reserve_in += victim_amount_in
    reserve_out -= victim_amount_out

    amount_out = get_uniswa_v2_amount_out(amount_out, reserve_out, reserve_in)
    if len(path.pool_addresses) == 2:
        assert eq_address(path.token_addresses[1], swap_event.token_in)
        assert eq_address(path.token_addresses[2], swap_event.token_out)
        reserve0, reserve1 = get_reserve_by_pool_address(cfg.http_endpoint,
                                                         [path.pool_addresses[0]],
                                                         block_number)[path.pool_addresses[0]]
        reserve_in, reserve_out = sort_reserve(path.token_addresses[1],
                                               path.token_addresses[0], reserve0, reserve1)
        amount_in_ = get_uniswa_v2_amount_out(amount_in, reserve_in, reserve_out)
        reserve_in -= amount_in
        reserve_out += amount_in_
        amount_out_ = get_uniswa_v2_amount_out(amount_out, reserve_in, reserve_out)
    else:
        amount_in_ = amount_in
        amount_out_ = amount_out
    return math.floor(amount_in_), math.floor(max(amount_out_ - amount_in_, 0))
