import time
from web3.exceptions import TransactionNotFound, TransactionIndexingInProgress
from ..utils import get_provider


def get_block_number(http_endpoint):
    w3 = get_provider(http_endpoint)
    return w3.eth.block_number


def get_gas_price(http_endpoint):
    w3 = get_provider(http_endpoint)
    return w3.eth.gas_price


def get_timestamp(http_endpoint, block_number):
    w3 = get_provider(http_endpoint)
    return w3.eth.get_block(block_number)["timestamp"]


def is_pending_tx(http_endpoint, tx_hash):
    try:
        w3 = get_provider(http_endpoint)
        tx = w3.eth.get_transaction(tx_hash)
    except TransactionNotFound:
        return False
    except ValueError as e:
        return False
    return tx["blockNumber"] is None

def is_indexing_tx(http_endpoint, tx_hash):
    try:
        w3 = get_provider(http_endpoint)
        tx = w3.eth.get_transaction(tx_hash)
    except TransactionNotFound:
        return False
    except ValueError as e:
        return False
    return tx["blockNumber"] is None

def is_successful_tx(http_endpoint, tx_hash):
    w3 = get_provider(http_endpoint)
    try:
        tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
    except TransactionIndexingInProgress:
        return False
    return tx_receipt["status"] == 1


def delay_time(http_endpoint, current_number, padding=5.35):
    w3 = get_provider(http_endpoint)
    """
    span = 10
    times = []
    first_block = w3.eth.get_block(current_number - span)
    prev_timestamp = first_block.timestamp

    for i in range(current_number - span + 1, current_number):
        block = w3.eth.get_block(i)
        time_ = block.timestamp - prev_timestamp
        prev_timestamp = block.timestamp
        times.append(time_)
    delay_second = sum(times) / len(times)
    """
    delay_second = 3
    latest_timestamp = w3.eth.get_block(current_number)

    delay = latest_timestamp.timestamp + delay_second - time.time() - padding
    if delay > 0:
        time.sleep(delay)
