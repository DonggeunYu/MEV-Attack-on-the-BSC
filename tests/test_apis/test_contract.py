import pytest
from src.apis.contract import get_decimals_by_token_address


@pytest.mark.parametrize(
    "token_address, symbol, decimals",
    [
        ("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "WETH", 18),
        ("0x6B175474E89094C44Da98b954EedeAC495271d0F", "DAI", 18),
        ("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "USDC", 6),
        ("0xdac17f958d2ee523a2206206994597c13d831ec7", "USDT", 6),
        ("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", "WBTC", 8),
        ("0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852", "UNI-V2", 18),
    ],
)
def test_get_decimals_by_token_address(
    hardhat_node_endpoint, token_address, symbol, decimals
):
    result = get_decimals_by_token_address(hardhat_node_endpoint, [token_address])
    assert result[token_address]["symbol"] == symbol
    assert result[token_address]["decimals"] == decimals
