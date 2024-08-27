// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;
import {ArbitrageSwap} from './ArbitrageSwap.sol';
import {Balance} from './Balance.sol';

contract BSC is ArbitrageSwap, Balance {

  constructor() ArbitrageSwap(56, 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c) {}
}
