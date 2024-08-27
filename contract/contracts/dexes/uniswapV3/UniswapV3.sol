// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IERC20} from '../../safeERC20/IERC20.sol';
import {ISafeERC20} from '../../safeERC20/ISafeERC20.sol';
import {IUniswapV3Pool} from './interfaces/IUniswapV3Pool.sol';
import {UniswapV3Constant} from './libraries/UniswapV3Constant.sol';

contract UniswapV3 {
  using ISafeERC20 for IERC20;

  function uniswapV3Swap(
    address poolAddress,
    address toAddress,
    address tokenIn,
    address tokenOut,
    uint256 amountIn
  ) internal {
    bool zeroForOne = tokenIn < tokenOut;
    uint160 sqrtPriceLimitX96 = zeroForOne ? UniswapV3Constant.MIN_SQRT_RATIO : UniswapV3Constant.MAX_SQRT_RATIO;
    bytes memory _data = abi.encode(tokenIn, zeroForOne);
    bytes memory data = abi.encode(uint(0), _data);
    IUniswapV3Pool(poolAddress).swap(toAddress, zeroForOne, int(amountIn), sqrtPriceLimitX96, data);
  }
}
