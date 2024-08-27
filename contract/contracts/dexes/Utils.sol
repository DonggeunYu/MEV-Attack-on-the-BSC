// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

contract Utils {
  // UniswapV2, SushiswapV2, PancakeSwapV2, THENA, BiswapV2, ApeSwap, MDEX, BabySwap, Nomiswap, WaultSwap
  // GibXSwap
  uint8[] uniswapV2SwapArray = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  // UniswapV3, SushiswapV3, PancakeSwapV3, THENA FUSION
  uint8[] uniswapV3SwapArray = [11, 12, 13, 14];
  uint8[] possibleFromAddress = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15];
  uint8[] possibleToAddress = [11, 12, 13, 14];

  function isUniswapV2(uint8 dexId) internal view returns (bool) {
    return numExistInArray(dexId, uniswapV2SwapArray);
  }

  function isUniswapV3(uint8 dexId) internal view returns (bool) {
    return numExistInArray(dexId, uniswapV3SwapArray);
  }

  function isPossibleFromAddress(uint8 dexId) internal view returns (bool) {
    return numExistInArray(dexId, possibleFromAddress);
  }

  function isPossibleToAddress(uint8 dexId) internal view returns (bool) {
    return numExistInArray(dexId, possibleToAddress);
  }

  function numExistInArray(uint8 num, uint8[] memory array) internal pure returns (bool) {
    for (uint i = 0; i < array.length; i++) {
      if (array[i] == num) {
        return true;
      }
    }
    return false;
  }
}
