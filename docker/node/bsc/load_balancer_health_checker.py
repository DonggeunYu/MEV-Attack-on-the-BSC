import json
from flask import Flask, Response
from web3 import Web3

app = Flask(__name__)

local_node_url = "http://localhost:8545"

public_node_url = (
    "https://bsc-mainnet.core.chainstack.com/8b86535e4243bdf9a37eea574a6f3ae3"
)


def get_eth_syncing():
    try:
        web3 = Web3(Web3.HTTPProvider(local_node_url))
        syncing = web3.eth.syncing
        return syncing
    except Exception as e:
        print(f"Error getting syncing status: {e}")
        return None


def compare_blocks():
    try:
        web3_local = Web3(Web3.HTTPProvider(local_node_url))
        local_block_number = web3_local.eth.block_number

        web3_public = Web3(Web3.HTTPProvider(public_node_url))
        public_block_number = web3_public.eth.block_number

        if public_block_number - 2 <= local_block_number <= public_block_number + 2:
            return True, local_block_number, public_block_number
        else:
            return False, local_block_number, public_block_number
    except Exception as e:
        return f"Error comparing blocks: {e}"


@app.route("/", methods=["GET"])
def check_sync():
    syncing = get_eth_syncing()
    if not syncing:
        status, local_block_number, public_block_number = compare_blocks()
        if status:
            return Response(
                f"Node is synced. Local block number: {local_block_number}, Public block number: {public_block_number}",
                status=200,
            )
        else:
            return Response(
                f"Node is not synced. Local block number: {local_block_number}, Public block number: {public_block_number}",
                status=500,
            )
    else:
        syncing_str = json.dumps(dict(syncing))
        return Response(f"Node is syncing. Syncing status: {syncing_str}", status=500)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8544)
