// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

interface IUniswapV2Factory {
    function getPair(address token0, address token1) external view returns (address pair);
}
