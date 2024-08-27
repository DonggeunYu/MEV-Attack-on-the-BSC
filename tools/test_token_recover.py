from src.utils import get_provider
from src.config import bsc_local_to_gcp_config


abi = [
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "amountIn",
          "type": "uint256"
        },
        {
          "internalType": "uint8[]",
          "name": "exchanges",
          "type": "uint8[]"
        },
        {
          "internalType": "address[]",
          "name": "poolAddresses",
          "type": "address[]"
        },
        {
          "internalType": "address[]",
          "name": "tokenAddresses",
          "type": "address[]"
        }
      ],
      "name": "sandwichFrontRun",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    ]


w3 = get_provider("https://nd-616-829-754.p2pify.com/9e71f21781b22b259103e4a7c0cf2b74")
contract = w3.eth.contract(address=bsc_local_to_gcp_config.contract_address, abi=abi)

account_address = bsc_local_to_gcp_config.account_address
nonce = w3.eth.get_transaction_count(account_address)

pool_address = ["d4eb4718d4ca70d538ec2cf9b4a1a9f49c3fd6ad"]
pool_address = [w3.to_checksum_address(pool) for pool in pool_address]
token_address = ["7ddc52c4de30e94be3a6a0a2b259b2850f421989", "bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"]
token_address = [w3.to_checksum_address(token) for token in token_address]
run_function = contract.functions.sandwichFrontRun(1259024014293135215568, [11], pool_address,
                                                   token_address)
tx = run_function.build_transaction({
    "nonce": nonce,
    "from": account_address,
    "gas": 2000000,
    "gasPrice": 1000000000
})

signed_tx = w3.eth.account.sign_transaction(tx, private_key=bsc_local_to_gcp_config.account_private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)