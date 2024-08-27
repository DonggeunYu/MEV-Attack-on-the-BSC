import asyncio
import json
import websockets
import time
from loguru import logger
import ssl
from web3 import Web3
from src.apis.transaction import recover_raw_transaction
from src.types import Transaction, Path
from src.utils import get_provider
from src.apis.transaction import contract_abi
from tqdm import tqdm

# block num = 37944029
ws = get_provider("https://nd-616-829-754.p2pify.com/9e71f21781b22b259103e4a7c0cf2b74")
local_ws = get_provider("http://localhost:8545")
print(local_ws.eth.block_number)

token_abi = [
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "dst", "type": "address"},
            {"name": "wad", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "name": "approve",
        "outputs": [],
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
        ],
        "constant": False,
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

def get_token_balance(token_address, address):
    token_contract = local_ws.eth.contract(address=token_address, abi=token_abi)
    balance = token_contract.functions.balanceOf(address).call()
    return balance

def transfer_token(caller, recipient, token_address, amount):
    local_ws.provider.make_request('hardhat_impersonateAccount', [caller])

    token_contract = local_ws.eth.contract(address=token_address, abi=token_abi)
    balance = token_contract.functions.balanceOf(caller).call()
    assert balance >= amount, f"Caller has insufficient balance: {balance}"

    nonce = local_ws.eth.get_transaction_count(caller)
    transfer_function = token_contract.functions.transfer(recipient, amount)
    transfer_tx = transfer_function.build_transaction(
        {
            "nonce": nonce,
            "from": caller,
            "gas": 100000,
            "gasPrice": 5 * 10**9,
        }
    )
    local_ws.eth.send_transaction(transfer_tx)

def get_transaction(victim_tx_hash):
    # Run victim transaction
    impersonated_tx = ws.eth.get_transaction(victim_tx_hash)
    #print("impersonated_tx", impersonated_tx)
    local_ws.provider.make_request('hardhat_impersonateAccount', [impersonated_tx['from']])

    # Initialize replay_tx as an empty dictionary
    replay_tx = {}

    # Common fields for both legacy and EIP-1559 transactions
    common_fields = ['from', 'to', 'gas', 'value', 'input', 'nonce', 'type', 'chainId',
                     'accessList', 'data', "r", "s", "v"]

    for field in common_fields:
        if field in impersonated_tx:
            replay_tx[field] = impersonated_tx[field]

    replay_tx["nonce"] = local_ws.eth.get_transaction_count(impersonated_tx["from"])

    # For legacy transactions
    if 'gasPrice' in impersonated_tx:
        replay_tx['gasPrice'] = impersonated_tx['gasPrice']

    if 'maxFeePerGas' in impersonated_tx and 'maxPriorityFeePerGas' in impersonated_tx:
        replay_tx['maxFeePerGas'] = impersonated_tx['maxFeePerGas']
        replay_tx['maxPriorityFeePerGas'] = impersonated_tx['maxPriorityFeePerGas']

    if 'input' in replay_tx:
        replay_tx['data'] = replay_tx.pop('input')

    replay_tx['chainId'] = 56 # need to hardcode for hardhat

    if 'type' in replay_tx and replay_tx['type'] == 2:
        if 'gasPrice' in replay_tx:
            del replay_tx['gasPrice']
    return replay_tx

def send_victim(victim_tx_hash):
    # Run victim transaction
    replay_tx = get_transaction(victim_tx_hash)

    raw = recover_raw_transaction(Transaction(
        tx_hash=victim_tx_hash,
        nonce=replay_tx["nonce"],
        gas_price=replay_tx.get("gasPrice", None),
        gas=replay_tx["gas"],
        caller=replay_tx["from"],
        receiver=replay_tx["to"],
        value=replay_tx["value"],
        data=replay_tx["data"],
        chain_id=replay_tx["chainId"],
        maxFeePerGas=replay_tx.get("maxFeePerGas", None),
        maxPriorityFeePerGas=replay_tx.get("maxPriorityFeePerGas", None),
        access_list=replay_tx.get("accessList", None),
        r=replay_tx.get("r", None).hex(),
        s=replay_tx.get("s", None).hex(),
        v=replay_tx.get("v", None),
        swap_events=[]
    ))
    #print("Vicitm raw: ", raw)
    #print(replay_tx)
    tx_hash = local_ws.eth.send_transaction(replay_tx)

    return tx_hash

