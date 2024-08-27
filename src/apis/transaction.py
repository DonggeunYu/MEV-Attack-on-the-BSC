import time
import ssl
import json
import websockets
import aiohttp
import asyncio
from loguru import logger
from web3 import Web3
from typing import List
from src.types import SandwichAttack
from .flashbots import generate_header
from eth_account._utils.legacy_transactions import (
    encode_transaction,
    serializable_unsigned_transaction_from_dict,
)
from src.types import ArbitrageAttack, Transaction
from ..config import Config
from ..utils import get_provider

contract_abi = [
    {
        "inputs": [
            {
                "internalType": "uint8",
                "name": "startIdx",
                "type": "uint8"
            },
            {
                "internalType": "uint256",
                "name": "amountIn",
                "type": "uint256"
            },
            {
                "internalType": "uint8[]",
                "name": "exchanges",
                "type": "uint8[]"
            },
            {
                "internalType": "address[]",
                "name": "poolAddresses",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "tokenAddresses",
                "type": "address[]"
            }
        ],
        "name": "multiHopArbitrageWithBloxroute",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint8",
                "name": "startIdx",
                "type": "uint8"
            },
            {
                "internalType": "uint256",
                "name": "amountIn",
                "type": "uint256"
            },
            {
                "internalType": "uint8[]",
                "name": "exchanges",
                "type": "uint8[]"
            },
            {
                "internalType": "address[]",
                "name": "poolAddresses",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "tokenAddresses",
                "type": "address[]"
            }
        ],
        "name": "multiHopArbitrageWithoutRelay",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "amountIn",
                "type": "uint256"
            },
            {
                "internalType": "uint8[]",
                "name": "exchanges",
                "type": "uint8[]"
            },
            {
                "internalType": "address[]",
                "name": "poolAddresses",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "tokenAddresses",
                "type": "address[]"
            }
        ],
        "name": "sandwichBackRunWithBloxroute",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "amountIn",
                "type": "uint256"
            },
            {
                "internalType": "uint8[]",
                "name": "exchanges",
                "type": "uint8[]"
            },
            {
                "internalType": "address[]",
                "name": "poolAddresses",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "tokenAddresses",
                "type": "address[]"
            }
        ],
        "name": "sandwichFrontRun",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "amountIn",
                "type": "uint256"
            },
            {
                "internalType": "uint8[]",
                "name": "exchanges",
                "type": "uint8[]"
            },
            {
                "internalType": "address[]",
                "name": "poolAddresses",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "tokenAddresses",
                "type": "address[]"
            }
        ],
        "name": "sandwichBackRun",
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
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
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
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "amountIn",
                "type": "uint256"
            },
            {
                "internalType": "uint8[]",
                "name": "exchanges",
                "type": "uint8[]"
            },
            {
                "internalType": "address[]",
                "name": "poolAddresses",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "tokenAddresses",
                "type": "address[]"
            },
            {
                "internalType": "uint256",
                "name": "amountOut",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "poolBalance",
                "type": "uint256"
            }
        ],
        "name": "sandwichFrontRunDifficult",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "amountIn",
          "type": "uint256"
        },
        {
          "internalType": "uint8[]",
          "name": "exchanges",
          "type": "uint8[]"
        },
        {
          "internalType": "address[]",
          "name": "poolAddresses",
          "type": "address[]"
        },
        {
          "internalType": "address[]",
          "name": "tokenAddresses",
          "type": "address[]"
        },
        {
          "internalType": "uint256",
          "name": "blockNumber",
          "type": "uint256"
        }
      ],
      "name": "sandwichBackRunDifficult",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
]


