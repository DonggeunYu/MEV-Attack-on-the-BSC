from src.apis.simple import get_block_number, get_gas_price


def test_get_block_number(hardhat_node_endpoint):
    block_number = get_block_number(hardhat_node_endpoint)
    assert block_number > 0


def test_get_gas_price(hardhat_node_endpoint):
    gas_price = get_gas_price(hardhat_node_endpoint)
    # 100 Gwei < gas price < 500 Gwei
    assert gas_price > 100 * 10**9
    assert gas_price < 500 * 10**9
