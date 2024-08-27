// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;
import {ArbitrageSwap} from './ArbitrageSwap.sol';
import {Balance} from './Balance.sol';

contract ETH is ArbitrageSwap, Balance{
  constructor() ArbitrageSwap(1, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2) {}
}
