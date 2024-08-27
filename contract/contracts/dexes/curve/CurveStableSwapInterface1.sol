// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IERC20} from '../../safeERC20/IERC20.sol';
import {ISafeERC20} from '../../safeERC20/ISafeERC20.sol';
import {ICurveStableSwapPoolInterface1} from '../../interfaces/ICurvePool.sol';

contract CurveStableSwapInterface1 {
  using ISafeERC20 for IERC20;

  function curveStableSwapInterface1Plain(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    curveStableSwapInterface1(poolAddress, tokenIn, tokenOut, amountIn, false, false);
  }

  function curveStableSwapInterface1Underlying(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    curveStableSwapInterface1(poolAddress, tokenIn, tokenOut, amountIn, false, true);
  }

  function curveStableSwapInterface1(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn,
    bool isMetaPool,
    bool isUnderlying
  ) internal {
    IERC20(tokenIn).forceApprove(poolAddress, amountIn);

    ICurveStableSwapPoolInterface1 pool = ICurveStableSwapPoolInterface1(poolAddress);

    int128 tokenInIndex = -1;
    int128 tokenOutIndex = -1;
    function(int128) external view returns (address) coinsFunc;
    if (!isMetaPool && !isUnderlying) {
      coinsFunc = pool.coins;
    } else if (!isMetaPool && isUnderlying) {
      coinsFunc = pool.underlying_coins;
    } else if (isMetaPool && !isUnderlying) {
      coinsFunc = pool.coins;
    } else {
      revert('Invalid path');
    }

    for (int128 i = 0; i < 8; ++i) {
      try coinsFunc(i) returns (address tokenByIndex) {
        if (tokenByIndex == tokenIn) {
          tokenInIndex = i;
        } else if (tokenByIndex == tokenOut) {
          tokenOutIndex = i;
        }
      } catch {
        break;
      }
    }
    require(tokenInIndex != -1 && tokenOutIndex != -1, 'curveStableSwapInterface1: Invalid path');

    // Curve Poll not support return amountOut
    if (isUnderlying) {
      uint256 expectedAmountOut = pool.get_dy_underlying(tokenInIndex, tokenOutIndex, amountIn) - 1;
      pool.exchange_underlying(tokenInIndex, tokenOutIndex, amountIn, expectedAmountOut);
    } else {
      uint256 expectedAmountOut = pool.get_dy(tokenInIndex, tokenOutIndex, amountIn) - 1;
      pool.exchange(tokenInIndex, tokenOutIndex, amountIn, expectedAmountOut);
    }
  }
}
