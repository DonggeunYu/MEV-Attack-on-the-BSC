// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IERC20} from '../../safeERC20/IERC20.sol';
import {ISafeERC20} from '../../safeERC20/ISafeERC20.sol';
import {ICurveStableSwapPoolInterface2} from '../../interfaces/ICurvePool.sol';

contract CurveStableSwapInterface2 {
  using ISafeERC20 for IERC20;

  function curveStableSwapInterface2Plain(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    curveStableSwapInterface2(poolAddress, tokenIn, tokenOut, amountIn, false, false);
  }

  function curveStableSwapInterface2Underlying(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    curveStableSwapInterface2(poolAddress, tokenIn, tokenOut, amountIn, false, true);
  }

  function curveStableSwapInterface2MetaPoolPlain(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    curveStableSwapInterface2(poolAddress, tokenIn, tokenOut, amountIn, true, false);
  }

  function curveStableSwapInterface2MetaPoolUnderlying(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    curveStableSwapInterface2(poolAddress, tokenIn, tokenOut, amountIn, true, true);
  }

  function curveStableSwapInterface2(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn,
    bool isMetaPool,
    bool isUnderlying
  ) internal {
    IERC20(tokenIn).forceApprove(poolAddress, amountIn);
    ICurveStableSwapPoolInterface2 pool = ICurveStableSwapPoolInterface2(poolAddress);

    int128 tokenInIndex = -1;
    int128 tokenOutIndex = -1;
    function(uint256) external view returns (address) coinsFunc;
    if (!isMetaPool && !isUnderlying) {
      coinsFunc = pool.coins;
    } else if (!isMetaPool && isUnderlying) {
      coinsFunc = pool.underlying_coins;
    } else if (isMetaPool && !isUnderlying) {
      coinsFunc = pool.coins;
    } else if (isMetaPool && isUnderlying) {
      coinsFunc = pool.base_coins;
    } else {
      revert('Invalid path');
    }

    if (isMetaPool && isUnderlying) {
      int128 nCoins = 0;
      for (uint256 i = 0; i < 8; ++i) {
        try pool.coins(i) returns (address tokenByIndex) {
          nCoins++;
          if (tokenByIndex == tokenIn) {
            tokenInIndex = int128(int(i));
          } else if (tokenByIndex == tokenOut) {
            tokenOutIndex = int128(int(i));
          }
        } catch {
          break;
        }
      }

      nCoins = nCoins - 1;

      for (uint256 i = 0; i < 8; ++i) {
        try coinsFunc(i) returns (address tokenByIndex) {
          if (tokenByIndex == tokenIn) {
            tokenInIndex = nCoins + int128(int(i));
          } else if (tokenByIndex == tokenOut) {
            tokenOutIndex = nCoins + int128(int(i));
          }
        } catch {
          break;
        }
      }
    } else {
      for (uint256 i = 0; i < 8; ++i) {
        try coinsFunc(i) returns (address tokenByIndex) {
          if (tokenByIndex == tokenIn) {
            tokenInIndex = int128(int(i));
          } else if (tokenByIndex == tokenOut) {
            tokenOutIndex = int128(int(i));
          }
        } catch {
          break;
        }
      }
    }
    require(tokenInIndex != -1 && tokenOutIndex != -1);

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
