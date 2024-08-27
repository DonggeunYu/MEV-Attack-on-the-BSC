import os
import sys
import json
import subprocess
import time
import requests
import pytest

sys.stdout = sys.stderr


@pytest.fixture(scope="session", autouse=True)
def http_endpoint():
    if os.environ.get("ETH_NODE_RPC_URL"):
        print("Using ETH_NODE_RPC_URL")
        return os.environ.get("ETH_NODE_RPC_URL")
    else:
        print("Using public ETH node URL")
        return (
            "https://rpc.ankr.com/eth/"
            "e890114d9658d479611923cae6286ad0de6bc32dba1c1bbeae69c0e394f3a9f3"
        )


def check_deployed_hardhat_node():
    try:
        response = requests.post(
            "http://localhost:8545",
            json={"method": "eth_blockNumber", "params": [], "id": 1, "jsonrpc": "2.0"},
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False


def pytest_sessionfinish(session, exitstatus):
    subprocess.call("pkill -f hardhat", shell=True)
    print("Killed hardhat node")


@pytest.fixture(scope="session", autouse=True)
def set_aiohttp_timeout_for_multicall():
    os.environ["AIOHTTP_TIMEOUT"] = "300"  # 300 seconds


@pytest.fixture(scope="session", autouse=True)
def deploy_hardhat_node():
    """Deploy hardhat node and deploy arbitrage contract."""

    # Start hardhat node
    print("Starting hardhat node")
    # Print Logs
    subprocess.Popen(
        "cd contract && npx hardhat --config hardhat_ethereum.ts node", shell=True
    )

    now = time.time()
    while not check_deployed_hardhat_node():
        if time.time() - now > 60:
            raise Exception("Hardhat node not started")
        time.sleep(0.2)

    print("Hardhat node started")

    # Deploy arbitrage contract
    subprocess.call(
        [
            "cd contract && "
            "npx hardhat --config hardhat_ethereum.ts "
            "--network localhost run scripts/deploy.ts"
        ],
        shell=True,
    )

    # Write file for operation needed pool addresses
    data = [
        {
            "exchange": 0,
            "pool_address": "0xa478c2975ab1ea89e8196811f51a7b7ade33eb11",
            "token_address": [
                "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            ],
            "holder_address": "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf",
        },  # Used for test_api_utils.py
        {
            "exchange": 1,
            "pool_address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
            "token_address": [
                "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            ],
            "holder_address": "0xf04a5cc80b1e94c69b48f5ee68a08cd2f09a7c3e",
        },
    ]

    formatted_data = {
        "exchanges": [],
        "poolAddresses": [],
        "tokenAddresses": [],
        "holderAddresses": [],
    }
    for i in range(len(data)):
        formatted_data["exchanges"].append(data[i]["exchange"])
        formatted_data["poolAddresses"].append(data[i]["pool_address"])
        formatted_data["tokenAddresses"].append(data[i]["token_address"])
        formatted_data["holderAddresses"].append(data[i]["holder_address"])
    with open("/tmp/arbitrage_pool_operation.json", "w") as f:
        f.write(json.dumps(formatted_data))

    # Run pool operation
    subprocess.call(
        [
            "cd contract && "
            "npx hardhat --config hardhat_ethereum.ts "
            "--network localhost run scripts/pool_operation.ts"
        ],
        shell=True,
    )


@pytest.fixture(scope="session")
def hardhat_node_endpoint():
    return "http://localhost:8545"


@pytest.fixture(scope="session")
def arbitrage_contract_address():
    arbitrage_deployed_address = open("/tmp/arbitrage_deployed_address.txt", "r").read()
    return arbitrage_deployed_address


@pytest.fixture(scope="session")
def account_address():
    return "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"


@pytest.fixture(scope="session")
def account_private_key():
    return "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