def send_sandwich_front_run(contract_address, path):
    from src.apis.transaction import contract_abi
    account_address = "0x007fc398a4d8fEaBcDa8eD17dB92976a7E0Dba00"
    account_private_key = "0x703c4b799f2137ce78e902484f674010d3dca796641bdc1224fd4a85f50404fb"
    contract = local_ws.eth.contract(address=contract_address, abi=contract_abi)
    # noqa F841

    nonce = local_ws.eth.get_transaction_count(account_address)

    gas_used = 239184 * 2
    gas_price = 1 * 10**9
    function_name = "sandwichFrontRun"
    data = [path.amount_in, path.exchanges, path.pool_addresses, path.token_addresses]
    print(data)
    run_function = eval(f"contract.functions.{function_name}")
    run_tx = run_function(*(data)).build_transaction(
            {
                "nonce": nonce,
                "from": account_address,
                "gas": gas_used,
                "gasPrice": gas_price,
            }
        )
    signed_run_tx = local_ws.eth.account.sign_transaction(run_tx, account_private_key)
    print(signed_run_tx.rawTransaction.hex())
    local_ws.eth.send_raw_transaction(signed_run_tx.rawTransaction.hex())

def send_sandwich_back_run(contract_address, path):
    account_address = "0x007fc398a4d8fEaBcDa8eD17dB92976a7E0Dba00"
    account_private_key = "0x703c4b799f2137ce78e902484f674010d3dca796641bdc1224fd4a85f50404fb"
    contract = local_ws.eth.contract(address=contract_address, abi=contract_abi)
    # noqa F841

    nonce = local_ws.eth.get_transaction_count(account_address)

    gas_used = 98278 * 4
    gas_price = 1**9
    function_name = "sandwichBackRun"
    data = [path.amount_in, path.exchanges, path.pool_addresses, path.token_addresses]
    print(data)
    run_function = eval(f"contract.functions.{function_name}")
    run_tx = run_function(*(data)).build_transaction(
            {
                "nonce": nonce + 1,
                "from": account_address,
                "gas": gas_used,
                "gasPrice": gas_price,
                #"value": 137026405166231
            }
        )
    signed_run_tx = local_ws.eth.account.sign_transaction(run_tx, account_private_key)
    print(signed_run_tx.rawTransaction.hex())
    local_ws.eth.send_raw_transaction(signed_run_tx.rawTransaction.hex())

def deposit(caller, contract_address, token_address, amount):
    token_contract = local_ws.eth.contract(address=token_address, abi=token_abi)
    balance = token_contract.functions.balanceOf(caller).call()
    assert balance >= amount, f"Caller has insufficient balance: {balance}"

    token_contract.functions.approve(contract_address, amount).transact({'from': caller})
    contract = local_ws.eth.contract(address=contract_address, abi=contract_abi)
    contract.functions.deposit(token_address, amount).transact({'from': caller})

