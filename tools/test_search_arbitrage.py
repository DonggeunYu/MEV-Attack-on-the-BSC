import asyncio
from src.arbitrage.search import search_arbitrage
from src.apis.trace_tx import trace_transaction_for_debug

async def main():
    from src.config import bsc_local_to_gcp_config

    bsc_local_to_gcp_config.contract_address = None
    block_number = 39107612 - 1
    tx = trace_transaction_for_debug(
        bsc_local_to_gcp_config,
        "0x75399f9492243711d33fc5348924af86a474465ef57d5f2e24a4b2475873c0f3",
    )
    print(tx.__dict__)
    for swap_event in tx.swap_events:
        print(swap_event)
    arbitrage_attack = search_arbitrage(
        bsc_local_to_gcp_config, tx, hex(block_number)
    )
    print(arbitrage_attack)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
