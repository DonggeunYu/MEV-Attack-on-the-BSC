// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import {IERC20} from '../../safeERC20/IERC20.sol';
import {ISafeERC20} from '../../safeERC20/ISafeERC20.sol';
import {IUniswapV2Pair} from './interfaces/IUniswapV2Pair.sol';
import {IMdexFactory} from './interfaces/IMDEXFactory.sol';

contract UniswapV2 {
    using ISafeERC20 for IERC20;

    function uniswapV2Swap(
        address poolAddress,
        address fromAddress,
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) internal {
        bool zeroForOne = tokenIn < tokenOut;

        if (fromAddress == address(this)) {
            IERC20(tokenIn).safeTransfer(poolAddress, amountIn);
        }

        uint amountOut = getAmountOut(poolAddress, tokenIn, 0, zeroForOne);

        uint beforeSwap = IERC20(tokenOut).balanceOf(address(this));
        if (zeroForOne) {
            IUniswapV2Pair(poolAddress).swap(0, amountOut, address(this), '');
        } else {
            IUniswapV2Pair(poolAddress).swap(amountOut, 0, address(this), '');
        }
        uint amountOutReceived = IERC20(tokenOut).balanceOf(address(this)) - beforeSwap;
        require(amountOutReceived * 100 >= amountOut * 95, 'UniswapV2: Slippage too high');
    }

    function getAmountOut(
        address poolAddress,
        address tokenIn,
        uint256 amountIn,
        bool zeroForOne
    ) public view returns (uint amountOut) {
        (uint reserve0, uint reserve1,) = IUniswapV2Pair(poolAddress).getReserves();
        (uint reserveIn, uint reserveOut) = zeroForOne ? (reserve0, reserve1) : (reserve1, reserve0);

        if (amountIn == 0) {
            amountIn = IERC20(tokenIn).balanceOf(poolAddress) - reserveIn;
        }

        (uint n, uint s) = getNandS(poolAddress);
        if (n != 0) {
            uint k = reserveIn * reserveOut * n * n;
            uint balance_in_adj = (reserveIn + amountIn) * n - amountIn * s;
            uint balance_out_adj = (k + balance_in_adj - 1) / balance_in_adj;
            uint amountOut_max = reserveOut - ((balance_out_adj + n - 1) / n);
            return amountOut_max;
        } else {
            uint amountInWithFee = amountIn * 997;
            uint numerator = amountInWithFee * reserveOut;
            uint denominator = reserveIn * 1000 + amountInWithFee;
            amountOut = numerator / denominator;
            return amountOut;
        }
    }

    function getNandS(address poolAddress) public view returns (uint n, uint s) {
        try IUniswapV2Pair(poolAddress).factory() returns (address factoryAddress) {
            if (factoryAddress == 0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6) { // UniswapV2
                return (1000, 3);
            } else if (factoryAddress == 0xc35DADB65012eC5796536bD9864eD8773aBc74C4) { // SushiSwapV2
                return (1000, 3);
            } else if (factoryAddress == 0xBCfCcbde45cE874adCB698cC183deBcF17952812) { // PancakeSwapV1
                return (1000, 2);
            } else if (factoryAddress == 0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73) { // PancakeSwapV2
                return (10000, 25);
            } else if (factoryAddress == 0x858E3312ed3A876947EA49d572A7C42DE08af7EE) { // BiswapV2
                return (1000, uint(IUniswapV2Pair(poolAddress).swapFee()));
            } else if (factoryAddress == 0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6) { // ApeSwap
                return (1000, 2);
            } else if (factoryAddress == 0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8) { // MDEX
                return (1000, IMdexFactory(0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8).getPairFees(poolAddress));
            } else if (factoryAddress == 0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da) { // BabySwap
                return (1000, 2);
            } else if (factoryAddress == 0xd6715A8be3944ec72738F0BFDC739d48C3c29349) { // NomiSwap
                return (1000, uint(IUniswapV2Pair(poolAddress).swapFee()));
            } else if (factoryAddress == 0xB42E3FE71b7E0673335b3331B3e1053BD9822570) { // WaultSwap
                return (1000, 2);
            } else if (factoryAddress == 0x97bCD9BB482144291D77ee53bFa99317A82066E8) { // GIBXSwap
                return (1000, 3);
            }
            else {
                return (0, 0);
            }
        } catch { // THENA
            return (0, 0);
        }

    }
}