def send_arbitrage(
        http_endpoint,
        account_address,
        account_private_key,
        contract_address,
        gas_price: int,
        amount: int,
        amount_flash_swap: int,
        exchanges: List[int],
        pool_addresses: List[str],
        token_addresses: List[str],
        gas: int = 0,
):
    account_address = Web3.to_checksum_address(account_address)
    contract_address = Web3.to_checksum_address(contract_address)
    pool_addresses = [Web3.to_checksum_address(address) for address in pool_addresses]
    token_addresses = [Web3.to_checksum_address(address) for address in token_addresses]
    arbitrage_contract_abi = [
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {
                    "internalType": "uint256",
                    "name": "amountFlashSwap",
                    "type": "uint256",
                },
                {"internalType": "uint8[]", "name": "exchanges", "type": "uint8[]"},
                {
                    "internalType": "address[]",
                    "name": "poolAddresses",
                    "type": "address[]",
                },
                {
                    "internalType": "address[]",
                    "name": "tokenAddresses",
                    "type": "address[]",
                },
            ],
            "name": "arbitrage",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
    ]

    w3 = get_provider(http_endpoint)
    contract = w3.eth.contract(address=contract_address, abi=arbitrage_contract_abi)
    nonce = _get_nonce(http_endpoint, account_address)
    tx = contract.functions.arbitrage(
        amount, amount_flash_swap, exchanges, pool_addresses, token_addresses
    ).build_transaction(
        {
            "nonce": nonce,
            "from": account_address,
            "maxFeePerGas": int(gas_price * 1.5),
            "gas": gas,
        }
    )
    signed_tx = w3.eth.account.sign_transaction(tx, account_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash


def recover_raw_transaction(tx: Transaction):
    """Recover raw transaction for replay.

    Inspired by: https://github.com/ethereum/eth-account/blob/1d26f44f6075d6f283aeaeff879f4508c9a228dc/eth_account/_utils/signing.py#L28-L42
    """
    transaction = {
        "nonce": tx.nonce,
        "gas": tx.gas,
        "to": Web3.to_checksum_address(tx.receiver),
        "value": tx.value
    }
    if tx.chain_id:
        transaction["chainId"] = tx.chain_id
    if tx.gas_price:
        transaction["gasPrice"] = tx.gas_price
    if tx.maxFeePerGas:
        transaction["maxFeePerGas"] = tx.maxFeePerGas
    if tx.maxPriorityFeePerGas:
        transaction["maxPriorityFeePerGas"] = tx.maxPriorityFeePerGas
    if tx.data:
        transaction["data"] = tx.data
    if tx.access_list:
        transaction["accessList"] = tx.access_list

    v = tx.v
    r = tx.r
    s = tx.s

    unsigned_transaction = serializable_unsigned_transaction_from_dict(transaction)
    return "0x" + encode_transaction(unsigned_transaction, vrs=(v, r, s)).hex()


async def send_mev_bundle(cfg: Config, sandwich_attack: SandwichAttack):
    w3 = Web3(Web3.HTTPProvider(cfg.http_endpoint))
    contract = w3.eth.contract(address=cfg.contract_address, abi=contract_abi)  # noqa F841

    nonce = _get_nonce(cfg.http_endpoint, cfg.account_address)

    front_run_function = eval(
        f"contract.functions.{sandwich_attack.front_run_function_name}"
    )
    front_run_tx = front_run_function(
        *(sandwich_attack.front_run_data)
    ).build_transaction(
        {
            "nonce": nonce,
            "from": cfg.account_address,
            "gas": sandwich_attack.front_run_gas_used * 13 // 10,
            "maxFeePerGas": sandwich_attack.next_block_base_fee * 11 // 10,
            "maxPriorityFeePerGas": 0,
        }
    )

    back_run_function = eval(
        f"contract.functions.{sandwich_attack.back_run_function_name}"
    )
    back_run_tx = back_run_function(*sandwich_attack.back_run_data).build_transaction(
        {
            "nonce": nonce + 1,
            "from": cfg.account_address,
            "gas": sandwich_attack.back_run_gas_used * 13 // 10,
            "maxFeePerGas": sandwich_attack.max_fee_per_gas,
            "maxPriorityFeePerGas": sandwich_attack.max_priority_fee_per_gas,
        }
    )

    signed_front_run_tx = w3.eth.account.sign_transaction(
        front_run_tx, cfg.account_private_key
    )
    signed_back_run_tx = w3.eth.account.sign_transaction(
        back_run_tx, cfg.account_private_key
    )

    victims_raw_tx = []
    for tx in sandwich_attack.txs:
        victims_raw_tx.append(recover_raw_transaction(tx))

    async def send_bundle(name, url, header, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=header, json=data) as response:
                if response.status != 200:
                    logger.error(
                        f"Failed to send bundle to {name}: {response.status}: {response.reason}"
                    )
                    return name, None
                response_data = await response.json()
                bundle_hash = response_data["result"]["bundleHash"]
                return name, bundle_hash

    tasks = []

    for name, url in cfg.builder_config.builders.items():
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendBundle",
            "params": [
                {
                    "txs": [signed_front_run_tx.rawTransaction.hex()]
                           + [signed_back_run_tx.rawTransaction.hex()],
                    "blockNumber": hex(sandwich_attack.block_number),
                    "minTimestamp": 0,
                    "maxTimestamp": sandwich_attack.block_timestamp + 120,
                }
            ],
        }
        header = generate_header(cfg, data)
        task = asyncio.create_task(send_bundle(name, url, header, data))
        tasks.append(task)

    # Gather results
    bundle_has_by_builder = {i[0]: i[1] for i in (await asyncio.gather(*tasks))}

    for name, bundle_hash in bundle_has_by_builder.items():
        logger.info(f"Bundle hash for {name}: {bundle_hash}")

    result = {
        "block_number": sandwich_attack.block_number,
        "bundle_has_by_builder": bundle_has_by_builder,
    }

    return result


