// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import {IERC20} from '../safeERC20/IERC20.sol';
import {ISafeERC20} from '../safeERC20/ISafeERC20.sol';
import {IBakerySwap} from '../interfaces/IBakerySwap.sol';

contract BakerySwap {
    using ISafeERC20 for IERC20;

    function bakerySwap(
        address poolAddress,
        address fromAddress,
        address toAddress,
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) internal {
        bool zeroForOne = tokenIn < tokenOut;
        IBakerySwap pool = IBakerySwap(poolAddress);
        if (fromAddress == address(this)) {
            IERC20(tokenIn).safeTransfer(poolAddress, amountIn);
        }

        uint amountOut = bekarySwapGetAmountOut(poolAddress, tokenIn, zeroForOne);

        uint beforeSwap = IERC20(tokenOut).balanceOf(toAddress);
        if (zeroForOne) {
            pool.swap(0, amountOut, toAddress);
        } else {
            pool.swap(amountOut, 0, toAddress);
        }
        uint amountOutReceived = IERC20(tokenOut).balanceOf(toAddress) - beforeSwap;
        require(amountOutReceived * 100 >= amountOut * 95, 'UniswapV2: Slippage too high');
    }

    function bekarySwapGetAmountOut(
        address poolAddress,
        address tokenIn,
        bool zeroForOne
    ) private view returns (uint amountOut) {
        (uint reserve0, uint reserve1,) = IBakerySwap(poolAddress).getReserves();
        (uint reserveIn, uint reserveOut) = zeroForOne ? (reserve0, reserve1) : (reserve1, reserve0);
        uint amountIn = IERC20(tokenIn).balanceOf(poolAddress) - reserveIn;

        uint n = 1000;
        uint s = 3;
        uint k = reserveIn * reserveOut * n * n;
        uint balance_in_adj = (reserveIn + amountIn) * n - amountIn * s;
        uint balance_out_adj = (k + balance_in_adj - 1) / balance_in_adj;
        amountOut = reserveOut - ((balance_out_adj + n - 1) / n);
        return amountOut;
    }
}
