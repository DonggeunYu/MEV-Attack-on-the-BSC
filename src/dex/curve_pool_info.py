STABLESWAP_PLAIN_AND_META_POOL_INFO = {
    "0xdc24316b9ae028f1497c275eb9192a3ea0f67022": {
        "TYPE": "USE_BALANCES",
        "GET_Y_MINUS_ONE": True,
        "GET_D_PLUS_ONE": True,
        "PRECISION_MUL": [1, 1000000000000],
        "COINS": [
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
        ],
        "LP_TOKEN": "0x06325440d014e39736583c165c2963ba99faf14e",
        "N_COINS": 2,
        "VYPER_VERSION_1": False,
    },
    "0x9c3b46c0ceb5b9e304fcd6d88fc50f7dd24b31bc": {
        "TYPE": "USE_RATE_MULTIPLIERS",
        "GET_Y_MINUS_ONE": True,
        "PRECISION_MUL": [],
        "RATE_MULTIPLIERS": [10**18, 10**18],
        "COINS": [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "0x5E8422345238F34275888049021821E8E08CAa1f",
        ],
        "N_COINS": 2,
    },
    "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7": {
        "TYPE": "USE_RATES",
        "GET_Y_MINUS_ONE": True,
        "PRECISION_MUL": [
            1,
            1000000000000,
            1000000000000,
        ],
        "COINS": [
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "0xdac17f958d2ee523a2206206994597c13d831ec7",
        ],
        "LP_TOKEN": "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
        "N_COINS": 3,
        "VYPER_VERSION_1": False,
    },
    "0xA5407eAE9Ba41422680e2e00537571bcC53efBfD": {
        "TYPE": "USE_LENDING",
        "USE_LENDING": [False, False, False, False],
        "PRECISION_MUL": [
            1,
            1000000000000,
            1000000000000,
            1,
        ],
        "COINS": [
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "0x57Ab1ec28D129707052df4dF418D58a2D46d5f51",
        ],
        "N_COINS": 4,
    },
    "0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C": {
        "TYPE": "USE_LENDING",
        "USE_LENDING": [True, True, False],
        "PRECISION_MUL": [
            1,
            1000000000000,
            1000000000000,
        ],
        "COINS": [
            "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
            "0x39AA39c021dfbaE8faC545936693aC917d5E7563",
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        ],
        "N_COINS": 3,
    },
    "0xDeBF20617708857ebe4F679508E7b7863a8A8EeE": {
        "TYPE": "AAVE",
        "A_PRECISION": 100,
        "PRECISION_MUL": [
            1,
            1000000000000,
            1000000000000,
        ],
        "N_COINS": 3,
    },
    "0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF": {
        "TYPE": "STORED_RATES",
        "GET_Y_MINUS_ONE": True,
        "A_PRECISION": 100,
        "PRECISION_MUL": [
            1,
            1000000000000,
            1000000000000,
        ],
        "COINS": [
            "0x8e595470ed749b85c6f7669de83eae304c2ec68f",
            "0x76eb2fe28b36b3ee97f3adae0c69606eedb2a37c",
            "0x48759f220ed983db51fa7a8c0d2aab8f3ce4166a",
        ],
        "N_COINS": 3,
    },
    "0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56": {
        "TYPE": "USE_LENDING",
        "USE_LENDING": [True, True],
        "PRECISION_MUL": [
            1,
            1000000000000,
        ],
        "COINS": [
            "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
            "0x39AA39c021dfbaE8faC545936693aC917d5E7563",
        ],
        "N_COINS": 2,
    },
    "0x06364f10B501e868329afBc005b3492902d6C763": {
        "TYPE": "USE_LENDING_1",
        "GET_Y_MINUS_ONE": True,
        "USE_LENDING": [True, True, True, False],
        "PRECISION_MUL": [1, 1000000000000, 1000000000000, 1],
        "COINS": [
            "0x99d1Fa417f94dcD62BfE781a1213c092a47041Bc",
            "0x9777d7E2b60bB01759D0E2f8be2095df444cb07E",
            "0x1bE5d71F2dA660BFdee8012dDc58D024448A0A59",
            "0x8E870D67F660D95d5be530380D0eC0bd388289E1",
        ],
        "N_COINS": 4,
    },
}
STABLESWAP_META_POOL_INFO = {
    "0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1": {
        "TYPE": "BASE_VIRTUAL_PRICE",
        "GET_Y_MINUS_ONE": True,
        "A_PRECISION": 100,
        "base_pool": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
        "BASE_CACHE_EXPIRES": 10 * 60,  # 10 minutes
        "PRECISION_MUL": [1, 1],
        "COINS": [
            "0x674C6Ad92Fd080e4004b2312b45f796a192D27a0",
            "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
        ],
        "N_COINS": 2,
        "BASE_N_COINS": 3,
    },
    "0x4f062658EaAF2C1ccf8C8e36D6824CDf41167956": {
        "TYPE": "BASE_VIRTUAL_PRICE",
        "GET_Y_MINUS_ONE": True,
        "A_PRECISION": 100,
        "base_pool": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
        "BASE_CACHE_EXPIRES": 10 * 60,  # 10 minutes
        "PRECISION_MUL": [10000000000000000, 1],
        "COINS": [
            "0x056Fd409E1d7A124BD7017459dFEa2F387b6d5Cd",
            "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
        ],
        "N_COINS": 2,
        "BASE_N_COINS": 3,
    },
}

