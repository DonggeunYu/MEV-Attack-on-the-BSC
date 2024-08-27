from src.utils import get_provider
from src.config import bsc_local_to_gcp_config

abi = [{
      "inputs": [
        {
          "internalType": "address",
          "name": "token",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "deposit",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "owner",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address payable",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "transferOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "token",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "to",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "withdraw",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
    ]

w3 = get_provider("https://nd-616-829-754.p2pify.com/9e71f21781b22b259103e4a7c0cf2b74")
contract = w3.eth.contract(address=bsc_local_to_gcp_config.contract_address, abi=abi)

account_address = bsc_local_to_gcp_config.account_address
nonce = w3.eth.get_transaction_count(account_address)

run_function = contract.functions.deposit(bsc_local_to_gcp_config.wrapped_native_token_address,
                                          10 ** 10)
run_tx = run_function.build_transaction(
        {
            "nonce": nonce,
            "from": account_address,
            "gas": 56496 * 2,
            "gasPrice": 10 ** 9,
            "value": 0
        }
    )
signed_run_tx = w3.eth.account.sign_transaction(run_tx,
                                               bsc_local_to_gcp_config.account_private_key)

w3.eth.send_raw_transaction(signed_run_tx.rawTransaction)

run_function = contract.functions.withdraw(bsc_local_to_gcp_config.wrapped_native_token_address,
                                             account_address,
                                             10 ** 10)
run_tx = run_function.build_transaction(
        {
            "nonce": nonce + 1,
            "from": account_address,
            "gas": 56496 * 2,
            "gasPrice": 10 ** 9,
            "value": 0
        }
    )
signed_run_tx = w3.eth.account.sign_transaction(run_tx,
                                               bsc_local_to_gcp_config.account_private_key)
w3.eth.send_raw_transaction(signed_run_tx.rawTransaction)