async def simulate_bundle(victim_tx_hash, block_number, front_run_path: Path, back_run_path: Path):
    replay_tx = get_transaction(victim_tx_hash)

    from src.config import bsc_local_to_gcp_config as cfg

    contract = local_ws.eth.contract(address=cfg.contract_address, abi=contract_abi)

    nonce = local_ws.eth.get_transaction_count(cfg.account_address)
    run_function = eval(f"contract.functions.{'sandwichFrontRun'}")
    run_tx = run_function(*[front_run_path.amount_in, front_run_path.exchanges,
                           front_run_path.pool_addresses, front_run_path.token_addresses]).build_transaction(
        {
            "nonce": nonce - 10,
            "from": cfg.account_address,
            "gas": 100000,
            "gasPrice": 1
        }
    )
    front_run_signed_run_tx = (local_ws.eth.account.sign_transaction(run_tx,
                                                                     cfg.account_private_key))

    front_run_raw_tx = front_run_signed_run_tx.rawTransaction.hex()

    run_function = eval(f"contract.functions.{'sandwichBackRun'}")
    run_tx = run_function(*[back_run_path.amount_in, back_run_path.exchanges,
                            back_run_path.pool_addresses, back_run_path.token_addresses]).build_transaction(
        {
            "nonce": nonce - 9,
            "from": cfg.account_address,
            "gas": 100000,
            "gasPrice": 1,
            #"value": 4 * 10 ** 15
        }
    )
    back_run_signed_run_tx = local_ws.eth.account.sign_transaction(run_tx, cfg.account_private_key)

    back_run_raw_tx = back_run_signed_run_tx.rawTransaction.hex()

    raw_victim_tx = recover_raw_transaction(Transaction(
        tx_hash=victim_tx_hash,
        nonce=replay_tx["nonce"],
        gas_price=replay_tx["gasPrice"],
        gas=replay_tx["gas"],
        caller=replay_tx["from"],
        receiver=replay_tx["to"],
        value=replay_tx["value"],
        data=replay_tx["data"],
        chain_id=replay_tx["chainId"],
        maxFeePerGas=replay_tx.get("maxFeePerGas", None),
        maxPriorityFeePerGas=replay_tx.get("maxPriorityFeePerGas", None),
        access_list=replay_tx.get("accessList", None),
        r=replay_tx.get("r", None).hex(),
        s=replay_tx.get("s", None).hex(),
        v=replay_tx.get("v", None),
        swap_events=[]
    ))

    async with websockets.connect(
            "wss://mev.api.blxrbdn.com/ws",
            extra_headers=[("Authorization", cfg.bloxroute_authorization)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE),
    ) as wss:
        request = json.dumps(
            {
                "id": 1,
                "method": "blxr_simulate_bundle",
                "params": {
                    "blockchain_network": "BSC-Mainnet",
                    "transaction": [front_run_raw_tx, raw_victim_tx, back_run_raw_tx],
                    "block_number": hex(ws.eth.block_number + 1),
                    "state_block_number": hex(block_number),
                    "timestamp": int(time.time()),
                    "mev_builders": {"bloxroute": "", "all": ""},
                },
            }
        )
        await wss.send(request)
        response = await wss.recv()
        response = json.loads(response)
        error = sum([1 for i in response["result"]["results"] if
                     "error" in i]) > 0 if "result" in response else False
        if "error" in response or error:
            logger.warning(f"Failed to simulate arbitrage attack: {response}")
            return None
        logger.info(f"Simulated arbitrage attack: {response}")

def run_previous_tx(block_number, from_, to):
    txs = ws.eth.get_block(block_number)["transactions"]
    for idx, tx in tqdm(enumerate(txs[from_:to + 1])):
        try:
            send_victim(tx)
        except:
            print(f"Failed to send tx: {idx} {tx.hex()}")


if __name__ == "__main__":
    block_number = 38883072 - 1

    victim_tx_hash = "0x387b93e4d021806fb487d1ee68484ba5af7d0e7b20c6a271080930b23d0adf50"
    contract_address = "0x00AA51B142c533cA9CA823c0B6F5E3401F95FcBC"
    contract_address = Web3.to_checksum_address(contract_address)

    path = Path(
        amount_in=1230966286349692533,
        exchanges=[11],
        pool_addresses=[
            "0x3DB5E175cef262394a97555c66B47f45aF8fF5eD",
        ],
        token_addresses=[
            '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
            "0x48A8Ba1754FE84E2f9dfA97982e524F18E5b4Bd3",
        ]
    )

    #run_previous_tx(38766710, 0, 50)
    #print(get_token_balance(path.token_addresses[0], contract_address))
    send_sandwich_front_run(contract_address, path)
    #run_previous_tx(38766710, 52, 87)
    tx_hash = send_victim(victim_tx_hash)
    from copy import deepcopy
    back_run_path = deepcopy(path)
    #back_run_path.amount_in = get_token_balance(back_run_path.token_addresses[-1],
    #contract_address)

    #print(back_run_path.amount_in)
    send_sandwich_back_run(contract_address, back_run_path)
    #print(get_token_balance(path.token_addresses[0], contract_address))

    #asyncio.run(simulate_bundle(victim_tx_hash, local_ws.eth.block_number, path, back_run_path))
