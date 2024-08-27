import json
from web3 import Web3
from eth_account import Account, messages
from typing import Dict
from ..config import Config


def generate_header(cfg: Config, data: Dict[str, str]) -> Dict[str, str]:
    message = messages.encode_defunct(text=Web3.keccak(text=json.dumps(data)).hex())
    account = Account.from_key(cfg.account_private_key)
    signed_message = account.sign_message(message)

    header = {
        "Content-Type": "application/json",
        "X-Flashbots-Signature": f"{cfg.account_address}:{signed_message.signature.hex()}",
    }
    return header
