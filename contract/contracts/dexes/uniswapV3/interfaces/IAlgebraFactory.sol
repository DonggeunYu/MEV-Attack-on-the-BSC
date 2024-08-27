// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

interface IAlgebraFactory {
    function poolByPair(address tokenA, address tokenB) external view returns (address pool);
}
