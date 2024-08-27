import pytest
from src.sandwich.optimization import (
    _check_only_uniswap_v2,
    _check_only_uniswap_v3,
    _check_uniswap_v2_and_v3,
    optimize_sandwich_contract,
)
from src.evm import EVM
from web3 import Web3
from src.apis.subscribe import Transaction


@pytest.mark.parametrize(
    "run, expected",
    [
        (
            {
                "exchanges": [0],
            },
            True,
        ),
        (
            {
                "exchanges": [2],
            },
            True,
        ),
        ({"exchanges": [1]}, False),
        ({"exchanges": [3]}, False),
        ({"exchanges": [0, 1]}, False),
    ],
)
def test__check_only_uniswap_v2(run, expected):
    assert _check_only_uniswap_v2(run) == expected


@pytest.mark.parametrize(
    "run, expected",
    [
        (
            {
                "exchanges": [1],
            },
            True,
        ),
        (
            {
                "exchanges": [3],
            },
            True,
        ),
        ({"exchanges": [0]}, False),
        ({"exchanges": [2]}, False),
        ({"exchanges": [1, 0]}, False),
    ],
)
def test__check_only_uniswap_v3(run, expected):
    assert _check_only_uniswap_v3(run) == expected


@pytest.mark.parametrize(
    "run, expected",
    [
        ({"exchanges": [0, 1], "stages": [0, 1]}, True),
        ({"exchanges": [0, 3], "stages": [0, 1]}, True),
        ({"exchanges": [2, 1], "stages": [0, 1]}, True),
        ({"exchanges": [2, 3], "stages": [0, 1]}, True),
        ({"exchanges": [1, 0], "stages": [0, 1]}, True),
        ({"exchanges": [3, 0], "stages": [0, 1]}, True),
        ({"exchanges": [1, 2], "stages": [0, 1]}, True),
        ({"exchanges": [3, 2], "stages": [0, 1]}, True),
        ({"exchanges": [0, 1], "stages": [0, 0]}, False),
        ({"exchanges": [0, 1], "stages": [1, 1]}, False),
        ({"exchanges": [0, 1], "stages": [1, 0]}, False),
        ({"exchanges": [0, 1], "stages": [0, 2]}, False),
        ({"exchanges": [0, 1], "stages": [2, 1]}, False),
        ({"exchanges": [0, 1], "stages": [2, 2]}, False),
        ({"exchanges": [0, 1], "stages": [1, 2]}, False),
        ({"exchanges": [0, 1], "stages": [2, 0]}, False),
        ({"exchanges": [0, 1], "stages": [0, 1, 2]}, False),
        ({"exchanges": [0, 1], "stages": [0]}, False),
        ({"exchanges": [0, 1], "stages": [1]}, False),
    ],
)
def test__check_uniswap_v2_and_v3(run, expected):
    assert _check_uniswap_v2_and_v3(run) == expected


