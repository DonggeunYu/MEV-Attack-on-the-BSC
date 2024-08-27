// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IERC20} from './safeERC20/IERC20.sol';
import {ISafeERC20} from './safeERC20/ISafeERC20.sol';
import {IUniswapV2Pair} from './dexes/uniswapV2/interfaces/IUniswapV2Pair.sol';
import {IUniswapV3Pool} from './dexes/uniswapV3/interfaces/IUniswapV3Pool.sol';
import {SwapCallBack} from './SwapCallBack.sol';
import {UniswapV3Constant} from './dexes/uniswapV3/libraries/UniswapV3Constant.sol';
import {INativeToken} from './interfaces/INativeToken.sol';

contract ArbitrageSwap is SwapCallBack {
    using ISafeERC20 for IERC20;
    address bloxrouteAddress = 0x74c5F8C6ffe41AD4789602BDB9a48E6Cad623520; // for fee send to bloxroute

    address private wrappedNativeAddress;
    constructor(uint chainID, address _wrappedNativeAddress) SwapCallBack(chainID) {
        wrappedNativeAddress = _wrappedNativeAddress;
    }

    address owner = msg.sender;
    modifier onlyOwner {
        require(msg.sender == owner, "Ownable: You are not the owner, Bye.");
        _;
    }


    function withdrawProfitWithBloxroute() internal {
        payable(bloxrouteAddress).transfer(msg.value);
    }

    receive() external payable {}



    function sandwichFrontRun(
        uint256 amountIn,
        uint8[] memory exchanges,
        address[] memory poolAddresses,
        address[] memory tokenAddresses
    ) external onlyOwner {
        address fromAddress = address(this);
        address toAddress;
        uint256 i = 0;
        for (; i < exchanges.length; i++) {
            if (
                i + 1 < exchanges.length && isPossibleToAddress(exchanges[i]) && isPossibleFromAddress(exchanges[i + 1])
            ) {
                toAddress = poolAddresses[i + 1];
            } else {
                toAddress = address(this);
            }
            amountIn = swap(exchanges[i], poolAddresses[i], fromAddress, toAddress, tokenAddresses[i], tokenAddresses[i + 1], amountIn);
            fromAddress = toAddress;
        }
    }

    function sandwichFrontRunDifficult(
        uint256 amountIn,
        uint8[] memory exchanges,
        address[] memory poolAddresses,
        address[] memory tokenAddresses,
        uint256 amountOut,
        uint256 poolBalance
    ) external onlyOwner {
        require(IERC20(tokenAddresses[tokenAddresses.length - 1]).balanceOf(poolAddresses[poolAddresses.length - 1]) == poolBalance, "SFRD: insufficient balance");
        address fromAddress = address(this);
        address toAddress;
        uint256 i = 0;
        for (; i < exchanges.length; i++) {
            if (
                // Can the current pool transfer tokens to the next pool, and can the next pool receive tokens from the previous pool.
                i + 1 < exchanges.length && isPossibleToAddress(exchanges[i]) && isPossibleFromAddress(exchanges[i + 1])
            ) {
                // If the above conditions are met, the next pool is set as the destination address.
                toAddress = poolAddresses[i + 1];
            } else {
                // If the above conditions are not met, the current contract is set as the destination address.
                toAddress = address(this);
            }
            amountIn = swap(exchanges[i], poolAddresses[i], fromAddress, toAddress, tokenAddresses[i], tokenAddresses[i + 1], amountIn);
            fromAddress = toAddress;
        }

        require(amountIn >= amountOut, "SFRD: amountIn <= amountOut");
    }

    function sandwichBackRunWithBloxroute(
        uint256 amountIn,
        uint8[] memory exchanges,
        address[] memory poolAddresses,
        address[] memory tokenAddresses
    ) external payable onlyOwner {
        _sandwichBackRun(amountIn, exchanges, poolAddresses, tokenAddresses);
        payable(bloxrouteAddress).transfer(msg.value);
    }

    function sandwichBackRun(
        uint256 amountIn,
        uint8[] memory exchanges,
        address[] memory poolAddresses,
        address[] memory tokenAddresses
    ) external onlyOwner {
        require(IERC20(tokenAddresses[tokenAddresses.length - 1]).balanceOf(address(this)) >= amountIn, "SandwichBackRun: insufficient balance");
        _sandwichBackRun(amountIn, exchanges, poolAddresses, tokenAddresses);
    }

    function sandwichBackRunDifficult(
        uint256 amountIn,
        uint8[] memory exchanges,
        address[] memory poolAddresses,
        address[] memory tokenAddresses,
        uint256 blockNumber
    ) external onlyOwner {
        require(block.number == blockNumber, "SandwichBackRunDifficult: block number is not correct");
        uint256 beforeBalance = IERC20(tokenAddresses[tokenAddresses.length - 1]).balanceOf(address(this));
        require(beforeBalance >= amountIn, "SandwichBackRunDifficult: insufficient balance");
        _sandwichBackRun(amountIn, exchanges, poolAddresses, tokenAddresses);
        if (tokenAddresses[0] == tokenAddresses[tokenAddresses.length - 1] &&
            IERC20(tokenAddresses[tokenAddresses.length - 1]).balanceOf(address(this)) < beforeBalance) {
            revert("SandwichBackRunDifficult: failed");
        }
    }

    function _sandwichBackRun(
        uint256 amountIn,
        uint8[] memory exchanges,
        address[] memory poolAddresses,
        address[] memory tokenAddresses
    ) internal {
        address fromAddress = address(this);
        address toAddress;
        // i to 1 from exchanges.length because underflow will occur
        for (uint256 i = exchanges.length; i > 0; i--) {
            if (
                i > 1 && isPossibleToAddress(exchanges[i - 1]) && isPossibleFromAddress(exchanges[i - 2])
            ) {
                toAddress = poolAddresses[i - 2];
            } else {
                toAddress = address(this);
            }
            amountIn = swap(exchanges[i - 1], poolAddresses[i - 1], fromAddress, toAddress, tokenAddresses[i], tokenAddresses[i - 1], amountIn);
            fromAddress = toAddress;
        }
    }
}