def _get_nonce(http_endpoint, account_address):
    w3 = get_provider(http_endpoint)
    return w3.eth.get_transaction_count(account_address)


async def send_private_transaction(
        cfg: Config, arbitrage_attack: ArbitrageAttack, block_number, gas_price: int
):
    w3 = Web3(Web3.HTTPProvider(cfg.http_endpoint))
    contract = w3.eth.contract(address=cfg.contract_address, abi=contract_abi)  # noqa F841

    nonce = _get_nonce(cfg.http_endpoint, cfg.account_address)

    run_function = eval(f"contract.functions.{arbitrage_attack.function_name}")
    run_tx = run_function(*(arbitrage_attack.data)).build_transaction(
        {
            "nonce": nonce,
            "from": cfg.account_address,
            "gas": arbitrage_attack.gas_used * 13 // 10,
            "maxFeePerGas": gas_price * 12 // 10,
            "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
        }
    )
    signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)

    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_callBundle",
        "params": [
            {
                "txs": [signed_run_tx.rawTransaction.hex()],
                "blockNumber": hex(block_number),
                "stateBlockNumber": "latest",
            }
        ],
    }
    header = generate_header(cfg, data)
    async with aiohttp.ClientSession() as session:
        async with session.post(
                cfg.builder_config.builders["flashbots"], headers=header, json=data
        ) as response:
            if response.status != 200:
                logger.error(
                    f"Failed to send bundle to flashbots: {response.status}: {response.reason}"
                )
                return None
            response_data = await response.json()
            if "result" not in response_data:
                logger.error(f"Failed to send bundle to flashbots: {response_data}")
                return None
            if "error" in response_data["result"]["results"][0]:
                logger.error(
                    f"Failed to send bundle to flashbots: {response_data['result']}"
                )
                return None

    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_sendPrivateTransaction",
        "params": [
            {
                "tx": signed_run_tx.rawTransaction.hex(),
                "maxBlockNumber": hex(block_number + 10),
                "preferences": {"fast": True, "privacy": {"builders": ["default"]}},
            }
        ],
    }
    header = generate_header(cfg, data)
    async with aiohttp.ClientSession() as session:
        async with session.post(
                cfg.builder_config.builders["flashbots"], headers=header, json=data
        ) as response:
            if response.status != 200:
                logger.error(
                    f"Failed to send bundle to default: {response.status}: {response.reason}"
                )
                return None
            response_data = await response.json()
            tx_hash = response_data["result"]
            return tx_hash


