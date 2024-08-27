import pytest
from src.arbitrage.search import search_arbitrage_candidate_path
from src.config import local_config
from src.types import Transaction, SwapEvent, DexInfos, DexInfo, PoolInfo, Path


@pytest.mark.parametrize(
    "tx, dex_infos, expected",
    [
        (
            Transaction(
                tx_hash="0xb7885c27b25a6e834b4d680be21ce8e00e710765e14fefed37be3dee66776561",
                gas_price=0,
                caller="",
                receiver="",
                value=0,
                data="",
                swap_events=[
                    SwapEvent(
                        dex="UniswapV2",
                        address="0x72833289c5f4ad7aa4a88a538300ec4d4a879421",
                        token_in="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                        token_out="0x0cC488a3F6C9A569614912e421115995493FDFEC",
                        amount_in=1,
                        amount_out=2,
                    ),
                ],
            ),
            DexInfos(
                [
                    DexInfo(
                        "UniswapV2",
                        [
                            PoolInfo(
                                "UniswapV2",
                                "0xeb2e0747e5dfd01fd7412b605702a06d4a96c1ab",
                                (
                                    "0x0cC488a3F6C9A569614912e421115995493FDFEC",
                                    "0xF2B2f7b47715256Ce4eA43363a867fdce9353e3A",
                                ),
                            )
                        ],
                    ),
                    DexInfo(
                        "UniswapV3",
                        [
                            PoolInfo(
                                "UniswapV3",
                                "0xa87de12ea019b7b55772bbffc0d9a844f7327ef9",
                                (
                                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                                    "0xF2B2f7b47715256Ce4eA43363a867fdce9353e3A",
                                ),
                            ),
                        ],
                    ),
                ]
            ),
            (
                (
                    Path(
                        amount_in=1,
                        exchanges=[1, 0, 0],
                        pool_addresses=[
                            "0xa87De12EA019B7b55772BbFFc0d9a844F7327Ef9",
                            "0xEB2e0747E5dfd01Fd7412b605702a06D4A96c1AB",
                            "0x72833289C5F4ad7aA4A88a538300EC4d4A879421",
                        ],
                        token_addresses=[
                            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                            "0xF2B2f7b47715256Ce4eA43363a867fdce9353e3A",
                            "0xF2B2f7b47715256Ce4eA43363a867fdce9353e3A",
                            "0x0cC488a3F6C9A569614912e421115995493FDFEC",
                            "0x0cC488a3F6C9A569614912e421115995493FDFEC",
                            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                        ],
                    ),
                ),
            ),
        )
    ],
)
def test_search_arbitrage_candidate_path(tx, dex_infos, expected):
    result = search_arbitrage_candidate_path(
        cfg=local_config, victim_tx=tx, dex_infos=dex_infos
    )

    for (key, value), expected_paths in zip(result.items(), expected):
        for path, expected_path in zip(value, expected_paths):
            assert path.exchanges == expected_path.exchanges
            assert path.pool_addresses == expected_path.pool_addresses
            assert path.token_addresses == expected_path.token_addresses
