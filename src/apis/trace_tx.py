import os
import sys
import traceback
from typing import List
from loguru import logger
from web3.exceptions import TransactionNotFound
from ..types import SwapEvent, Transaction
from ..config import Config
from ..utils import get_provider, eq_address
from ..dex import DEX2ID

TOP_BIT_256BIT_INT = 2 ** 255
BIT_256BIT_INT = 2 ** 256


def hex_to_uint256(hex_str):
    return int(hex_str, 16)


def hex_to_int256(hex_str):
    value = int(hex_str, 16)
    if value >= TOP_BIT_256BIT_INT:
        value -= BIT_256BIT_INT
    return value


def set_swap_event(dex, swap_events, to):
    exist = False
    for swap_event in swap_events:
        if swap_event.address == to:
            swap_event.dex = dex
            exist = True
    if not exist:
        swap_events.append(SwapEvent(
            dex=dex,
            address=to,
        ))

    return swap_events

def set_transfer_event(swap_events, from_, to, recipient, value):
    def swap_in_out_if_minus(swap_event):
        if swap_event.amount_in < 0 or swap_event.amount_out < 0:
            swap_event.token_in, swap_event.token_out = swap_event.token_out, swap_event.token_in
            swap_event.amount_in, swap_event.amount_out = -swap_event.amount_out, -swap_event.amount_in
    recipient_exist = False
    from_exist = False
    for swap_event in swap_events:
        if (swap_event.address == recipient and
                    (swap_event.token_in is None or swap_event.token_in == to)):
            swap_event.token_in = to
            swap_event.amount_in += value
            recipient_exist = True
        elif (swap_event.address == from_ and
                (swap_event.token_out is None or swap_event.token_out == to)):
            swap_event.token_out = to
            swap_event.amount_out += value
            from_exist = True
        elif (swap_event.address == recipient and
                (swap_event.token_out == to)):
            swap_event.amount_out -= value
            swap_in_out_if_minus(swap_event)
            recipient_exist = True
        elif (swap_event.address == from_ and
                (swap_event.token_in == to)):
            swap_event.amount_in -= value
            swap_in_out_if_minus(swap_event)
            from_exist = True

    if recipient_exist is False:
        swap_events.append(SwapEvent(
                    address=recipient,
                    token_in=to,
                    amount_in=value
                ))
    if from_exist is False:
        swap_events.append(SwapEvent(
                    address=from_,
                    token_out=to,
                    amount_out=value
                ))

    return swap_events

def search_dex_transaction(call, previous_swap_events=None):
    """
    Search for DEX transactions in the call trace

    Args:
        call: The call trace
        previous_swap_events: Do not use this argument. It is used for recursive calls.

    """
    if previous_swap_events is not None:
        swap_events = previous_swap_events
    else:
        swap_events = []

    from_ = call["from"]
    to = call["to"]
    input = call["input"]

    if "input" not in call:
        return []

    if input.startswith("0x022c0d9f"):
        swap_events = set_swap_event("UNISWAP_V2", swap_events, to)
    if input.startswith("0x6d9a640a"):
        swap_events = set_swap_event("BAKERYSWAP", swap_events, to)
    if input.startswith("0x128acb08"):
        swap_events = set_swap_event("UNISWAP_V3", swap_events, to)

    # transfer
    is_in_transfer = False
    if input.startswith("0xa9059cbb"):
        recipient = "0x" + input[2 + 32: 2 + 32 + 40]
        value = hex_to_uint256(input[2 + 32 + 40: 2 + 32 + 40 + 64])
        if value > 0:
            swap_events = set_transfer_event(swap_events, from_, to, recipient, value)
            is_in_transfer = True
    # transferFrom
    if input.startswith("0x23b872dd"):
        sender = "0x" + input[2 + 32: 2 + 32 + 40]
        recipient = "0x" + input[2 + 32 + 40 + 64 - 40: 2 + 32 + 40 + 64]
        value = hex_to_uint256(input[2 + 32 + 40 + 64: 2 + 32 + 40 + 64 + 64])
        if value > 0:
            swap_events = set_transfer_event(swap_events, sender, to, recipient, value)
            is_in_transfer = True

    if "calls" in call and not is_in_transfer:
        for c in call["calls"]:
            swap_events = search_dex_transaction(c, swap_events)

    return swap_events


def filter_swap_events(swap_events: List[SwapEvent]):
    valid_swap_events = []
    for swap_event in swap_events:
        if swap_event.is_valid():
            valid_swap_events.append(swap_event)

    return valid_swap_events


