from ..config import Config
from ..evm import EVM
from ..types import Transaction, Path
from ..apis.contract import get_token_price
from ..utils import eq_address

class SimulationIterator:
    def __init__(
        self,
        amount_in,
        max_amount_in,
        break_count_if_zero=20,
        max_count=30,
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
        self.maximized_amount_in = 0

        self.front_run_amount_in = 0
        self.back_run_amount_in = 0
        self.amount_out = 0

        self.first = True

    def __next__(self):
        if self.first:
            self.first = False
            self.count += 1
            return self.amount_in

        if self.amount_out > self.maximized_revenue:
            self.maximized_amount_in = self.amount_in
            self.maximized_revenue = self.amount_out

        if (
            self.count >= self.break_count_if_zero and self.maximized_revenue == 0
        ) or self.count >= self.max_count:
            raise StopIteration
        self.count += 1
        if self.before_revenue < self.amount_out:
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

        self.before_revenue = self.amount_out
        if self.before_amount_in == self.amount_in:  # Max amount in twice
            raise StopIteration
        if self.maximized_revenue > 0 and self.amount_out == 0:
            raise StopIteration
        self.before_amount_in = self.amount_in
        self.amount_in *= self.alpha
        self.amount_in = min(int(self.amount_in), self.max_amount_in)
        return self.amount_in

    def __iter__(self):
        return self


def simulate_arbitrage(
    cfg: Config,
    evm: EVM,
    victim_tx: Transaction,
    path: Path,
) -> (int, int):
    # Check possibility of arbitrage
    evm.revert()
    try:
        evm.message_call_from_tx(victim_tx)

        if eq_address(victim_tx.receiver, evm.contract_address):
            evm.put_balance(victim_tx.swap_events[0].amount_in)

        base_balance = evm.balance_of_contract(path.token_addresses[0])

        evm.send_arbitrage(
            10 ** 14, path.exchanges, path.pool_addresses, path.token_addresses
        )
    except Exception as e:
        from loguru import logger
        logger.info(f"No possibility of arbitrage: tx_hash={victim_tx.tx_hash}")
        logger.error(f"Error simulating arbitrage: tx_hash={victim_tx.tx_hash}")
        #logger.error(f"Error simulating arbitrage: amount_in={amount_in}")
        logger.error(f"Error simulating arbitrage: path={path}")
        logger.error(f"Error simulating arbitrage: {e}")
        return 0, 0, 0
    amount_in = path.amount_in if path.amount_in else base_balance

    simulation_iterator = SimulationIterator(
        amount_in=amount_in,
        max_amount_in=amount_in * 50,
    )
    maximized_gas_used = 0
    for amount_in in simulation_iterator:
        evm.revert()
        try:
            evm.message_call_from_tx(victim_tx)
            if eq_address(victim_tx.receiver, evm.contract_address):
                evm.put_balance(victim_tx.swap_events[0].amount_in)
            evm.send_arbitrage(
                amount_in=amount_in,
                exchanges=path.exchanges,
                pool_addresses=path.pool_addresses,
                token_addresses=path.token_addresses
            )
            gas_used = evm.latest_gas_used
            amount_out = evm.balance_of_contract(path.token_addresses[-1]) - base_balance
        except Exception:
            amount_out = 0
            gas_used = 0
        simulation_iterator.amount_out = amount_out

        if amount_out > simulation_iterator.maximized_revenue:
            maximized_gas_used = gas_used

    if simulation_iterator.maximized_revenue == 0:
        return 0, 0, 0

    token_price_based_on_eth = get_token_price(
        cfg, cfg.wrapped_native_token_address, path.token_addresses[-1]
    )
    revenue_based_on_eth = (
        simulation_iterator.maximized_revenue * token_price_based_on_eth
    )
    return simulation_iterator.maximized_amount_in, revenue_based_on_eth, maximized_gas_used
