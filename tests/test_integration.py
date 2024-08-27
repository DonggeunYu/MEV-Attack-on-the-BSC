from web3 import Web3


def check_existence_of_contract(http_endpoint, contract_address):
    w3 = Web3(Web3.HTTPProvider(http_endpoint))
    contract = w3.eth.contract(address=contract_address)
    assert contract.functions is not None


def test_check_arbitrage_contract(hardhat_node_endpoint, arbitrage_contract_address):
    check_existence_of_contract(hardhat_node_endpoint, arbitrage_contract_address)
