import pytest
from src.types import SwapEvent, Transaction
from src.apis.trace_tx import trace_transaction


@pytest.mark.parametrize(
    "tx_hash, expected",
    [
        (
            "0xf93e406627da3edb484a5d49272b9e4dba5283224359aaaf6379562bb9ac228e",
            Transaction(
                tx_hash="0xf93e406627da3edb484a5d49272b9e4dba5283224359aaaf6379562bb9ac228e",
                gas_price=44296534405,
                caller="0x777fE3118c99133733123445c5f6319dA3694CA5",
                receiver="0x9f51040aEc194a89cb6a7e852E79Ea07Cc0bF648",
                value=74,
                data="0x524f05aa4838b106fce9647bdf1e7877bf73ce8b0bad5f970000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000540000b4e16d0168e52d35cacd2c6185b44281ec28c9dc00000000000003003416cf6c708da44db2624d63ea0aaef7113527c600006400000100000d4a11d5eeaac28ec3f61d100daf4d40471f185200000000000000540000b4e16d0168e52d35cacd2c6185b44281ec28c9dc000000000000030042b43738db5252308f83400dd8c30754c6d0764d0027100000c80100b8a1a865e4405281311c5bc0f90c240498472d3e000000000000",
                swap_events=[
                    SwapEvent(
                        dex="UniswapV2",
                        address="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
                        token_in="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        token_out="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        amount_in=203097844817962244148,
                        amount_out=688612212140,
                    ),
                    SwapEvent(
                        dex="UniswapV3",
                        address="0x3416cf6c708da44db2624d63ea0aaef7113527c6",
                        token_in="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        token_out="0xdac17f958d2ee523a2206206994597c13d831ec7",
                        amount_in=688612212140,
                        amount_out=688821494236,
                    ),
                    SwapEvent(
                        dex="UniswapV2",
                        address="0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852",
                        token_in="0xdac17f958d2ee523a2206206994597c13d831ec7",
                        token_out="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        amount_in=688821494236,
                        amount_out=208697668087240751660,
                    ),
                ],
            ),
        ),
        (
            "0xea3d2bae4fd7e8c7e76e8da389fb8a9b4f946c1eb27d1db3e8b6d346d047c4ed",
            Transaction(
                tx_hash="0xea3d2bae4fd7e8c7e76e8da389fb8a9b4f946c1eb27d1db3e8b6d346d047c4ed",
                gas_price=44349795442,
                caller="0xF90029931C7a9A27E350cd35c91cbEdbB58350c4",
                receiver="0xD4674001A9a66b31F3c09E3b1Fec465404c83d35",
                value=98,
                data="0x21f515c14838b106fce9647bdf1e7877bf73ce8b0bad5f9700000000000000008c3ef0247444434b388c818ca8b9251b393131c08a736a67ccb19297000000000000001075474eb378e05b1d00380200318fbee0a0d60e5de7009864632ceda8d77489b80027100000c80100180efc1349a69390ade25667487a826164c9c6e40000000000000038020088e6a0c2ddd26feeb64f039a2c41296fcb3f56400001f400000a03008ad599c3a0ff1de082011efddc58f1908eb6e6d8000bb800003c",
                swap_events=[
                    SwapEvent(
                        dex="UniswapV3",
                        address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                        token_in="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        token_out="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        amount_in=460365889173414306808,
                        amount_out=1604035132633,
                    ),
                    SwapEvent(
                        dex="UniswapV3",
                        address="0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
                        token_in="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        token_out="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        amount_in=1604035132633,
                        amount_out=475494676681074809640,
                    ),
                ],
            ),
        ),
        (
            "0xb169fb3969b3549e7cf85cc5eee4f715d428a456ad39f387456ce561757502f7",
            Transaction(
                tx_hash="0xb169fb3969b3549e7cf85cc5eee4f715d428a456ad39f387456ce561757502f7",
                gas_price=43455252686,
                caller="0x0c44e8b3F8F6846D62d560991Cc58749B3F2D325",
                receiver="0x0d531E9bFcc88C42A4A707162b853d233eb586Fc",
                value=95,
                data="0xdc4d776a0000000000000000000000004838b106fce9647bdf1e7877bf73ce8b0bad5f970000000000000000000000000000000000000000000000008c3ef0247444434b00000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000001a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002600000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48000000000000000000000000000000000000000000000000000000000000000200000000000000000000000088e6a0c2ddd26feeb64f039a2c41296fcb3f5640000000000000000000000000b4e16d0168e52d35cacd2c6185b44281ec28c9dc000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                swap_events=[
                    SwapEvent(
                        dex="UniswapV3",
                        address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                        token_in="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        token_out="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        amount_in=390598073219909890370,
                        amount_out=1355229360071,
                    ),
                    SwapEvent(
                        dex="UniswapV2",
                        address="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
                        token_in="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        token_out="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        amount_in=1355229360071,
                        amount_out=403295157221122946334,
                    ),
                ],
            ),
        ),
        (
            "0xf1e475af004b5ab16b23b14a8e060db9d8739ed74271b42849f72627afc4ff1b",
            Transaction(
                tx_hash="0xf1e475af004b5ab16b23b14a8e060db9d8739ed74271b42849f72627afc4ff1b",
                gas_price=42870534405,
                caller="0x1049b387a014feD9F5Cc4D198073D1f19dE63c8B",
                receiver="0xca122E50566cC5a5F0B744c6aF7831C5174f40Fa",
                value=47,
                data="0xe449f3410000000000000000000000004838b106fce9647bdf1e7877bf73ce8b0bad5f970000000000000000000000000000000000000000000000008c3ef0247444434b00000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000001a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002600000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480000000000000000000000000000000000000000000000000000000000000002000000000000000000000000b4e16d0168e52d35cacd2c6185b44281ec28c9dc0000000000000000000000007bea39867e4169dbe237d55c8242a8f2fcdcc387000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                swap_events=[
                    SwapEvent(
                        dex="UniswapV3",
                        address="0x7bea39867e4169dbe237d55c8242a8f2fcdcc387",
                        token_in="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        token_out="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        amount_in=85401894589,
                        amount_out=25900888941500138575,
                    ),
                    SwapEvent(
                        dex="UniswapV2",
                        address="0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
                        token_in="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        token_out="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        amount_in=25623998714561155825,
                        amount_out=85401894589,
                    ),
                ],
            ),
        ),
    ],
)
def test_trace_transaction(http_endpoint, tx_hash, expected):
    tx = trace_transaction(http_endpoint, tx_hash, debug_trace_transaction=True)
    assert tx.tx_hash == expected.tx_hash
    assert tx.gas_price == expected.gas_price
    assert tx.caller == expected.caller
    assert tx.receiver == expected.receiver
    assert tx.value == expected.value
    assert tx.data == expected.data
    assert len(tx.swap_events) == len(expected.swap_events)
    for swap_event, expected_swap_event in zip(tx.swap_events, expected.swap_events):
        assert swap_event.dex == expected_swap_event.dex
        assert swap_event.address == expected_swap_event.address
        assert swap_event.token_in == expected_swap_event.token_in
        assert swap_event.token_out == expected_swap_event.token_out
        assert swap_event.amount_in == expected_swap_event.amount_in
        assert swap_event.amount_out == expected_swap_event.amount_out