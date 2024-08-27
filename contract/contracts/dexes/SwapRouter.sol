// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {UniswapV2} from './uniswapV2/UniswapV2.sol';
import {UniswapV3} from './uniswapV3/UniswapV3.sol';
import {BakerySwap} from './BakerySwap.sol';
import {IUniswapV2Pair} from './uniswapV2/interfaces/IUniswapV2Pair.sol';
import {IERC20} from '../safeERC20/IERC20.sol';
import {ISafeERC20} from '../safeERC20/ISafeERC20.sol';
import {CurveCryptoSwap} from './curve/CurveCryptoSwap.sol';
import {CurveStableSwapInterface1} from './curve/CurveStableSwapInterface1.sol';
import {CurveStableSwapInterface2} from './curve/CurveStableSwapInterface2.sol';
import {CurveStableSwapNG} from './curve/CurveStableSwapNG.sol';

import {Utils} from './Utils.sol';

contract SwapRouter is
  UniswapV2,
  UniswapV3,
  BakerySwap,
  Utils,
  CurveCryptoSwap,
  CurveStableSwapInterface1,
  CurveStableSwapInterface2,
  CurveStableSwapNG
{
  using ISafeERC20 for IERC20;

  function swap(
    uint8 dexId,
    address poolAddress,
    address fromAddress,
    address toAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal returns (uint256 amountOut) {
    amountOut = IERC20(tokenOut).balanceOf(toAddress);
    if (isUniswapV2(dexId)) {
      uniswapV2Swap(poolAddress, fromAddress, tokenIn, tokenOut, amountIn);
    } else if (isUniswapV3(dexId)) {
      uniswapV3Swap(poolAddress, toAddress, tokenIn, tokenOut, amountIn);
    } else if (dexId == 13) {
      bakerySwap(poolAddress, fromAddress, toAddress, tokenIn, tokenOut, amountIn);
    } else {
      revert('Invalid dexId');
    }

    amountOut = IERC20(tokenOut).balanceOf(toAddress) - amountOut;
  }
}
