from web3 import Web3
from typing import Optional, List
from src.api_utils import subscribe_new_blocks

# get MemPool transactions

TOP_BIT_256BIT_INT = 2**255
BIT_256BIT_INT = 2**256


def hex_to_uint256(hex_str):
    return int(hex_str, 16)


def hex_to_int256(hex_str):
    value = int(hex_str, 16)
    if value >= TOP_BIT_256BIT_INT:
        value -= BIT_256BIT_INT
    return value


class SwapEvent:
    def __init__(self, dex, address, amount0In, amount1In):
        self.dex = dex
        self.address = address
        self.amount0In = amount0In
        self.amount1In = amount1In

    def __str__(self):
        return f"{self.dex} {self.address} {self.amount0In} {self.amount1In}"


class Transaction:
    def __init__(self, tx_hash, swap_events: List[SwapEvent]):
        self.tx_hash = tx_hash
        self.swap_events = swap_events

    def __str__(self):
        text = f"Tx: {self.tx_hash}"
        for event in self.swap_events:
            text += f"\n{event}"
        return text


def trace_transaction(w3: Web3, tx_hash: str) -> Optional[Transaction]:
    trace = w3.provider.make_request("eth_getTransactionReceipt", [tx_hash])
    if trace is None or trace["result"] is None:
        return None

    logs = trace["result"]["logs"]

    swap_events = []
    for log in logs:
        topic = log["topics"][0]
        if (
            topic
            == "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
        ):
            address = log["address"]
            data = log["data"][2:]
            amount0In = hex_to_uint256(data[:64])
            amount1In = hex_to_uint256(data[64:128])
            swap_events.append(SwapEvent("UniswapV2", address, amount0In, amount1In))
        elif (
            topic
            == "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
        ):
            address = log["address"]
            data = log["data"][2:]
            amount0In = max(hex_to_int256(data[:64]), 0)
            amount1In = max(hex_to_int256(data[64:128]), 0)
            swap_events.append(SwapEvent("UniswapV3", address, amount0In, amount1In))

    if swap_events:
        return Transaction(tx_hash, swap_events)
    else:
        return None


async def subscribe_new_blocks_with_pending_txs(http_endpoint: str, ws_endpoint: str):
    w3 = Web3(Web3.HTTPProvider(http_endpoint))
    new_block_sub = subscribe_new_blocks(ws_endpoint)

    async for block in new_block_sub:
        block_number = int(block["params"]["result"]["number"], 16)
        pending_txs = w3.eth.getBlock("pending", full_transactions=True)

        filtered_txs = []
        deadline = block_number - 10
        for tx in pending_txs["transactions"]:
            if tx.blockNumber < deadline:
                continue
            if tx.to is None:
                continue
            if tx.input == "0x":
                continue

            filtered_txs.append(tx)

        print(f"Block: {block_number}, Pending txs: {len(filtered_txs)}")

        # trace
        transactions = []
        for tx in filtered_txs:
            traced_transaction = trace_transaction(w3, tx.hash.hex())
            if traced_transaction is not None:
                transactions.append(traced_transaction)

        yield transactions


async def main():
    subscribe_new_blocks_with_pending_txs_caller = (
        subscribe_new_blocks_with_pending_txs(
            "http://34.22.99.244:8545", "ws://34.22.99.244:8546"
        )
    )

    async for transactions in subscribe_new_blocks_with_pending_txs_caller:
        for transaction in transactions:
            print(transaction)
            print("")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
