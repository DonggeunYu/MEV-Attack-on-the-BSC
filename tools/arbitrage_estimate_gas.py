from src.api_utils import get_arbitrage_estimated_gas, send_arbitrage

estimated_gas = get_arbitrage_estimated_gas(
    http_endpoint="http://localhost:8545",
    account_address="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    contract_address="0xBe6Eb4ACB499f992ba2DaC7CAD59d56DA9e0D823",
    gas_price=int(47.715965136 * 1e9),
    amount=101376562500000707,
    exchanges=[1, 1, 1],
    pool_addresses=[
        "0x19fe9857bb3652e9007f2347a1f877ffa9215f7f",
        "0x2b2a82d50e6e9d5b95ca644b989f9b143ea9ede2",
        "0x60594a405d53811d3bc4766596efd80fd545a270",
    ],
    token_addresses=[
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "0x102c776ddb30c754ded4fdcc77a19230a60d4e4f",
        "0x102c776ddb30c754ded4fdcc77a19230a60d4e4f",
        "0x6b175474e89094c44da98b954eedeac495271d0f",
        "0x6b175474e89094c44da98b954eedeac495271d0f",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    ],
)

print(estimated_gas)

send_arbitrage(
    http_endpoint="http://localhost:8545",
    account_address="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    account_private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    contract_address="0xBe6Eb4ACB499f992ba2DaC7CAD59d56DA9e0D823",
    gas_price=int(47.715965136 * 1e9),
    amount=101376562500000707,
    exchanges=[1, 1, 1],
    pool_addresses=[
        "0x19fe9857bb3652e9007f2347a1f877ffa9215f7f",
        "0x2b2a82d50e6e9d5b95ca644b989f9b143ea9ede2",
        "0x60594a405d53811d3bc4766596efd80fd545a270",
    ],
    token_addresses=[
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "0x102c776ddb30c754ded4fdcc77a19230a60d4e4f",
        "0x102c776ddb30c754ded4fdcc77a19230a60d4e4f",
        "0x6b175474e89094c44da98b954eedeac495271d0f",
        "0x6b175474e89094c44da98b954eedeac495271d0f",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    ],
    gas=estimated_gas,
)
