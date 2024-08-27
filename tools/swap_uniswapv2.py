from web3 import Web3

tca = Web3.to_checksum_address

http_endpoint = "http://localhost:8545"
provider = Web3(Web3.HTTPProvider(http_endpoint))
print(provider.eth.blockNumber)

pool_address = tca("0x43bec83553828f02a4a20baa536917f709866322")
token0 = tca("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")
token1 = tca("0x19efa7d0fc88ffe461d1091f8cbe56dc2708a84f")

uniswap_v2_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
]
uniswap_v2_contract = provider.eth.contract(address=pool_address, abi=uniswap_v2_abi)
reserves = uniswap_v2_contract.functions.getReserves().call()
print(reserves)

uniswap_v2_router_abi = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactTokensForTokensSupportingFeeOnTransferTokens",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

uniswap_v2_router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

uniswap_v2_router = provider.eth.contract(
    address=uniswap_v2_router_address, abi=uniswap_v2_router_abi
)
amount_in = 10**18
account_address = tca("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
account_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
nonce = provider.eth.getTransactionCount(account_address)

token_abi = [
    {
        "constant": False,
        "inputs": [
            {"name": "guy", "type": "address"},
            {"name": "wad", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]
token0_contract = provider.eth.contract(address=token0, abi=token_abi)
tx = token0_contract.functions.approve(
    uniswap_v2_router_address, amount_in + 1300000000000000000
).buildTransaction(
    {
        "nonce": nonce,
        "from": account_address,
        "maxFeePerGas": 100000000000,
        "gas": 2500000,
    }
)
signed_tx = provider.eth.account.sign_transaction(tx, account_key)
tx_hash = provider.eth.sendRawTransaction(signed_tx.rawTransaction)
print(tx_hash)
provider.eth.waitForTransactionReceipt(tx_hash)

nonce = provider.eth.getTransactionCount(account_address)
tx = uniswap_v2_router.functions.swapExactTokensForTokens(
    amount_in, 0, [token0, token1], account_address, 999999999999999
).buildTransaction(
    {
        "nonce": nonce,
        "from": account_address,
        "maxFeePerGas": 100000000000,
        "gas": 2500000,
    }
)
signed_tx = provider.eth.account.sign_transaction(tx, account_key)
tx_hash = provider.eth.sendRawTransaction(signed_tx.rawTransaction)
print(tx_hash)
provider.eth.waitForTransactionReceipt(tx_hash)

token1_contract = provider.eth.contract(address=token1, abi=token_abi)
print(token1_contract.functions.balanceOf(account_address).call())
"""
print(uniswap_v2_contract.functions.getReserves().call())

amount_in = 800000000000000000
nonce = provider.eth.getTransactionCount(account_address)
tx = uniswap_v2_router.functions.swapExactTokensForTokens(
    amount_in, 0, [token0, token1], account_address, 999999999999999).buildTransaction(
    {"nonce": nonce, "from": account_address, "maxFeePerGas": 100000000000, "gas": 2500000})
signed_tx = provider.eth.account.sign_transaction(tx, account_key)
tx_hash = provider.eth.sendRawTransaction(signed_tx.rawTransaction)
print(tx_hash)
provider.eth.waitForTransactionReceipt(tx_hash)

token1_contract = provider.eth.contract(address=token1, abi=token_abi)
print(token1_contract.functions.balanceOf(account_address).call())

nonce = provider.eth.getTransactionCount(account_address)
tx = token1_contract.functions.approve(uniswap_v2_router_address, 374211903639104145503913).buildTransaction(
    {"nonce": nonce, "from": account_address, "maxFeePerGas": 100000000000, "gas": 2500000})
signed_tx = provider.eth.account.sign_transaction(tx, account_key)
tx_hash = provider.eth.sendRawTransaction(signed_tx.rawTransaction)
print(tx_hash)

print(uniswap_v2_contract.functions.getReserves().call())
print(token1_contract.functions.balanceOf(account_address).call())
print(token0_contract.functions.balanceOf(account_address).call())
amount_in = 361271310063823594720303
nonce = provider.eth.getTransactionCount(account_address)
tx = uniswap_v2_router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
    amount_in, 1000000000000, [token1, token0], account_address, 999999999999999).buildTransaction(
    {"nonce": nonce, "from": account_address, "maxFeePerGas": 100000000000, "gas": 2500000})
signed_tx = provider.eth.account.sign_transaction(tx, account_key)
tx_hash = provider.eth.sendRawTransaction(signed_tx.rawTransaction)
print(tx_hash)
provider.eth.waitForTransactionReceipt(tx_hash)
print(token1_contract.functions.balanceOf(account_address).call())
print(token0_contract.functions.balanceOf(account_address).call())
"""
