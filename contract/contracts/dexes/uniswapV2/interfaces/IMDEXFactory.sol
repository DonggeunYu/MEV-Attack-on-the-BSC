// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

interface IMdexFactory {
    function getPairFees(address pair) external view returns (uint256);
}