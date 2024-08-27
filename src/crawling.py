import json
import aiohttp
from typing import Dict, List
from loguru import logger
from bs4 import BeautifulSoup
from .config import CoinMarketCapConfig


async def get_pool_list_from_coinmarketcap(
    coin_market_cap_config=CoinMarketCapConfig,
) -> Dict[str, List[str]]:
    url = coin_market_cap_config.url

    pool_addresses = {}
    logger.info("Getting pool list from coinmarketcap")
    async with aiohttp.ClientSession() as session:
        for key, swap in coin_market_cap_config.dex_query_map.items():
            logger.info(f"Swap: {swap}")
            pool_addresses[key] = []
            index = 1
            end = False
            while True:
                joined_url = url + str(index) + "&swap=" + swap
                async with session.get(joined_url) as response:
                    soup = BeautifulSoup(await response.read(), "html.parser")
                    data = soup.find("script", type="application/json").text
                    data = json.loads(data)

                    rows = data["props"]["pageProps"]["dehydratedState"]["queries"][0][
                        "state"
                    ]["data"]["pageList"]

                    if len(rows) == 0:
                        logger.info(
                            f"No more data, stop crawling. index: {index}, count: "
                            f"{len(pool_addresses[key])}"
                        )
                        break

                    for row in rows:
                        if int(row["txns24h"]) < coin_market_cap_config.min_txns24h:
                            logger.info(
                                f"txns24h < {coin_market_cap_config.min_txns24h}, stop crawling. "
                                f"index: {index}, count: {len(pool_addresses[key])}"
                            )
                            end = True
                            break
                        row["pairContractAddress"] = row["pairContractAddress"][:42]
                        pool_addresses[key].append(row["pairContractAddress"])
                        """
                        logger.debug(
                            f"Index: {index}, Count: {len(pool_addresses)} "
                            f"Token: {row['baseTokenSymbol']}/{row['quotoTokenSymbol']} "
                            f"pairContractAddress: {row['pairContractAddress']}, txns24h: {row['txns24h']}"
                        )
                        """

                    index += 1

                if end:
                    break
    return pool_addresses
