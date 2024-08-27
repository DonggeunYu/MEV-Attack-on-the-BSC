import asyncio
from web3 import Web3
from src.apis.transaction import send_recover_sandwich_attack
from src.types import SandwichAttack
from src.apis.simple import get_block_number

async def main():
    from src.config import bsc_local_to_gcp_config
    bsc_local_to_gcp_config.http_endpoint = "https://bsc.rpc.blxrbdn.com"
    sandwich = SandwichAttack(front_run_data=[],
    front_run_function_name="",
    front_run_gas_used=0,
    back_run_function_name="sandwichBackRun",
                              back_run_data=[274366490423747179346763, [0],
                                             [Web3.to_checksum_address(
                                                 '0x58ceF3eeDB9A4adc6B5a2Ee5c85Aea07D72787f0')],
                                             [Web3.to_checksum_address(
                                                 '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'),
                                              Web3.to_checksum_address(
                                                  '0xe369fec23380f9F14ffD07a1DC4b7c1a9fdD81c9')],
                                             ],
                              back_run_gas_used=10 ** 6,
                              revenue_based_on_eth=0)
    await send_recover_sandwich_attack(bsc_local_to_gcp_config, sandwich)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())