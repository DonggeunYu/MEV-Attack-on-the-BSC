from web3 import Web3

w3 = Web3(
    Web3.HTTPProvider(
        "https://eth-sepolia.g.alchemy.com/v2/OJ_kc5aBfDEgXWr1u8ah0LetcRU2oPuP"
    )
)

account_address = "0x2a426E21E6CF0Bfd16965F2a570241bF3d86DD0A"
account_private_key = "49a6c1dab5db7e3b5aca37b1865a427610f84bebec04099e99ad6bc0ea8d7156"
contract_address = "0xD08C91bDF390Dd50796231CB961D0DCec15dB945"
token_address = "0xfff9976782d46cc05630d1f6ebab18b2324d6b14"
amount = 10**18

contract_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenAddress", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "transferFromContract",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

contract = w3.eth.contract(
    address=Web3.to_checksum_address(contract_address), abi=contract_abi
)

# Transfer 1 token from the contract to the account
tx_hash = contract.functions.transferFromContract(
    Web3.to_checksum_address(token_address),
    Web3.to_checksum_address(account_address),
    amount,
).build_transaction(
    {
        "from": Web3.to_checksum_address(account_address),
        "gas": 1000000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(
            Web3.to_checksum_address(account_address)
        ),
    }
)

signed_tx = w3.eth.account.sign_transaction(tx_hash, account_private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
print(tx_hash.hex())