async def send_arbitrage_attack_single(cfg: Config, arbitrage_attack: ArbitrageAttack, gas_price:
int):
    w3 = get_provider(cfg.http_endpoint)
    contract = w3.eth.contract(address=cfg.contract_address, abi=contract_abi)  # noqa F841

    nonce = _get_nonce(cfg.http_endpoint, cfg.account_address)

    run_function = eval(f"contract.functions.{arbitrage_attack.function_name}")
    run_tx = run_function(*(arbitrage_attack.data)).build_transaction(
        {
            "nonce": nonce,
            "from": cfg.account_address,
            "gas": arbitrage_attack.gas_used * 2,
            "gasPrice": gas_price,
            "value": 0
        }
    )
    signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)

    raw_tx = signed_run_tx.rawTransaction.hex()

    async with websockets.connect(
            "wss://api.blxrbdn.com/ws",
            extra_headers=[("Authorization", cfg.bloxroute_authorization)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE),
    ) as ws:
        request = json.dumps(
            {
                "id": 1,
                "method": "blxr_tx",
                "params": {
                    "blockchain_network": "BSC-Mainnet",
                    "transaction": raw_tx,
                },
            }
        )
        await ws.send(request)
        response = await ws.recv()
        response = json.loads(response)
        if "error" in response:
            logger.warning(f"Failed to send arbitrage attack: {response}")
            return None
        logger.info(f"Send arbitrage attack: {response}")


async def send_arbitrage_attack(
        cfg: Config, victim: Transaction, arbitrage_attack: ArbitrageAttack, gas_price: int,
        accessible_block_number: int
):
    now = time.time()
    w3 = get_provider(cfg.http_endpoint)
    contract = w3.eth.contract(address=cfg.contract_address, abi=contract_abi)  # noqa F841

    nonce = _get_nonce(cfg.http_endpoint, cfg.account_address)

    run_function = eval(f"contract.functions.{arbitrage_attack.function_name}")
    run_tx = run_function(*(arbitrage_attack.data)).build_transaction(
        {
            "nonce": nonce,
            "from": cfg.account_address,
            "gas": arbitrage_attack.gas_used * 2,
            "gasPrice": gas_price,
            "value": 4 * 10 ** 14
        }
    )
    signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)

    raw_tx = signed_run_tx.rawTransaction.hex()

    raw_victim_tx = recover_raw_transaction(victim)

    async with websockets.connect(
            "wss://mev.api.blxrbdn.com/ws",
            extra_headers=[("Authorization", cfg.bloxroute_authorization)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE),
    ) as ws:
        request = json.dumps(
            {
                "id": 1,
                "method": "blxr_simulate_bundle",
                "params": {
                    "blockchain_network": "BSC-Mainnet",
                    "transaction": [raw_victim_tx, raw_tx],
                    "block_number": hex(accessible_block_number),
                    "state_block_number": "latest",
                    "mev_builders": {"bloxroute": "", "all": ""},
                },
            }
        )
        await ws.send(request)
        response = await ws.recv()
        response = json.loads(response)
        error = sum([1 for i in response["result"]["results"] if
                     "error" in i]) > 0 if "result" in response else False
        if "error" in response or error:
            logger.warning(f"Failed to simulate arbitrage attack: {response}")
            return None
        logger.info(f"Simulated arbitrage attack: {response}")

        request = json.dumps(
            {
                "id": 1,
                "method": "blxr_submit_bundle",
                "params": {
                    "blockchain_network": "BSC-Mainnet",
                    "transaction": [raw_victim_tx, raw_tx],
                    "block_number": hex(accessible_block_number),
                    "mev_builders": {"bloxroute": "", "all": ""},
                },
            }
        )
        await ws.send(request)
        response = await ws.recv()
        response = json.loads(response)
        if "error" in response:
            logger.warning(f"Failed to send arbitrage attack: {response}")
            return None
        tx_hash = response["result"]["bundleHash"]
        logger.info(f"[{time.time() - now:.4f}] Arbitrage attack bundle hash: {tx_hash}")
        logger.info(
            f"Arbitrage attack transaction hash: {signed_run_tx.hash.hex()}"
        )


