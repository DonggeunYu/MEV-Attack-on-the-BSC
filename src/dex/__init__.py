import json
from .dex import DexBase  # noqa F401
from .uniswap_v2 import UniswapV2
from .uniswap_v3 import UniswapV3
from .sushiswap_V3 import SushiSwapV3

DEX2CLASS = {
    "UNISWAP_V2": UniswapV2,
    "SUSHISWAP_V2": UniswapV2,
    "PANCAKESWAP_V2": UniswapV2,
    "THENA": UniswapV2,
    "BISWAP_V2": UniswapV2,
    "APESWAP": UniswapV2,
    "MDEX": UniswapV2,
    "BABYSWAP": UniswapV2,
    "NOMISWAP": UniswapV2,
    "BAKERYSWAP": UniswapV2,
    "UNISWAP_V3": UniswapV3,
    "SUSHISWAP_V3": SushiSwapV3,
    "PANCAKESWAP_V3": SushiSwapV3,
    "THENA_FUSION": UniswapV3,
    "WAULTSWAP": UniswapV2,
}

dex2id_path = "dex2id.json"
with open(dex2id_path, "r") as f:
    data = json.load(f)
    DEX2NAME = {key: value["name"] for key, value in data.items()}
    DEX2ID = {key: value["id"] for key, value in data.items()}
    ID2NAME = {value["id"]: value["name"] for key, value in data.items()}
    ID2DEX = {value["id"]: key for key, value in data.items()}

labels_path = "labels.json"
with open(labels_path, "r") as f:
    data = json.load(f)
    DEX2AMM = {}
    for amm, dexes in data["DEX_BY_AMM"].items():
        for dex in dexes:
            DEX2AMM[dex] = amm
