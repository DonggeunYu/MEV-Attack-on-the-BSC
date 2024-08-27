import pytest
from src.evm import EVM


@pytest.fixture(scope="session", autouse=True)
def evm(http_endpoint):
    fake_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # vitalik.eth
    return EVM(http_endpoint, fake_address)


@pytest.mark.dependency()
def test_deploy_contract(evm):
    evm.reset(19419205)

    assert isinstance(evm.get_contract_address(), str)


@pytest.mark.dependency(depends=["test_deploy_contract"])
def test_send_multi_hop_swap_front_run(evm):
    token_abi = [
        {
            "constant": True,
            "inputs": [{"name": "", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "dst", "type": "address"},
                {"name": "wad", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        },
    ]

    # Check the WETH holder's balance for transfer to the contract
    weth_holder_address = "0x6b44ba0a126a2a1a8aa6cd1adeed002e141bcd44"
    weth_token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    result, _ = evm.call_function(
        caller=weth_holder_address,
        to=weth_token_address,
        value=0,
        function_name="balanceOf",
        input=[weth_holder_address],
        abi=token_abi,
    )
    assert result[0] > 10**19

    # Transfer 10 WETH to the contract
    result, _ = evm.call_function(
        caller=weth_holder_address,
        to=weth_token_address,
        value=0,
        function_name="transfer",
        input=[evm.get_contract_address(), 10**19],
        abi=token_abi,
        commit=True,
    )
    assert result[0] is not False

    # Call the contract
    contract_output_amount_out, gas_used = evm.send_multi_hop_swap(
        amount_in=10**19,
        exchanges=[1, 0],
        pool_addresses=[
            "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
            "0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5",
        ],
        token_addresses=[
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        ],
        preserve_amount=0,
    )
    assert gas_used > 200000

    # Check the contract's balance
    dai_token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    result, _ = evm.call_function(
        caller=evm.account_address,  # Mock the address
        to=dai_token_address,
        value=0,
        function_name="balanceOf",
        input=[evm.get_contract_address()],
        abi=token_abi,
    )
    assert contract_output_amount_out == result[0]


@pytest.mark.dependency(depends=["test_send_multi_hop_swap_front_run"])
def test_send_multi_hop_swap_back_run(evm):
    token_abi = [
        {
            "constant": True,
            "inputs": [{"name": "", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "dst", "type": "address"},
                {"name": "wad", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        },
    ]

    # Check the WETH holder's balance for transfer to the contract
    weth_token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    result, _ = evm.call_function(
        caller=evm.account_address,
        to=weth_token_address,
        value=0,
        function_name="balanceOf",
        input=[evm.account_address],
        abi=token_abi,
    )
    before_account_weth_balance = result[0]

    # Get the contract's balance
    dai_token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    result, _ = evm.call_function(
        caller=evm.account_address,  # Mock the address
        to=dai_token_address,
        value=0,
        function_name="balanceOf",
        input=[evm.get_contract_address()],
        abi=token_abi,
    )
    contract_dai_balance = result[0]

    # Call the contract
    contract_output_amount_out, gas_used = evm.send_multi_hop_swap(
        amount_in=contract_dai_balance,
        exchanges=[0, 1],
        pool_addresses=[
            "0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5",
            "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        ],
        token_addresses=[
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        ],
        preserve_amount=int(10**19 * 0.95),
    )
    assert contract_output_amount_out > 0
    assert gas_used > 200000

    # Check the WETH holder's balance for transfer to the contract
    weth_token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    result, _ = evm.call_function(
        caller=evm.account_address,
        to=weth_token_address,
        value=0,
        function_name="balanceOf",
        input=[evm.account_address],
        abi=token_abi,
    )
    assert result[0] - before_account_weth_balance == contract_output_amount_out


@pytest.mark.dependency(depends=["test_send_multi_hop_swap_back_run"])
def test_send_multi_hop_swap_back_run_error(evm):
    token_abi = [
        {
            "constant": True,
            "inputs": [{"name": "", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "dst", "type": "address"},
                {"name": "wad", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        },
    ]

    # Check the WETH holder's balance for transfer to the contract
    weth_holder_address = "0x6b44ba0a126a2a1a8aa6cd1adeed002e141bcd44"
    weth_token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    result, _ = evm.call_function(
        caller=weth_holder_address,
        to=weth_token_address,
        value=0,
        function_name="balanceOf",
        input=[weth_holder_address],
        abi=token_abi,
    )
    assert result[0] > 10**19

    # Transfer 10 WETH to the contract
    result, _ = evm.call_function(
        caller=weth_holder_address,
        to=weth_token_address,
        value=0,
        function_name="transfer",
        input=[evm.get_contract_address(), 10**19],
        abi=token_abi,
        commit=True,
    )
    assert result[0] is not False

    # Call the contract
    contract_output_amount_out, gas_used = evm.send_multi_hop_swap(
        amount_in=10**19,
        exchanges=[1, 0],
        pool_addresses=[
            "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
            "0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5",
        ],
        token_addresses=[
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        ],
        preserve_amount=0,
    )
    assert gas_used > 190000

    # Check the contract's balance
    dai_token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    result, _ = evm.call_function(
        caller=evm.account_address,  # Mock the address
        to=dai_token_address,
        value=0,
        function_name="balanceOf",
        input=[evm.get_contract_address()],
        abi=token_abi,
    )
    assert contract_output_amount_out == result[0]

    # Get the contract's balance
    dai_token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    result, _ = evm.call_function(
        caller=evm.account_address,  # Mock the address
        to=dai_token_address,
        value=0,
        function_name="balanceOf",
        input=[evm.get_contract_address()],
        abi=token_abi,
    )
    contract_dai_balance = result[0]

    # Call the contract
    contract_output_amount_out, gas_used = evm.send_multi_hop_swap(
        amount_in=contract_dai_balance,
        exchanges=[0, 1],
        pool_addresses=[
            "0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5",
            "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        ],
        token_addresses=[
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        ],
        preserve_amount=10**19,
    )
    assert contract_output_amount_out == 0  # Test for Error
    assert gas_used > 190000
