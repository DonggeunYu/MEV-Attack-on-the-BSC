// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IERC20} from '../../safeERC20/IERC20.sol';
import {ISafeERC20} from '../../safeERC20/ISafeERC20.sol';
import {ICurveCryptoPool} from '../../interfaces/ICurvePool.sol';

contract CurveCryptoSwap {
  using ISafeERC20 for IERC20;

  function curveCryptoSwap(address poolAddress, address tokenIn, address tokenOut, uint256 amountIn) internal {
    IERC20(tokenIn).forceApprove(poolAddress, amountIn);

    ICurveCryptoPool pool = ICurveCryptoPool(poolAddress);

    uint256 tokenInIndex = 999;
    uint256 tokenOutIndex = 999;
    for (uint256 i = 0; i < 20; ++i) {
      try pool.coins(i) returns (address tokenByIndex) {
        if (tokenByIndex == tokenIn) {
          tokenInIndex = uint256(int(i));
        } else if (tokenByIndex == tokenOut) {
          tokenOutIndex = uint256(int(i));
        }
      } catch {
        break;
      }
    }
    require(tokenInIndex != 999 && tokenOutIndex != 999);

    // Curve Poll not support return amountOut
    uint256 expectedAmountOut = pool.get_dy(tokenInIndex, tokenOutIndex, amountIn) - 1;
    pool.exchange(tokenInIndex, tokenOutIndex, amountIn, expectedAmountOut);
  }
}