async def send_sandwich_attack_using_bloxroute(
        cfg: Config, victim: Transaction, sandwich: SandwichAttack,
        accessible_block_number: int, gas_price, bundle_fee
):
    from ..utils import get_provider

    w3 = get_provider(cfg.http_endpoint)
    contract = w3.eth.contract(address=cfg.contract_address, abi=contract_abi)  # noqa F841

    nonce = _get_nonce(cfg.http_endpoint, cfg.account_address)

    run_function = eval(f"contract.functions.{sandwich.front_run_function_name}")
    run_tx = run_function(*(sandwich.front_run_data)).build_transaction(
        {
            "nonce": nonce,
            "from": cfg.account_address,
            "gas": int(sandwich.front_run_gas_used * 1.1),
            "gasPrice": 10 ** 9,
        }
    )
    front_run_signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)

    front_run_raw_tx = front_run_signed_run_tx.rawTransaction.hex()

    run_function = eval(f"contract.functions.{sandwich.back_run_function_name}")
    run_tx = run_function(*(sandwich.back_run_data)).build_transaction(
        {
            "nonce": nonce + 1,
            "from": cfg.account_address,
            "gas": int(sandwich.back_run_gas_used * 1.1),
            "gasPrice": gas_price,
            "value": bundle_fee
        }
    )
    back_run_signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)

    back_run_raw_tx = back_run_signed_run_tx.rawTransaction.hex()

    raw_victim_tx = recover_raw_transaction(victim)

    async with websockets.connect(
            "wss://mev.api.blxrbdn.com/ws",
            extra_headers=[("Authorization", cfg.bloxroute_authorization)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE),
    ) as ws:
        request = json.dumps(
            {
                "id": 1,
                "method": "blxr_simulate_bundle",
                "params": {
                    "blockchain_network": "BSC-Mainnet",
                    "transaction": [front_run_raw_tx, raw_victim_tx, back_run_raw_tx],
                    "block_number": hex(accessible_block_number),
                    "state_block_number": "latest",
                    "timestamp": int(time.time()),
                    "mev_builders": {"bloxroute": "", "all": ""},
                },
            }
        )
        await ws.send(request)
        response = await ws.recv()
        response = json.loads(response)
        error = sum([1 for i in response["result"]["results"] if
                     "error" in i]) > 0 if "result" in response else False
        if "error" in response or error:
            logger.warning(f"Failed to simulate arbitrage attack: {response}")
            return None
        logger.info(f"Simulated arbitrage attack: {response}")

    async with websockets.connect(
            "wss://mev.api.blxrbdn.com/ws",
            extra_headers=[("Authorization", cfg.bloxroute_authorization)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE),
    ) as ws:
        request = json.dumps(
            {
                "id": 1,
                "method": "blxr_submit_bundle",
                "params": {
                    "blockchain_network": "BSC-Mainnet",
                    "transaction": [front_run_raw_tx, raw_victim_tx, back_run_raw_tx],
                    "block_number": hex(accessible_block_number),
                    "mev_builders": {"bloxroute": "", "all": ""},
                },
            }
        )
        await ws.send(request)
        response = await ws.recv()
        response = json.loads(response)
        if "error" in response:
            logger.warning(f"Failed to send arbitrage attack: {response}")
            return None
        tx_hash = response["result"]["bundleHash"]
        logger.info(f"Sandwich attack bundle hash: {tx_hash}")
        logger.info(
            f"Sandwich attack front run transaction hash: {front_run_signed_run_tx.hash.hex()}"
        )
        logger.info(
            f"Sandwich attack back run transaction hash: {back_run_signed_run_tx.hash.hex()}"
        )


