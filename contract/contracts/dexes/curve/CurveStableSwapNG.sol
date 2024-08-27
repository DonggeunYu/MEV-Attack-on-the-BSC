// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IERC20} from '../../safeERC20/IERC20.sol';
import {ISafeERC20} from '../../safeERC20/ISafeERC20.sol';
import {ICurveStablePoolNG} from '../../interfaces/ICurvePool.sol';

contract CurveStableSwapNG {
  using ISafeERC20 for IERC20;

  function curveStableSwapNGPlain(address poolAddress, address tokenIn, address tokenOut, uint256 amountIn) internal {
    curveStableSwapNG(poolAddress, tokenIn, tokenOut, amountIn, false, false);
  }

  function curveStableSwapNGMetaPoolPlain(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    curveStableSwapNG(poolAddress, tokenIn, tokenOut, amountIn, true, false);
  }

  function curveStableSwapNGMetaPoolUnderlying(
    address poolAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    curveStableSwapNG(poolAddress, tokenIn, tokenOut, amountIn, true, true);
  }

  function curveStableSwapNG(
    address poolAddress,
    address token0,
    address token1,
    uint256 amountIn,
    bool isMetaPool,
    bool isUnderlying
  ) internal {
    IERC20(token0).forceApprove(poolAddress, amountIn);

    ICurveStablePoolNG pool = ICurveStablePoolNG(poolAddress);

    int128 token0Index = -1;
    int128 token1Index = -1;
    function(uint256) external view returns (address) coinsFunc;
    if (!isMetaPool && !isUnderlying) {
      coinsFunc = pool.coins;
    } else if (isMetaPool && !isUnderlying) {
      coinsFunc = pool.coins;
    } else if (isMetaPool && isUnderlying) {
      coinsFunc = pool.BASE_COINS;
    } else {
      revert('Invalid path');
    }

    if (isMetaPool && isUnderlying) {
      int128 nCoins = 0;
      for (uint256 i = 0; i < 8; ++i) {
        try pool.coins(i) returns (address tokenByIndex) {
          nCoins++;
          if (tokenByIndex == token0) {
            token0Index = int128(int(i));
          } else if (tokenByIndex == token1) {
            token1Index = int128(int(i));
          }
        } catch {
          break;
        }
      }

      nCoins = nCoins - 1;

      for (uint256 i = 0; i < 8; ++i) {
        try coinsFunc(i) returns (address tokenByIndex) {
          if (tokenByIndex == token0) {
            token0Index = nCoins + int128(int(i));
          } else if (tokenByIndex == token1) {
            token1Index = nCoins + int128(int(i));
          }
        } catch {
          break;
        }
      }
    } else {
      for (uint256 i = 0; i < 8; ++i) {
        try coinsFunc(i) returns (address tokenByIndex) {
          if (tokenByIndex == token0) {
            token0Index = int128(int(i));
          } else if (tokenByIndex == token1) {
            token1Index = int128(int(i));
          }
        } catch {
          break;
        }
      }
    }
    require(token0Index != -1 && token1Index != -1, 'Invalid path');

    // Curve Poll not support return amountOut
    if (isUnderlying) {
      uint256 expectedAmountOut = pool.get_dy_underlying(token0Index, token1Index, amountIn) - 1;
      pool.exchange_underlying(token0Index, token1Index, amountIn, expectedAmountOut, address(this));
    } else {
      uint256 expectedAmountOut = pool.get_dy(token0Index, token1Index, amountIn) - 1;
      pool.exchange(token0Index, token1Index, amountIn, expectedAmountOut, address(this));
    }
  }
}
