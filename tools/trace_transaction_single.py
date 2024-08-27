from web3 import Web3
from src.apis.trace_tx import trace_transaction_for_debug

TOP_BIT_256BIT_INT = 2**255
BIT_256BIT_INT = 2**256


def hex_to_uint256(hex_str):
    return int(hex_str, 16)


def hex_to_int256(hex_str):
    value = int(hex_str, 16)
    if value >= TOP_BIT_256BIT_INT:
        value -= BIT_256BIT_INT
    return value


# Uniswap V2 and V3 0xb169fb3969b3549e7cf85cc5eee4f715d428a456ad39f387456ce561757502f7
# Uniswap V3 V3 0xea3d2bae4fd7e8c7e76e8da389fb8a9b4f946c1eb27d1db3e8b6d346d047c4ed
tx_hash = "0xf3af49440ddf1a2a868c28d4542c493d52cfdf83779a0bcf8e919769b215caa3"
w3 = Web3(Web3.HTTPProvider("http://34.22.99.244:8545"))
# w3 = Web3(Web3.HTTPProvider(
# "https://eth-mainnet.g.alchemy.com/v2/nYfATDWALLC6aLyyCrweNYFjkBxXSTlM"))
# w3 = Web3(Web3.HTTPProvider("http://34.22.99.244:8545"))


a = trace_transaction_for_debug(
    "https://bsc-mainnet.core.chainstack.com/8b86535e4243bdf9a37eea574a6f3ae3",
    37561318,
    tx_hash,
)
print(a)


# tx hashes from block
"""
for tx_hashes in w3.eth.get_block("latest")["transactions"]:
    print(tx_hashes.hex())
    trace(tx_hashes)
"""

"""
for txs_by_address in w3.geth.txpool.content()["pending"].values():
    for tx in txs_by_address.values():
        print(tx["hash"])
        trace(tx["hash"])
"""
