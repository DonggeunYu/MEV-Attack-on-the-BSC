import math
import time
from typing import Any, Dict, List, Optional, Tuple
from web3 import Web3
from ..multicall import Call
from ..utils import multicall_by_chunk
from .dex import DexBase
from .utils import mostSignificantBit, leastSignificantBit
from ..types import PoolInfo
from ..utils import memoize
from decimal import Decimal


MIN_SQRT_RATIO = 4295128739
MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342
MIN_TICK = -887272
MAX_TICK = 887272


class UniswapV3(DexBase):
    def __init__(self, http_endpoint: str, word_cache_size=8):
        super().__init__(http_endpoint)
        self.uniwap_v3_bitmap = UniswapV3Bitmap(
            http_endpoint, [], word_cache_size=word_cache_size
        )

    def fetch_pools_reserve_info(
        self, pool_addresses: List[str], block_number=None
    ) -> Dict[str, Tuple[Any]]:
        """
        Fetch reserve info from uniswap v3

        Args:
            pool_addresses:

        Returns:
            Dict[str, List[Any]]: {pool_address: [sqrt_price_x96, tick, observation_index, observation_cardinality,
                observation_cardinality_next, fee_protocol, unlocked]}

        """
        signature_slot0 = "slot0()((uint160,int24,uint16,uint16,uint16,uint8,bool))"
        signature_liquidity = "liquidity()(uint128)"
        calls = []
        for address in pool_addresses:
            call = Call(
                address, signature_slot0, [(address + "_s", lambda x: x)], block_number
            )
            calls.append(call)
            call = Call(
                address,
                signature_liquidity,
                [(address + "_l", lambda x: x)],
                block_number,
            )
            calls.append(call)
        result = multicall_by_chunk(self.http_endpoint, calls)

        formmatted_result = {}
        for k, v in result.items():
            address = k[:-2]
            type = k[-1]
            if address not in formmatted_result:
                formmatted_result[address] = []
            if type == "s":
                v = list(v)
                formmatted_result[address].extend(v)
            else:
                formmatted_result[address].append(v)

        for k, v in formmatted_result.items():
            formmatted_result[k] = tuple(v)

        return formmatted_result

    def fetch_pools_token_addresses(
        self, pool_addresses: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        signature0 = "token0()(address)"
        signature1 = "token1()(address)"
        calls = []
        for address in pool_addresses:
            call0 = Call(address, signature0, [(address + "_0", lambda x: x)])
            call1 = Call(address, signature1, [(address + "_1", lambda x: x)])
            calls.extend([call0, call1])
        result = multicall_by_chunk(self.http_endpoint, calls)

        formatted_result = {}
        for k, v in result.items():
            address = k[:-2]
            if address not in formatted_result:
                formatted_result[address] = []
            if k.endswith("_0"):
                formatted_result[address] = [v] + formatted_result[address]
            else:
                formatted_result[address].append(v)

        for k, v in formatted_result.items():
            formatted_result[k] = tuple(v)

        return formatted_result

    def fetch_pools_fee(self, addresses: List[str]):
        """
        Fetch fee from uniswap v3
        Fee is in 1e-6

        Args:
            addresses: list of pool address

        Returns: Dict[str, int]: {pool_address: fee}

        """
        signature = "fee()(uint24)"
        calls = []
        for address in addresses:
            call = Call(address, signature, [(address, lambda x: x)])
            calls.append(call)
        result = multicall_by_chunk(self.http_endpoint, calls)
        result = {k: v for k, v in result.items()}
        return result

    @memoize(maxsize=512)
    def calculate_price(
        self,
        pool_info: PoolInfo,
        token0: str,
        token1: str,
        decimals0: int,
        decimals1: int,
    ):
        (
            sqrt_price_x96,
            tick,
            observation_index,
            observation_cardinality,
            observation_cardinality_next,
            fee_protocol,
            unlocked,
            _,
        ) = pool_info.reserve_info
        price = (sqrt_price_x96 / (2**96)) ** 2

        if token1 == pool_info.token_addresses[0]:
            price = 1 / price
        return price * (1 - pool_info.fee * 1e-6)

    @staticmethod
    def calculate_amount_in_by_slippage(
        pool_reserve_info, slippage=0.005, reverse=False
    ):
        """


        Args:
            pool_reserve_info:
            slippage:
            reverse:

        Returns: Expected amount out by slippage
        """
        (
            sqrt_price_x96,
            tick,
            observation_index,
            observation_cardinality,
            observation_cardinality_next,
            fee_protocol,
            unlocked,
            liquidity,
        ) = pool_reserve_info

        # (L * (P ** 0.5)) / (L / (P ** 0.5)) = P
        # delta = ((L * (P ** 0.5)) / (P * (1 - slippage))) - (L / (P ** 0.5))
        if reverse:
            price = (sqrt_price_x96 / (2**96)) ** 2
            price = 1 / price
            delta = ((liquidity * (price**0.5)) / (price * (1 - slippage))) - (
                liquidity / (price**0.5)
            )
        else:
            price = (sqrt_price_x96 / (2**96)) ** 2
            delta = ((liquidity * (price**0.5)) / (price * (1 - slippage))) - (
                liquidity / (price**0.5)
            )
        delta = math.floor(delta)
        return delta

    def calculate_slippage(
        self,
        pool_info: PoolInfo,
        amount_in: float,
        token0: str,
        token1: str,
        decimals0: int,
        decimals1: int,
    ) -> float:
        (
            sqrt_price_x96,
            tick,
            observation_index,
            observation_cardinality,
            observation_cardinality_next,
            fee_protocol,
            unlocked,
            liquidity,
        ) = pool_info.reserve_info

        reverse = token0 == pool_info.token_addresses[1]

        if reverse:
            sqrt_price = sqrt_price_x96 / (2**96)
            sqrt_price = 1 / sqrt_price
            return 1 - (
                (liquidity * sqrt_price) / ((liquidity / sqrt_price) + amount_in)
            ) / (sqrt_price**2)
        else:
            sqrt_price = sqrt_price_x96 / (2**96)
            return 1 - (
                (liquidity * sqrt_price) / ((liquidity / sqrt_price) + amount_in)
            ) / (sqrt_price**2)

    def calculate_amount_out(
        self,
        pool_info: PoolInfo,
        amount_in: int,
        token0: str,
        token1: str,
        block_number: Optional[int] = None,
        timeout=None,
        reflect=False,
    ) -> int:
        pool_address = pool_info.address
        fee = pool_info.fee

        reverse = token0 == pool_info.token_addresses[1]

        if pool_address not in self.uniwap_v3_bitmap.tick_bitmap:
            self.uniwap_v3_bitmap.tick_bitmap[pool_address] = {}
            self.uniwap_v3_bitmap.tick_data[pool_address] = {}
        (
            sqrt_price_x96,
            tick,
            observation_index,
            observation_cardinality,
            observation_cardinality_next,
            fee_protocol,
            unlocked,
            liquidity,
        ) = pool_info.reserve_info
        amount_specified_remaining = amount_in
        amount_calculated = 0
        next_tick = 0
        now = time.time()
        while (
            amount_specified_remaining != 0
            and MIN_SQRT_RATIO < sqrt_price_x96
            and sqrt_price_x96 < MAX_SQRT_RATIO
        ):
            sqrt_price_start_x96 = sqrt_price_x96
            tick_spacing = UniswapV3Bitmap._get_tick_spacing_from_fee(fee)

            compressed = int(Decimal(tick) // tick_spacing)

            if tick < 0 and tick % tick_spacing != 0:
                compressed -= 1

            initialized_status = False
            if reverse:
                word_position, bit_position = UniswapV3Bitmap.position(compressed + 1)

                if (
                    word_position not in self.uniwap_v3_bitmap.tick_bitmap[pool_address]
                    or self.uniwap_v3_bitmap.tick_bitmap[pool_address][word_position][
                        "block_number"
                    ]
                    < block_number
                ):
                    self.uniwap_v3_bitmap.update_tick_data_at_word(
                        pool_address, word_position, right=True
                    )
                bitmap_at_word = self.uniwap_v3_bitmap.tick_bitmap[pool_address][
                    word_position
                ]["bitmap"]

                mask = ~((1 << bit_position) - 1)
                masked = bitmap_at_word & mask

                initialized_status = masked != 0
                if initialized_status:
                    next_tick = (
                        compressed + 1 + (leastSignificantBit(masked) - bit_position)
                    ) * tick_spacing
                else:
                    # 255 = 2^8 - 1 = MAX_UINT8
                    next_tick = (compressed + 1 + (255 - bit_position)) * tick_spacing

            else:
                word_position, bit_position = UniswapV3Bitmap.position(compressed)

                if (
                    word_position not in self.uniwap_v3_bitmap.tick_bitmap[pool_address]
                    or self.uniwap_v3_bitmap.tick_bitmap[pool_address][word_position][
                        "block_number"
                    ]
                    < block_number
                ):
                    self.uniwap_v3_bitmap.update_tick_data_at_word(
                        pool_address, word_position, right=False
                    )
                bitmap_at_word = self.uniwap_v3_bitmap.tick_bitmap[pool_address][
                    word_position
                ]["bitmap"]

                mask = 2 * (1 << bit_position) - 1
                masked = bitmap_at_word & mask

                initialized_status = masked != 0
                if initialized_status:
                    next_tick = (
                        compressed - (bit_position - mostSignificantBit(masked))
                    ) * tick_spacing
                else:
                    next_tick = (compressed - (bit_position)) * tick_spacing

            tick_next_word, _ = UniswapV3Bitmap._get_tick_bitmap_position(
                next_tick, tick_spacing
            )
            if tick_next_word not in self.uniwap_v3_bitmap.tick_bitmap[pool_address]:
                self.uniwap_v3_bitmap.update_tick_data_at_word(
                    pool_address, tick_next_word
                )
            if next_tick < MIN_TICK:
                next_tick = MIN_TICK
            if next_tick > MAX_TICK:
                next_tick = MAX_TICK
            sqrt_price_next_x96 = get_sqrt_ratio_at_tick(next_tick)

            # compute values to swap to the target tick, price limit, or point where input/output amount is exhausted
            if reverse:
                if sqrt_price_next_x96 > MAX_SQRT_RATIO:
                    new_sqrt_price_x96 = MAX_SQRT_RATIO - 1
                else:
                    new_sqrt_price_x96 = sqrt_price_next_x96
            else:
                if sqrt_price_next_x96 < MIN_SQRT_RATIO:
                    new_sqrt_price_x96 = MIN_SQRT_RATIO
                else:
                    new_sqrt_price_x96 = sqrt_price_next_x96

            sqrt_price_x96, amount_in, amount_out, fee_amount = compute_swap_step(
                sqrt_price_x96,
                new_sqrt_price_x96,
                liquidity,
                amount_specified_remaining,
                fee,
            )

            amount_specified_remaining -= amount_in + fee_amount
            amount_calculated = amount_calculated - amount_out

            if sqrt_price_x96 == sqrt_price_next_x96:
                if initialized_status:
                    liquidity_net = self.uniwap_v3_bitmap.tick_data[pool_address][
                        next_tick
                    ]["liquidity_net"]

                    if not reverse:
                        liquidity_net = -liquidity_net

                    liquidity = liquidity + liquidity_net

                tick = next_tick if reverse else next_tick - 1

            elif sqrt_price_x96 != sqrt_price_start_x96:
                tick = get_tick_at_sqrt_ratio(sqrt_price_x96)
            if timeout is not None and time.time() - now > timeout:
                break

        # Update Status
        if reflect:
            pool_info.reserve_info = (
                sqrt_price_x96,
                tick,
                observation_index,
                observation_cardinality,
                observation_cardinality_next,
                fee_protocol,
                unlocked,
                liquidity,
            )

        if reverse:
            amount0, amount1 = amount_calculated, amount_in - amount_specified_remaining
        else:
            amount0, amount1 = amount_in - amount_specified_remaining, amount_calculated

        return -amount0 if reverse else -amount1


class UniswapV3Bitmap:
    def __init__(
        self, http_endpoint: str, pool_addresses: List[str], word_cache_size=8
    ):
        self.http_endpoint = http_endpoint
        self.lens_address = "0xbfd8137f7d1516D3ea5cA83523914859ec47F573"
        self.tick_bitmap = {pool_address: {} for pool_address in pool_addresses}
        self.tick_data = {pool_address: {} for pool_address in pool_addresses}
        self.word_cache_size = word_cache_size

    @staticmethod
    def _get_tick_spacing_from_fee(fee: int):
        tick_spacing_by_fee = {
            100: 1,
            500: 10,
            3000: 60,
            10000: 200,
        }

        return tick_spacing_by_fee[fee]

    @staticmethod
    def _get_tick_bitmap_position(tick, tick_spacing):
        tick = int(int(Decimal(tick)) // tick_spacing)
        word_position, bit_position = UniswapV3Bitmap.position(tick)
        return word_position, bit_position

    @staticmethod
    def position(tick: int) -> Tuple[int, int]:
        word_position: int = tick >> 8
        bit_position: int = tick % 256
        return word_position, bit_position

    def get_tick_bitmap(self, address, word_position, right=True):
        w3 = Web3(Web3.HTTPProvider(self.http_endpoint))
        signature = "tickBitmap(int16)(uint256)"
        calls = []
        for i in range(self.word_cache_size):
            if right:
                call = Call(
                    address,
                    [signature, word_position + i],
                    [(address + "_" + str(word_position + i), lambda x: x)],
                    _w3=w3,
                )
            else:
                call = Call(
                    address,
                    [signature, word_position - i],
                    [(address + "_" + str(word_position - i), lambda x: x)],
                    _w3=w3,
                )
            calls.append(call)
        result = multicall_by_chunk(self.http_endpoint, calls)
        formatted_result = {}
        for k, v in result.items():
            _word_position = int(k.split("_")[-1])
            formatted_result[_word_position] = v

        return formatted_result

    def get_block_number(self):
        w3 = Web3(Web3.HTTPProvider(self.http_endpoint))
        block_number = w3.eth.blockNumber
        return block_number

    def get_single_tick_data(self, address, ticks):
        w3 = Web3(Web3.HTTPProvider(self.http_endpoint))
        signature = "getPopulatedTicksInWord(address,int16)((int24,int128,uint128)[])"

        calls = []
        for tick in ticks:
            call = Call(
                self.lens_address,
                [signature, address, tick],
                [(address + "_" + str(tick), lambda x: x)],
                _w3=w3,
            )
            calls.append(call)

        result = multicall_by_chunk(self.http_endpoint, calls)
        formatted_result = []
        for k, v in result.items():
            if len(v) > 0:
                formatted_result.extend(v)
        return formatted_result

    def update_tick_data_at_word(self, address, word_position, right=True):
        block_number = self.get_block_number()

        single_tick_bitmap = self.get_tick_bitmap(address, word_position, right)
        for key, value in single_tick_bitmap.items():
            self.tick_bitmap[address][key] = {
                "bitmap": value,
                "block_number": block_number,
            }

        filtered_single_tick_bitmap = {}
        for key, value in single_tick_bitmap.items():
            if value == 0:
                continue
            filtered_single_tick_bitmap[key] = value

        if filtered_single_tick_bitmap:
            list_of_word_position = filtered_single_tick_bitmap.keys()
            single_tick_data = self.get_single_tick_data(address, list_of_word_position)
            for tick, liquidity_net, liquidity_gross in single_tick_data:
                self.tick_data[address][tick] = {
                    "liquidity_net": liquidity_net,
                    "liquidity_gross": liquidity_gross,
                    "block_number": block_number,
                }


def get_sqrt_ratio_at_tick(tick: int) -> int:
    abs_tick = abs(tick)
    assert 0 <= abs_tick <= MAX_TICK, "TICK_OUT_OF_RANGE"

    ratio = (
        0xFFFCB933BD6FAD37AA2D162D1A594001
        if (abs_tick & 0x1 != 0)
        else 0x100000000000000000000000000000000
    )

    if abs_tick & 0x2 != 0:
        ratio = (ratio * 0xFFF97272373D413259A46990580E213A) >> 128
    if abs_tick & 0x4 != 0:
        ratio = (ratio * 0xFFF2E50F5F656932EF12357CF3C7FDCC) >> 128
    if abs_tick & 0x8 != 0:
        ratio = (ratio * 0xFFE5CACA7E10E4E61C3624EAA0941CD0) >> 128
    if abs_tick & 0x10 != 0:
        ratio = (ratio * 0xFFCB9843D60F6159C9DB58835C926644) >> 128
    if abs_tick & 0x20 != 0:
        ratio = (ratio * 0xFF973B41FA98C081472E6896DFB254C0) >> 128
    if abs_tick & 0x40 != 0:
        ratio = (ratio * 0xFF2EA16466C96A3843EC78B326B52861) >> 128
    if abs_tick & 0x80 != 0:
        ratio = (ratio * 0xFE5DEE046A99A2A811C461F1969C3053) >> 128
    if abs_tick & 0x100 != 0:
        ratio = (ratio * 0xFCBE86C7900A88AEDCFFC83B479AA3A4) >> 128
    if abs_tick & 0x200 != 0:
        ratio = (ratio * 0xF987A7253AC413176F2B074CF7815E54) >> 128
    if abs_tick & 0x400 != 0:
        ratio = (ratio * 0xF3392B0822B70005940C7A398E4B70F3) >> 128
    if abs_tick & 0x800 != 0:
        ratio = (ratio * 0xE7159475A2C29B7443B29C7FA6E889D9) >> 128
    if abs_tick & 0x1000 != 0:
        ratio = (ratio * 0xD097F3BDFD2022B8845AD8F792AA5825) >> 128
    if abs_tick & 0x2000 != 0:
        ratio = (ratio * 0xA9F746462D870FDF8A65DC1F90E061E5) >> 128
    if abs_tick & 0x4000 != 0:
        ratio = (ratio * 0x70D869A156D2A1B890BB3DF62BAF32F7) >> 128
    if abs_tick & 0x8000 != 0:
        ratio = (ratio * 0x31BE135F97D08FD981231505542FCFA6) >> 128
    if abs_tick & 0x10000 != 0:
        ratio = (ratio * 0x9AA508B5B7A84E1C677DE54F3E99BC9) >> 128
    if abs_tick & 0x20000 != 0:
        ratio = (ratio * 0x5D6AF8DEDB81196699C329225EE604) >> 128
    if abs_tick & 0x40000 != 0:
        ratio = (ratio * 0x2216E584F5FA1EA926041BEDFE98) >> 128
    if abs_tick & 0x80000 != 0:
        ratio = (ratio * 0x48A170391F7DC42444E8FA2) >> 128

    if tick > 0:
        MAX_UINT256 = 2**256 - 1
        ratio = (MAX_UINT256) // ratio

    # this divides by 1<<32 rounding up to go from a Q128.128 to a Q128.96
    # we then downcast because we know the result always fits within 160 bits due to our tick input constraint
    # we round up in the division so getTickAtSqrtRatio of the output price is always consistent
    return (ratio >> 32) + (0 if (ratio % (1 << 32) == 0) else 1)


def get_tick_at_sqrt_ratio(sqrt_price_x96: int) -> int:
    def gt(x, y):
        return 1 if x > y else 0

    def mod(x, y):
        return 0 if y == 0 else x % y

    def mul(x, y):
        return x * y

    def shl(x, y):
        return y << x

    def shr(x, y):
        return y >> x

    def or_(x, y):
        return x | y

    assert 0 <= sqrt_price_x96 <= 2**160 - 1, "Not a valid uint160"

    # second inequality must be < because the price can never reach the price at the max tick
    assert sqrt_price_x96 >= MIN_SQRT_RATIO and sqrt_price_x96 < MAX_SQRT_RATIO, "R"

    ratio = sqrt_price_x96 << 32

    r: int = ratio
    msb: int = 0

    f = shl(7, gt(r, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF))
    msb = or_(msb, f)
    r = shr(f, r)

    f = shl(7, gt(r, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF))
    msb = or_(msb, f)
    r = shr(f, r)

    f = shl(6, gt(r, 0xFFFFFFFFFFFFFFFF))
    msb = or_(msb, f)
    r = shr(f, r)

    f = shl(5, gt(r, 0xFFFFFFFF))
    msb = or_(msb, f)
    r = shr(f, r)

    f = shl(4, gt(r, 0xFFFF))
    msb = or_(msb, f)
    r = shr(f, r)

    f = shl(3, gt(r, 0xFF))
    msb = or_(msb, f)
    r = shr(f, r)

    f = shl(2, gt(r, 0xF))
    msb = or_(msb, f)
    r = shr(f, r)

    f = shl(1, gt(r, 0x3))
    msb = or_(msb, f)
    r = shr(f, r)

    f = gt(r, 0x1)
    msb = or_(msb, f)

    if msb >= 128:
        r = ratio >> (msb - 127)
    else:
        r = ratio << (127 - msb)

    log_2 = (int(msb) - 128) << 64

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(63, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(62, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(61, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(60, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(59, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(58, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(57, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(56, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(55, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(54, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(53, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(52, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(51, f))
    r = shr(f, r)

    r = shr(127, mul(r, r))
    f = shr(128, r)
    log_2 = or_(log_2, shl(50, f))

    log_sqrt10001 = log_2 * 255738958999603826347141  # 128.128 number

    tick_low = (log_sqrt10001 - 3402992956809132418596140100660247210) >> 128
    tick_high = (log_sqrt10001 + 291339464771989622907027621153398088495) >> 128

    tick = (
        tick_low
        if (tick_low == tick_high)
        else (
            tick_high
            if get_sqrt_ratio_at_tick(tick_high) <= sqrt_price_x96
            else tick_low
        )
    )

    return tick


def compute_swap_step(
    sqrt_ratio_current_x96: int,
    sqrt_ratio_target_x96: int,
    liquidity: int,
    amount_remaining: int,
    fee_pips: int,
) -> Tuple[int, int, int, int]:
    zeroForOne: bool = sqrt_ratio_current_x96 >= sqrt_ratio_target_x96
    exact_in: bool = amount_remaining >= 0
    amount_in = 0
    amount_out = 0
    if exact_in:
        amount_remaining_less_fee: int = (amount_remaining * (10**6 - fee_pips)) // (
            10**6
        )
        amount_in = (
            get_amount0_delta(
                sqrt_ratio_target_x96, sqrt_ratio_current_x96, liquidity, True
            )
            if zeroForOne
            else get_amount1_delta(
                sqrt_ratio_current_x96, sqrt_ratio_target_x96, liquidity, True
            )
        )

        if amount_remaining_less_fee >= amount_in:
            sqrt_ratio_next_x96 = sqrt_ratio_target_x96
        else:
            sqrt_ratio_next_x96 = get_next_sqrt_price_from_output(
                sqrt_ratio_current_x96,
                liquidity,
                amount_remaining_less_fee,
                zeroForOne,
            )
    else:
        amount_out = (
            get_amount1_delta(
                sqrt_ratio_target_x96, sqrt_ratio_current_x96, liquidity, False
            )
            if zeroForOne
            else get_amount0_delta(
                sqrt_ratio_current_x96, sqrt_ratio_target_x96, liquidity, False
            )
        )
        if -amount_remaining >= amount_out:
            sqrt_ratio_next_x96 = sqrt_ratio_target_x96
        else:
            sqrt_ratio_next_x96 = get_next_sqrt_price_from_output(
                sqrt_ratio_current_x96,
                liquidity,
                -amount_remaining,
                zeroForOne,
            )

    max: bool = sqrt_ratio_target_x96 == sqrt_ratio_next_x96
    # get the input/output amounts
    if zeroForOne:
        amount_in = (
            amount_in
            if (max and exact_in)
            else get_amount0_delta(
                sqrt_ratio_next_x96, sqrt_ratio_current_x96, liquidity, True
            )
        )
        amount_out = (
            amount_out
            if (max and not exact_in)
            else get_amount1_delta(
                sqrt_ratio_next_x96, sqrt_ratio_current_x96, liquidity, False
            )
        )
    else:
        amount_in = (
            amount_in
            if (max and exact_in)
            else get_amount1_delta(
                sqrt_ratio_current_x96, sqrt_ratio_next_x96, liquidity, True
            )
        )
        amount_out = (
            amount_out
            if (max and not exact_in)
            else get_amount0_delta(
                sqrt_ratio_current_x96, sqrt_ratio_next_x96, liquidity, False
            )
        )
    # cap the output amount to not exceed the remaining output amount
    if not exact_in and (amount_out > -amount_remaining):
        amount_out = -amount_remaining

    if exact_in and (sqrt_ratio_next_x96 != sqrt_ratio_target_x96):
        # we didn't reach the target, so take the remainder of the maximum input as fee
        fee_amount = amount_remaining - amount_in
    else:
        fee_amount = mul_div_rounding_up(amount_in, fee_pips, 10**6 - fee_pips)

    return (
        sqrt_ratio_next_x96,
        amount_in,
        amount_out,
        fee_amount,
    )


def mul_div_rounding_up(a: int, b: int, denominator: int):
    MIN_UINT256 = 0
    MAX_UINT256 = 2**256 - 1
    result: int = (a * b) // denominator
    if (a * b) % denominator > 0:
        # must be less than max uint256 since we're rounding up
        assert MIN_UINT256 <= result < MAX_UINT256, "FAIL!"
        result += 1
    return result


def div_rounding_up(x, y) -> int:
    def gt(x, y):
        return 1 if x > y else 0

    def div(x, y):
        return 0 if y == 0 else x // y

    def mod(x, y):
        return 0 if y == 0 else x % y

    return div(x, y) + gt(mod(x, y), 0)


def get_amount0_delta(
    sqrt_Ratio0_x96: int,
    sqrt_Ratio1_x96: int,
    liquidity: int,
    round_up: Optional[bool] = None,
) -> int:
    MIN_UINT128 = 0
    MAX_UINT128 = 2**128 - 1
    Q96_RESOLUTION = 96
    if round_up is not None or MIN_UINT128 <= liquidity <= MAX_UINT128:
        if sqrt_Ratio0_x96 > sqrt_Ratio1_x96:
            sqrt_Ratio0_x96, sqrt_Ratio1_x96 = sqrt_Ratio1_x96, sqrt_Ratio0_x96

        numerator1 = liquidity << Q96_RESOLUTION
        numerator2 = sqrt_Ratio1_x96 - sqrt_Ratio0_x96
        assert sqrt_Ratio0_x96 > 0, "require sqrt_Ratio0_x96 > 0"

        return (
            div_rounding_up(
                mul_div_rounding_up(numerator1, numerator2, sqrt_Ratio1_x96),
                sqrt_Ratio0_x96,
            )
            if round_up
            else ((numerator1 * numerator2) // sqrt_Ratio1_x96) // sqrt_Ratio0_x96
        )
    else:
        if liquidity < 0:
            return -get_amount0_delta(
                sqrt_Ratio0_x96, sqrt_Ratio1_x96, -liquidity, False
            )
        else:
            return get_amount0_delta(sqrt_Ratio0_x96, sqrt_Ratio1_x96, liquidity, True)


def get_amount1_delta(
    sqrt_ratio0_x96: int,
    sqrt_ratio1_x96: int,
    liquidity: int,
    round_up: Optional[bool] = None,
) -> int:
    MIN_UINT128 = 0
    MAX_UINT128 = 2**128 - 1
    Q96 = 2**96
    if round_up is not None or MIN_UINT128 <= liquidity <= MAX_UINT128:
        if sqrt_ratio0_x96 > sqrt_ratio1_x96:
            sqrt_ratio0_x96, sqrt_ratio1_x96 = sqrt_ratio1_x96, sqrt_ratio0_x96

        return (
            mul_div_rounding_up(liquidity, sqrt_ratio1_x96 - sqrt_ratio0_x96, Q96)
            if round_up
            else (liquidity * (sqrt_ratio1_x96 - sqrt_ratio0_x96)) // Q96
        )
    else:
        if liquidity < 0:
            return -get_amount1_delta(
                sqrt_ratio0_x96, sqrt_ratio1_x96, -liquidity, False
            )
        else:
            return get_amount1_delta(sqrt_ratio0_x96, sqrt_ratio1_x96, liquidity, True)


def get_next_sqrt_price_from_amount1_rounding_down(
    sqrtPX96: int,
    liquidity: int,
    amount: int,
    add: bool,
) -> int:
    Q96_RESOLUTION = 96
    Q96 = 2**Q96_RESOLUTION
    if add:
        quotient = (
            (amount << Q96_RESOLUTION) // liquidity
            if amount <= 2**160 - 1
            else (amount * Q96) // liquidity
        )
        return sqrtPX96 + quotient
    else:
        quotient = (
            div_rounding_up(amount << Q96_RESOLUTION, liquidity)
            if amount <= (2**160) - 1
            else mul_div_rounding_up(amount, Q96, liquidity)
        )
        assert sqrtPX96 > quotient, "PRICE_MOVE_LIMIT_EXCEEDED"

        # always fits 160 bits
        return sqrtPX96 - quotient


def get_next_sqrt_price_from_amount0_rounding_up(
    sqrtPX96: int,
    liquidity: int,
    amount: int,
    add: bool,
) -> int:
    Q96_RESOLUTION = 96
    # we short circuit amount == 0 because the result is otherwise not guaranteed to equal the input price
    if amount == 0:
        return sqrtPX96

    numerator1 = liquidity << Q96_RESOLUTION

    if add:
        product = amount * sqrtPX96
        if product // amount == sqrtPX96:
            denominator = numerator1 + product
            if denominator >= numerator1:
                # always fits in 160 bits
                return mul_div_rounding_up(numerator1, sqrtPX96, denominator)
        return div_rounding_up(numerator1, numerator1 // sqrtPX96 + amount)
    else:
        product = amount * sqrtPX96
        # if the product overflows, we know the denominator underflows
        # in addition, we must check that the denominator does not underflow

        assert (
            product // amount == sqrtPX96 and numerator1 > product
        ), "product / amount == sqrtPX96 && numerator1 > product"

        denominator = numerator1 - product
        return mul_div_rounding_up(numerator1, sqrtPX96, denominator)


def get_next_sqrt_price_from_output(
    sqrtPX96: int,
    liquidity: int,
    amountOut: int,
    zeroForOne: bool,
):
    # round to make sure that we pass the target price
    return (
        get_next_sqrt_price_from_amount0_rounding_up(
            sqrtPX96, liquidity, amountOut, True
        )
        if zeroForOne
        else get_next_sqrt_price_from_amount1_rounding_down(
            sqrtPX96, liquidity, amountOut, True
        )
    )