def trace_transaction_for_debug(cfg, tx_hash):
    w3 = get_provider(cfg.http_endpoint)
    try:
        tx_detail = w3.eth.get_transaction(tx_hash)
    except TransactionNotFound:
        return None

    trace = w3.provider.make_request(
        "debug_traceTransaction", [tx_hash, {"tracer": "callTracer"}]
    )

    logger.warning(f"Calling debug_traceTransaction with tx_hash: {tx_hash}")
    if (
            "result" not in trace
            or "error" in trace["result"]
            or ("error" in trace and trace["error"]["code"] == -32000)
    ):
        logger.info(f"Error calling debug_traceCall with tx_hash: {tx_detail['txHash']}")
        return None

    if "calls" not in trace["result"]:
        logger.info(f"No calls found for tx hash: {tx_detail['txHash']}")
        return None

    try:
        swap_events = search_dex_transaction(trace["result"])
        swap_events = filter_swap_events(swap_events)
        new_swap_events = []
        for swap_event in swap_events:
            if eq_address(swap_event.token_in, cfg.wrapped_native_token_address) and swap_event.amount_in < 1e16:
                pass
            else:
                new_swap_events.append(swap_event)
        swap_events = sorted(new_swap_events, key=lambda x: DEX2ID[x.dex])
    except Exception as e:
        swap_events = []
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(exc_type)
        logger.error(fname)
        logger.error(exc_tb.tb_lineno)
        logger.error(e)
        logger.error(traceback.format_exc())
        # raise e

    return Transaction(
        chain_id=tx_detail["chainId"] if "chainId" in tx_detail else None,
        tx_hash=tx_detail["hash"].hex(),
        gas=tx_detail["gas"],
        gas_price=tx_detail["gasPrice"] if "gasPrice" in tx_detail else None,
        maxFeePerGas=tx_detail["maxFeePerGas"] if "maxFeePerGas" in tx_detail else None,
        maxPriorityFeePerGas=tx_detail[
            "maxPriorityFeePerGas"] if "maxPriorityFeePerGas" in tx_detail else None,
        caller=tx_detail["from"],
        receiver=tx_detail["to"],
        value=tx_detail["value"],
        data=tx_detail["input"],
        nonce=tx_detail["nonce"],
        r=tx_detail["r"].hex(),
        s=tx_detail["s"].hex(),
        v=tx_detail["v"],
        access_list=tx_detail["accessList"] if "accessList" in tx_detail else None,
        swap_events=swap_events,
    )


def trace_transaction(cfg: Config, tx_detail):
    w3 = get_provider(cfg.http_endpoint)
    txContents = tx_detail["txContents"]
    gas_price = txContents["gasPrice"] if txContents["gasPrice"] else txContents["maxFeePerGas"]
    tx_detail_for_trace = {
        "from": txContents["from"],
        "to": txContents["to"],
        "gas_cost": gas_price,
        "value": txContents["value"],
        "data": txContents["input"],
    }
    trace = w3.provider.make_request(
        "debug_traceCall", [tx_detail_for_trace, "latest", {"tracer": "callTracer"}]
    )

    if (
            "result" not in trace
            or "error" in trace["result"]
            or ("error" in trace and trace["error"]["code"] == -32000)
    ):
        logger.info(f"Error calling debug_traceCall with tx_hash: {tx_detail['txHash']}")
        return None

    if "calls" not in trace["result"]:
        logger.info(f"No calls found for tx hash: {tx_detail['txHash']}")
        return None

    try:
        swap_events = search_dex_transaction(trace["result"])
        swap_events = filter_swap_events(swap_events)
        new_swap_events = []
        for swap_event in swap_events:
            if (eq_address(swap_event.token_in, cfg.wrapped_native_token_address) and
                    swap_event.amount_in < 1e15):
                pass
            else:
                new_swap_events.append(swap_event)
        swap_events = sorted(new_swap_events, key=lambda x: DEX2ID[x.dex])
    except Exception as e:
        swap_events = []
        logger.error(f"Error parsing tx hash: {tx_detail['txHash']}")
        logger.error(f"Error parsing swap events: {e}")
        # raise e

    if len(swap_events) == 0:
        logger.info(f"No swap events found for tx hash: {tx_detail['txHash']}")
        return None

    return Transaction(
        chain_id=txContents["chainId"] if "chainId" in txContents else None,
        tx_hash=tx_detail["txHash"],
        gas=txContents["gas"],
        gas_price=gas_price,
        maxFeePerGas=txContents["maxFeePerGas"] if "maxFeePerGas" in txContents else None,
        maxPriorityFeePerGas=txContents[
            "maxPriorityFeePerGas"] if "maxPriorityFeePerGas" in txContents else None,
        caller=txContents["from"],
        receiver=txContents["to"],
        value=txContents["value"],
        data=txContents["input"],
        nonce=txContents["nonce"],
        r=txContents["r"],
        s=txContents["s"],
        v=txContents["v"],
        access_list=txContents["accessList"] if "accessList" in txContents else None,
        swap_events=swap_events,
    )
