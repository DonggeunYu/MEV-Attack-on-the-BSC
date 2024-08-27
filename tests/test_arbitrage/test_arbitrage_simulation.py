from src.arbitrage.simulation import simulate_arbitrage
from src.config import local_config
from src.evm import EVM
from src.types import Path
from src.apis.trace_tx import trace_transaction


def test_simulate_arbitrage(http_endpoint):
    evm = EVM(
        http_endpoint=http_endpoint,
        account_address=local_config.account_address,
    )
    evm.set(19352304)
    tx_hash = "0x98216aa945b9d9792c1c7f073ac3f4205747b47195b65dc184362c6ce6501a83"
    tx = trace_transaction(http_endpoint, tx_hash)
    path = Path(
        exchanges=[0, 1],
        pool_addresses=[
            "0x769f539486b31ef310125c44d7f405c6d470cd1f",
            "0xd572d276b699947a043c85f8d66ce311cc85e357",
        ],
        token_addresses=[
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "0x1258D60B224c0C5cD888D37bbF31aa5FCFb7e870",
            "0x1258D60B224c0C5cD888D37bbF31aa5FCFb7e870",
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        ],
    )

    amount_in, revenue_based_on_eth = simulate_arbitrage(local_config, evm, tx, path)
    assert amount_in > 2342000000000000000
    assert revenue_based_on_eth > 42490000000000000
