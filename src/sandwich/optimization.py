from ..evm import EVM
from ..apis.subscribe import Transaction


def _check_only_uniswap_v2(front_run):
    return len(front_run["exchanges"]) == 1 and front_run["exchanges"][0] in [0, 2]


def _check_only_uniswap_v3(front_run):
    return len(front_run["exchanges"]) == 1 and front_run["exchanges"][0] in [1, 3]


def _check_uniswap_v2_and_v3(front_run):
    uniswap_v2_v3_exchanges = [
        [0, 1],
        [0, 3],
        [2, 1],
        [2, 3],
        [1, 0],
        [3, 0],
        [1, 2],
        [3, 2],
    ]
    return (
        len(front_run["exchanges"]) == 2
        and front_run["exchanges"] in uniswap_v2_v3_exchanges
        and front_run["stages"] == [0, 1]
    )


def _optimize_contract(evm: EVM, run):
    if _check_only_uniswap_v2(run):
        front_run_function_name = "optimizedSwapUniswapV2"
        zero_for_one = run["token_addresses"][0] < run["token_addresses"][1]
        front_run_data = [
            run["amounts_in"][0],
            # front_run["amounts_out"][0], # Not use front_run["amounts_out"][0]
            # because it excluded fee
            evm.get_uniswap_v2_amount_out(
                run["amounts_in"][0],
                run["pool_addresses"][0],
                run["token_addresses"][0],
                run["token_addresses"][1],
            ),
            run["pool_addresses"][0],
            run["token_addresses"][0],
            run["token_addresses"][1],
            zero_for_one,
        ]
    elif _check_only_uniswap_v3(run):
        front_run_function_name = "optimizedSwapUniswapV3"
        zero_for_one = run["token_addresses"][0] < run["token_addresses"][1]
        front_run_data = [
            run["amounts_in"][0],
            run["pool_addresses"][0],
            run["token_addresses"][0],
            zero_for_one,
        ]
    elif _check_uniswap_v2_and_v3(run):
        if 0 in run["exchanges"]:
            uniswap_v2_idx = run["exchanges"].index(0)
        else:
            uniswap_v2_idx = run["exchanges"].index(2)
        uniswap_v2_token0_idx = uniswap_v2_idx * 2
        uniswap_v2_token1_idx = uniswap_v2_idx * 2 + 1
        if 1 in run["exchanges"]:
            uniswap_v3_idx = run["exchanges"].index(1)
        else:
            uniswap_v3_idx = run["exchanges"].index(3)
        uniswap_v3_token0_idx = uniswap_v3_idx * 2
        uniswap_v3_token1_idx = uniswap_v3_idx * 2 + 1

        front_run_function_name = "optimizedSwapUniswapV2V3"
        if (
            run["token_addresses"][uniswap_v2_token0_idx]
            < run["token_addresses"][uniswap_v2_token1_idx]
        ):
            uniswap_v2_zero_for_one = True
        else:
            uniswap_v2_zero_for_one = False
        if (
            run["token_addresses"][uniswap_v3_token0_idx]
            < run["token_addresses"][uniswap_v3_token1_idx]
        ):
            uniswap_v3_zero_for_one = True
        else:
            uniswap_v3_zero_for_one = False

        front_run_data = [
            run["amounts_in"][uniswap_v2_idx],
            run["amounts_in"][uniswap_v3_idx],
            evm.get_uniswap_v2_amount_out(
                run["amounts_in"][uniswap_v2_idx],
                run["pool_addresses"][uniswap_v2_idx],
                run["token_addresses"][uniswap_v2_idx * 2],
                run["token_addresses"][uniswap_v2_idx * 2 + 1],
            ),
            run["pool_addresses"][uniswap_v2_idx],
            run["pool_addresses"][uniswap_v3_idx],
            run["token_addresses"][uniswap_v2_idx * 2],
            run["token_addresses"][uniswap_v2_idx * 2 + 1],
            run["token_addresses"][uniswap_v3_idx * 2],
            run["token_addresses"][uniswap_v3_idx * 2 + 1],
            uniswap_v2_zero_for_one,
            uniswap_v3_zero_for_one,
        ]
    else:
        front_run_function_name = "multiHopSwap"
        front_run_data = [
            run["amounts_in"],
            run["stages"],
            run["exchanges"],
            run["pool_addresses"],
            run["token_addresses"],
            run["preserve_amounts"],
        ]

    return front_run_function_name, front_run_data


def _optimize_contract_and_call(evm: EVM, run):
    run_function_name, run_data = _optimize_contract(evm, run)
    if run_function_name == "multiHopSwap":
        try:
            result, front_run_gas_used = evm.send_multi_hop_swap(*run_data)
        except Exception:
            raise Exception("Front Run Failed", run_data)
    else:
        result, front_run_gas_used = evm.send_with_funtion_name(
            run_function_name, run_data
        )

    return run_function_name, run_data, result, front_run_gas_used


def optimize_sandwich_contract(
    evm: EVM, front_run, victim_txs: [Transaction], back_run
):
    evm.reset()

    # FrontRun
    (
        front_run_function_name,
        front_run_data,
        _,
        front_run_gas_used,
    ) = _optimize_contract_and_call(evm, front_run)
    print(front_run_data)

    # Victim Swap
    for victim_tx in victim_txs:
        evm.call_raw_committing_from_tx(victim_tx)

    # Back Run
    (
        back_run_function_name,
        back_run_data,
        _,
        back_run_gas_used,
    ) = _optimize_contract_and_call(evm, back_run)

    return (
        front_run_function_name,
        front_run_data,
        front_run_gas_used,
        back_run_function_name,
        back_run_data,
        back_run_gas_used,
    )