STABLESWAP_NG_PLAIN_POOL_INFO = {
    "0xa5588f7cdf560811710a2d82d3c9c99769db1dcb": {
        "N_COINS": 2,
    },
    "0xce6431d21e3fb1036ce9973a3312368ed96f5ce7": {
        "N_COINS": 2,
    },
}

STABLESWAP_NG_META_POOL_INFO = {
    "0x00e6fd108c4640d21b40d02f18dd6fe7c7f725ca": {
        "BASE_POOL": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
        "N_COINS": 2,
        "BASE_N_COINS": 3,
        "COINS": [
            "0x0E573Ce2736Dd9637A0b21058352e1667925C7a8",
            "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
        ],
    },
    "0xc83b79c07ece44b8b99ffa0e235c00add9124f9e": {
        "BASE_POOL": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
        "N_COINS": 2,
        "BASE_N_COINS": 3,
        "COINS": [
            "0x59D9356E565Ab3A36dD77763Fc0d87fEaf85508C",
            "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490",
        ],
    },
}

CRYPTOSWAP_POOL_INFO = {
    "0x9409280dc1e6d33ab7a8c6ec03e5763fb61772b5": {
        "COINS": [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32",
        ],
        "N_COINS": 2,
    },
    "0xb576491f1e6e5e62f1d8f26062ee822b40b0e0d4": {
        "COINS": [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b",
        ],
        "N_COINS": 2,
    },
}

TRYCRYPTOSWAP_POOL_INFO = {
    "0xd51a44d3fae010294c616388b506acda1bfaae46": {
        "PRECISIONS": [1000000000000, 10000000000, 1],
        "COINS": [
            "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        ],
        "N_COINS": 3,
    }
}
TRYCRYPTOSWAP_NG_POOL_INFO = {
    "0x7f86bf177dd4f3494b841a37e810a34dd56c829b": {
        "COINS": [
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        ],
        "N_COINS": 3,
    },
    "0x2570f1bd5d2735314fc102eb12fc1afe9e6e7193": {
        "COINS": [
            "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
            "0xae78736Cd615f374D3085123A210448E74Fc6393",
            "0xac3E018457B222d93114458476f3E3416Abbe38F",
        ],
        "N_COINS": 3,
    },
}

INFORMATION_FOR_POOL = {}
for pool_info in [
    STABLESWAP_PLAIN_AND_META_POOL_INFO,
    STABLESWAP_META_POOL_INFO,
    STABLESWAP_NG_PLAIN_POOL_INFO,
    STABLESWAP_NG_META_POOL_INFO,
    CRYPTOSWAP_POOL_INFO,
    TRYCRYPTOSWAP_POOL_INFO,
    TRYCRYPTOSWAP_NG_POOL_INFO,
]:
    for k, v in pool_info.items():
        INFORMATION_FOR_POOL[k.lower()] = v
