import asyncio
from src.sandwich.search import search_sandwich
from src.apis.trace_tx import trace_transaction_for_debug
from src.types import DexInfos, DexInfo, PoolInfo


async def main():
    from src.config import bsc_local_to_gcp_config
    #bsc_local_to_gcp_config.contract_address = None
    #bsc_local_to_gcp_config.http_endpoint = 'http://75.101.172.157:8545'
    block_number = 	39187520 - 1
    tx = trace_transaction_for_debug(
        bsc_local_to_gcp_config,
        "0xdb1114b196c06a774cbc4d5b51daa91eef56c996ef5bf7649b64fba9c886b369",
    )
    print(tx.__dict__)

    #bsc_local_to_gcp_config.http_endpoint = 'http://75.101.172.157:8545'
    dex_info_v3 = DexInfo(
        "UNISWAP_V3",
        [
            PoolInfo(
                "PANCAKESWAP_V3",
                "0x172fcd41e0913e95784454622d1c3724f546f849",
                (
                    "0x55d398326f99059fF775485246999027B3197955",
                    "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                ),
            ),
            PoolInfo(
                "UNISWAP_V3",
                "0x36696169c63e42cd08ce11f5deebbcebae652050",
                (
                    "0x55d398326f99059fF775485246999027B3197955",
                    "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                ),
            ),
        ],
    )
    dex_info_v2 = DexInfo(
        "UNISWAP_V2",
        [
            PoolInfo(
                "UNISWAP_V2",
                "0x2a529766847129f8cc13cebc6b7dfe89ee49d55c",
                (
                    "0x8E6cd950Ad6ba651F6DD608Dc70e5886B1AA6B24",
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                ),
            ),
            PoolInfo(
                "UNISWAP_V2",
                "0xa5e9c917b4b821e4e0a5bbefce078ab6540d6b5e",
                (
                    "0x8E6cd950Ad6ba651F6DD608Dc70e5886B1AA6B24",
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                ),
            ),
        ],
    )

    sandwich_attack, arbitrage_attack, _ = search_sandwich(
        bsc_local_to_gcp_config, tx, hex(block_number)
    )
    print(sandwich_attack)
    print(arbitrage_attack)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
