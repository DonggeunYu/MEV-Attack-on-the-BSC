from web3 import Web3
from src.apis.subscribe import Transaction, SwapEvent
from src.evm import EVM
from src.sandwich.simulation import (
    SimulationIterator,
    simulate_sandwich_attack,
    simulate_sandwich_attack_arbitrage,
)
from src.config import local_config


def test_simulation_iterator(http_endpoint, account_address):
    evm = EVM(http_endpoint, account_address)

    evm.set(19459702)

    simulation_iterator = SimulationIterator(
        amount_in=10**18,
        evm=evm,
        max_amount_in=10**19,
        max_count=10,
    )
    for amount_in in simulation_iterator:
        simulation_iterator.maximized_front_run_amount_in = 1
        simulation_iterator.maximized_back_run_amount_in = 2
        simulation_iterator.maximized_revenue = 3
        simulation_iterator.amount_out = 1**18

    assert simulation_iterator.amount_in == 165668175527638144
    assert simulation_iterator.amount_out == 1
    assert simulation_iterator.maximized_front_run_amount_in == 1
    assert simulation_iterator.maximized_back_run_amount_in == 2
    assert simulation_iterator.maximized_revenue == 3
    assert simulation_iterator.count == 10
    assert simulation_iterator.before_revenue == 1
    assert simulation_iterator.before_amount_in == 249718229518098784
    assert simulation_iterator.to_right is False
    assert simulation_iterator.alpha == 0.6634204312890623
    assert simulation_iterator.gamma == 0.05


def test_simulate_sandwich_attack(http_endpoint):
    evm = EVM(http_endpoint, local_config.account_address)
    evm.set(fork_block_number=19459702)
    evm.reset()

    front_run = {
        "exchanges": [1],
        "pool_addresses": ["0xf359492d26764481002ed88bd2acae83ca50b5c9"],
        "token_addresses": [
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "0x467bccd9d29f223bce8043b84e8c8b282827790f",
        ],
    }
    back_run = {
        "exchanges": [1],
        "pool_addresses": [
            "0xf359492d26764481002ed88bd2acae83ca50b5c9",
        ],
        "token_addresses": [
            "0x467bccd9d29f223bce8043b84e8c8b282827790f",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        ],
    }

    w3 = Web3(Web3.HTTPProvider(http_endpoint))
    victim_tx_hash = (
        "0x68a9d6267108817b501a2ac6c899a17967d12842641d27bcb11e90f8fbb49814"
    )
    result = w3.provider.make_request("eth_getTransactionByHash", [victim_tx_hash])
    victim_tx = Transaction(
        int(result["result"]["blockNumber"], 16),
        result["result"]["hash"],
        int(result["result"]["gasPrice"], 16),
        result["result"]["from"],
        result["result"]["to"],
        int(result["result"]["value"], 16),
        result["result"]["input"],
        None,
        None,
    )

    front_run, back_run, revenue_based_on_eth = simulate_sandwich_attack(
        cfg=local_config,
        evm=evm,
        front_run=front_run,
        victim_tx=victim_tx,
        back_run=back_run,
        amount_in=10**18,
    )
    assert front_run == {
        "exchanges": [1],
        "pool_addresses": ["0xf359492d26764481002ed88bd2acae83ca50b5c9"],
        "token_addresses": [
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "0x467bccd9d29f223bce8043b84e8c8b282827790f",
        ],
        "amounts_in": [1908296209552358656],
        "amounts_out": [156415282],
        "stages": [0],
        "preserve_amounts": [0],
    }
    assert back_run == {
        "exchanges": [1],
        "pool_addresses": ["0xf359492d26764481002ed88bd2acae83ca50b5c9"],
        "token_addresses": [
            "0x467bccd9d29f223bce8043b84e8c8b282827790f",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        ],
        "amounts_in": [156415282],
        "amounts_out": [1966320628333281190],
        "stages": [0],
        "preserve_amounts": [1908296209552358656],
    }
    assert revenue_based_on_eth == 58024418780922534


def test_simulate_sandwich_attack_arbitrage(http_endpoint):
    evm = EVM(http_endpoint, local_config.account_address)
    evm.set(fork_block_number=19459702)
    evm.reset()

    front_run = {
        "exchanges": [0],
        "pool_addresses": ["0xf75390b0993f1e28ce5185aaee488cc876462e6e"],
        "token_addresses": [
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "0x8dca0c91d84085df5ac88a1f813f5dc6da855c2a",
        ],
    }
    back_run = {
        "exchanges": [0],
        "pool_addresses": [
            "0xf75390b0993f1e28ce5185aaee488cc876462e6e",
        ],
        "token_addresses": [
            "0x8dca0c91d84085df5ac88a1f813f5dc6da855c2a",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        ],
    }

    w3 = Web3(Web3.HTTPProvider(http_endpoint))
    victim_tx_hash = (
        "0x6a11495878381813e3805782eb37da8906db083e179b71153eacd60d2023d8e5"
    )
    result = w3.provider.make_request("eth_getTransactionByHash", [victim_tx_hash])
    victim_tx = Transaction(
        int(result["result"]["blockNumber"], 16),
        result["result"]["hash"],
        int(result["result"]["gasPrice"], 16),
        result["result"]["from"],
        result["result"]["to"],
        int(result["result"]["value"], 16),
        result["result"]["input"],
        None,
        None,
    )
    victim_swap_event = SwapEvent(
        "UniswapV2", "0xf75390b0993f1e28ce5185aaee488cc876462e6e", 0, 900000000000000000
    )
    victim_swap_event.token0 = "0x8dca0c91d84085df5ac88a1f813f5dc6da855c2a"
    victim_swap_event.token1 = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    victim_swap_event_path = [victim_swap_event]

    front_run, back_run, revenue_based_on_eth = simulate_sandwich_attack(
        cfg=local_config,
        evm=evm,
        front_run=front_run,
        victim_tx=victim_tx,
        back_run=back_run,
        amount_in=10**18,
    )
    front_run, back_run, temp = simulate_sandwich_attack_arbitrage(
        cfg=local_config,
        evm=evm,
        front_run=front_run,
        victim_tx=victim_tx,
        back_run=back_run,
        victim_swap_event_path=victim_swap_event_path,
    )
    revenue_based_on_eth += temp