async def get_48_club_minimum_gas_price():
    url = "https://puissant-bsc.48.club"
    headers = {
        "Content-Type": "application/json"
    }

    minimum_gas_price = 0
    data = {"method": "eth_gasPrice", "params": [], "id": 1, "jsonrpc": "2.0"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            minimum_gas_price = int((json.loads(await response.text()))["result"], 16)
    return minimum_gas_price


async def send_sandwich_attack_using_48club(
        cfg: Config, victim: Transaction, sandwich: SandwichAttack, gas_price: int):
    url = "https://puissant-bsc.48.club"
    headers = {
        "Content-Type": "application/json"
    }
    w3 = get_provider(cfg.http_endpoint)
    contract = w3.eth.contract(address=cfg.contract_address, abi=contract_abi)  # noqa F841

    nonce = _get_nonce(cfg.http_endpoint, cfg.account_address)

    raw_tx = {
        "from": cfg.account_address,
        "to": cfg.account_address,
        "value": 0,
        "gas": 21000,
        "gasPrice": gas_price,
        "nonce": nonce,
        "chainId": 56,
    }
    signed_tx = w3.eth.account.sign_transaction(raw_tx, cfg.account_private_key)
    garbage_raw_tx = signed_tx.rawTransaction.hex()

    run_function = eval(f"contract.functions.{sandwich.front_run_function_name}")
    run_tx = run_function(*(sandwich.front_run_data)).build_transaction(
        {
            "nonce": nonce + 1,
            "from": cfg.account_address,
            "gas": int(sandwich.front_run_gas_used * 1.5),
            "gasPrice": victim.gas_price + 1
        }
    )
    front_run_signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)

    front_run_raw_tx = front_run_signed_run_tx.rawTransaction.hex()

    run_function = eval(f"contract.functions.{sandwich.back_run_function_name}")
    run_tx = run_function(*(sandwich.back_run_data)).build_transaction(
        {
            "nonce": nonce + 2,
            "from": cfg.account_address,
            "gas": int(sandwich.back_run_gas_used * 1.5),
            "gasPrice": 10 ** 9
        }
    )
    back_run_signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)

    back_run_raw_tx = back_run_signed_run_tx.rawTransaction.hex()

    raw_victim_tx = recover_raw_transaction(victim)

    max_timestamp = int(time.time() + 120)
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_sendPuissant",
        "params": [
            {
                "txs": [garbage_raw_tx, front_run_raw_tx, raw_victim_tx, back_run_raw_tx],
                "maxTimestamp": max_timestamp
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            result = json.loads(await response.text())

        if "result" in result:
            logger.info(f"Sandwich attack bundle hash: {result['result']}")
            logger.info(
                f"Sandwich attack front run transaction hash: {front_run_signed_run_tx.hash.hex()}"
            )
            logger.info(
                f"Sandwich attack back run transaction hash: {back_run_signed_run_tx.hash.hex()}"
            )
        else:
            logger.error(f"Failed to send sandwich attack: {result}")


async def send_sandwich_attack_using_general(
        cfg: Config, victim: Transaction, sandwich: SandwichAttack, front_run_gas_price):
    w3 = get_provider(cfg.http_endpoint)
    contract = w3.eth.contract(address=cfg.contract_address, abi=contract_abi)  # noqa F841

    nonce = _get_nonce(cfg.http_endpoint, cfg.account_address)

    run_function = eval(f"contract.functions.{sandwich.front_run_function_name}")
    run_tx = run_function(*(sandwich.front_run_data)).build_transaction(
        {
            "nonce": nonce,
            "from": cfg.account_address,
            "gas": int(sandwich.front_run_gas_used * 1.5),
            "gasPrice": front_run_gas_price
        }
    )
    front_run_signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)
    w3.eth.send_raw_transaction(front_run_signed_run_tx.rawTransaction)

    run_function = eval(f"contract.functions.{sandwich.back_run_function_name}")
    run_tx = run_function(*(sandwich.back_run_data)).build_transaction(
        {
            "nonce": nonce + 1,
            "from": cfg.account_address,
            "gas": int(sandwich.back_run_gas_used * 2),
            "gasPrice": victim.gas_price
        }
    )
    back_run_signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)
    w3.eth.send_raw_transaction(back_run_signed_run_tx.rawTransaction)
    logger.info(f"Sandwich attack front run transaction hash: {front_run_signed_run_tx.hash.hex()}")
    logger.info(f"Sandwich attack back run transaction hash: {back_run_signed_run_tx.hash.hex()}")

    return front_run_signed_run_tx.hash.hex(), back_run_signed_run_tx.hash.hex()


async def send_recover_sandwich_attack(
        cfg: Config, sandwich: SandwichAttack):
    w3 = get_provider("https://bsc.rpc.blxrbdn.com")
    contract = w3.eth.contract(address=cfg.contract_address, abi=contract_abi)  # noqa F841

    nonce = _get_nonce(cfg.http_endpoint, cfg.account_address)

    run_function = eval(f"contract.functions.{sandwich.back_run_function_name}")
    run_tx = run_function(*(sandwich.back_run_data)).build_transaction(
        {
            "nonce": nonce,
            "from": cfg.account_address,
            "gas": int(sandwich.back_run_gas_used * 2),
            "gasPrice": 10 ** 9
        }
    )
    back_run_signed_run_tx = w3.eth.account.sign_transaction(run_tx, cfg.account_private_key)
    w3.eth.send_raw_transaction(back_run_signed_run_tx.rawTransaction)
    logger.info(f"Sandwich attack back run transaction hash: {back_run_signed_run_tx.hash.hex()}")

    return back_run_signed_run_tx.hash.hex()