def optimize_sandwich_contract_test_case():
    test_case = []

    # Uniswap V2
    block_number = 19446903
    victim_tx_hashes = [
        "0x7525dedbc6fcb71f9547c0c76e57fbe588304c4516e3d0c8f1ae4f422c9cfaf7"
    ]
    front_run = {
        "exchanges": [0],
        "pool_addresses": ["0x90c1b108ec75070a503784e44582a1cc0124956f"],
        "token_addresses": [
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "0x71810f6c664bc7bcbd8819fba6b07c70ca9f78ba",
        ],
        "amounts_in": [340682785363448000],
        "amounts_out": [137743444692356],
        "stages": [0],
        "preserve_amounts": [0],
    }
    back_run = {
        "exchanges": [0],
        "pool_addresses": ["0x90c1b108ec75070a503784e44582a1cc0124956f"],
        "token_addresses": [
            "0x71810f6c664bc7bcbd8819fba6b07c70ca9f78ba",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        ],
        "amounts_in": [137743444692356],
        "amounts_out": [412691811212585455],
        "stages": [0],
        "preserve_amounts": [340682785363448000],
    }
    front_run_function_name = "optimizedSwapUniswapV2"
    front_run_data = [
        340682785363448000,
        143482754887870,
        "0x90c1b108ec75070a503784e44582a1cc0124956f",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "0x71810f6c664bc7bcbd8819fba6b07c70ca9f78ba",
        False,
    ]
    front_run_gas_used = 169410
    back_run_function_name = "optimizedSwapUniswapV2"
    back_run_data = [
        137743444692356,
        412691811212585455,
        "0x90c1b108ec75070a503784e44582a1cc0124956f",
        "0x71810f6c664bc7bcbd8819fba6b07c70ca9f78ba",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        True,
    ]
    back_run_gas_used = 234681
    test_case.append(
        (
            block_number,
            victim_tx_hashes,
            front_run,
            back_run,
            front_run_function_name,
            front_run_data,
            front_run_gas_used,
            back_run_function_name,
            back_run_data,
            back_run_gas_used,
        )
    )

    # Uniswap V3
    block_number = 19458754
    victim_tx_hashes = [
        "0xd46fefde4a5153713012bc66acdfbfd8ccf33cfd9dfb57e6a80200523bbc784f"
    ]
    front_run = {
        "exchanges": [1],
        "pool_addresses": ["0x18bbe20f81bdcb340325e28a6ee6bb426b7ccbc1"],
        "token_addresses": [
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "0x8248270620Aa532E4d64316017bE5E873E37cc09",
        ],
        "amounts_in": [482999996199731200],
        "amounts_out": [1202846783209715921911],
        "stages": [0],
        "preserve_amounts": [0],
    }
    back_run = {
        "exchanges": [1],
        "pool_addresses": ["0x18bbe20f81bdcb340325e28a6ee6bb426b7ccbc1"],
        "token_addresses": [
            "0x8248270620Aa532E4d64316017bE5E873E37cc09",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        ],
        "amounts_in": [1202846783209715921911],
        "amounts_out": [487048956358950912],
        "stages": [0],
        "preserve_amounts": [482999996199731200],
    }
    front_run_function_name = "optimizedSwapUniswapV3"
    front_run_data = [
        482999996199731200,
        "0x18bbe20f81bdcb340325e28a6ee6bb426b7ccbc1",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        False,
    ]
    front_run_gas_used = 119333
    back_run_function_name = "optimizedSwapUniswapV3"
    back_run_data = [
        1202846783209715921911,
        "0x18bbe20f81bdcb340325e28a6ee6bb426b7ccbc1",
        "0x8248270620Aa532E4d64316017bE5E873E37cc09",
        True,
    ]
    back_run_gas_used = 95162
    test_case.append(
        (
            block_number,
            victim_tx_hashes,
            front_run,
            back_run,
            front_run_function_name,
            front_run_data,
            front_run_gas_used,
            back_run_function_name,
            back_run_data,
            back_run_gas_used,
        )
    )

    # Uniswap V2, V3
    block_number = 19459702
    victim_tx_hashes = [
        "0x68a9d6267108817b501a2ac6c899a17967d12842641d27bcb11e90f8fbb49814",
        "0x6a11495878381813e3805782eb37da8906db083e179b71153eacd60d2023d8e5",
    ]
    front_run_function_name = "optimizedSwapUniswapV2V3"
    front_run = {
        "amounts_in": [1908296359726353152, 276705550809143488],
        "amounts_out": [156415294, 508660767992680],
        "stages": [0, 1],
        "exchanges": [1, 0],
        "pool_addresses": [
            "0xf359492d26764481002ed88bd2acae83ca50b5c9",
            "0xf75390b0993f1e28ce5185aaee488cc876462e6e",
        ],
        "token_addresses": [
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "0x467bccd9d29f223bce8043b84e8c8b282827790f",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "0x8dca0c91d84085df5ac88a1f813f5dc6da855c2a",
        ],
        "preserve_amounts": [0, 0],
    }
    front_run_data = [
        276705550809143488,
        1908296359726353152,
        535432387360715,
        "0xf75390b0993f1e28ce5185aaee488cc876462e6e",
        "0xf359492d26764481002ed88bd2acae83ca50b5c9",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "0x8dca0c91d84085df5ac88a1f813f5dc6da855c2a",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "0x467bccd9d29f223bce8043b84e8c8b282827790f",
        False,
        False,
    ]
    front_run_gas_used = 237746
    back_run_function_name = "optimizedSwapUniswapV2V3"
    back_run = {
        "amounts_in": [156415294, 508660767992680],
        "amounts_out": [1966320781898278362, 285084145273503873],
        "stages": [0, 1],
        "exchanges": [1, 0],
        "pool_addresses": [
            "0xf359492d26764481002ed88bd2acae83ca50b5c9",
            "0xf75390b0993f1e28ce5185aaee488cc876462e6e",
        ],
        "token_addresses": [
            "0x467bccd9d29f223bce8043b84e8c8b282827790f",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "0x8dca0c91d84085df5ac88a1f813f5dc6da855c2a",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        ],
        "preserve_amounts": [1908296359726353152, 276705550809143488],
    }
    back_run_data = [
        508660767992680,
        156415294,
        285084145273503873,
        "0xf75390b0993f1e28ce5185aaee488cc876462e6e",
        "0xf359492d26764481002ed88bd2acae83ca50b5c9",
        "0x8dca0c91d84085df5ac88a1f813f5dc6da855c2a",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "0x467bccd9d29f223bce8043b84e8c8b282827790f",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        True,
        True,
    ]

    back_run_gas_used = 280795
    test_case.append(
        (
            block_number,
            victim_tx_hashes,
            front_run,
            back_run,
            front_run_function_name,
            front_run_data,
            front_run_gas_used,
            back_run_function_name,
            back_run_data,
            back_run_gas_used,
        )
    )

    return test_case


@pytest.mark.parametrize(
    "block_number, victim_tx_hashes, front_run, back_run, "
    "expected_front_run_function_name, expected_front_run_data, expected_front_run_gas_used, "
    "expected_back_run_function_name, expected_back_run_data, expected_back_run_gas_used",
    optimize_sandwich_contract_test_case(),
)
def test_optimize_sandwich_contract(
    http_endpoint,
    account_address,
    block_number,
    victim_tx_hashes,
    front_run,
    back_run,
    expected_front_run_function_name,
    expected_front_run_data,
    expected_front_run_gas_used,
    expected_back_run_function_name,
    expected_back_run_data,
    expected_back_run_gas_used,
):
    evm = EVM(http_endpoint, account_address)
    evm.set(block_number)

    evm.reset()

    w3 = Web3(Web3.HTTPProvider(http_endpoint))
    victim_txs = []
    for victim_tx_hash in victim_tx_hashes:
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
        victim_txs.append(victim_tx)

    (
        front_run_function_name,
        front_run_data,
        front_run_gas_used,
        back_run_function_name,
        back_run_data,
        back_run_gas_used,
    ) = optimize_sandwich_contract(evm, front_run, victim_txs, back_run)

    assert front_run_function_name == expected_front_run_function_name
    assert front_run_data == expected_front_run_data
    assert front_run_gas_used == expected_front_run_gas_used
    assert back_run_function_name == expected_back_run_function_name
    assert back_run_data == expected_back_run_data
    assert back_run_gas_used == expected_back_run_gas_used
