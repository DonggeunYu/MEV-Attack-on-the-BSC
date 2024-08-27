// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IERC20} from './safeERC20/IERC20.sol';
import {ISafeERC20} from './safeERC20/ISafeERC20.sol';
import {IUniswapV2Pair} from './dexes/uniswapV2/interfaces/IUniswapV2Pair.sol';
import {IUniswapV2Factory} from './dexes/uniswapV2/interfaces/IUniswapV2Factory.sol';
import {IUniswapV3Pool} from './dexes/uniswapV3/interfaces/IUniswapV3Pool.sol';
import {IUniswapV3Factory} from './dexes/uniswapV3/interfaces/IUniswapV3Factory.sol';
import {IAlgebraFactory} from './dexes/uniswapV3/interfaces/IAlgebraFactory.sol';
import {SwapRouter} from './dexes/SwapRouter.sol';

contract SwapCallBack is SwapRouter {
    using ISafeERC20 for IERC20;

    address private uniswapV2Factory;
    address private sushiswapV2Factory;
    address private pancakeSwapV1Factory;
    address private pancakeSwapV2Factory;
    address private thenaFactory;
    address private biswapFactory;
    address private apeswapFactory;
    address private mdexFactory;
    address private babyswapFactory;
    address private nomiswapFactory;
    address private waultSwapFactory;
    address private gibxFactory;
    address private uniswapV3Factory;
    address private pancakeSwapV3Factory;
    address private algebraswapFactory;
    constructor(uint chainID) {
        if (chainID == 56) {
            uniswapV2Factory = 0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6;
            sushiswapV2Factory = 0xc35DADB65012eC5796536bD9864eD8773aBc74C4;
            pancakeSwapV1Factory = 0xBCfCcbde45cE874adCB698cC183deBcF17952812;
            pancakeSwapV2Factory = 0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73;
            thenaFactory = 0x20a304a7d126758dfe6B243D0fc515F83bCA8431;
            biswapFactory = 0x858E3312ed3A876947EA49d572A7C42DE08af7EE;
            apeswapFactory = 0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6;
            mdexFactory = 0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8;
            babyswapFactory = 0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da;
            nomiswapFactory = 0xd6715A8be3944ec72738F0BFDC739d48C3c29349;
            waultSwapFactory = 0xB42E3FE71b7E0673335b3331B3e1053BD9822570;
            gibxFactory = 0x97bCD9BB482144291D77ee53bFa99317A82066E8;
            uniswapV3Factory = 0xdB1d10011AD0Ff90774D0C6Bb92e5C5c8b4461F7;
            pancakeSwapV3Factory = 0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865;
            algebraswapFactory = 0x306F06C147f064A010530292A1EB6737c3e378e4;
        }
    }

    // ============ UniswapV2 ============

    function uniswapV2Call(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        // UniswapV2, SushiswapV2
        if (_uniswapV2Verity(sushiswapV2Factory) || _uniswapV2Verity(uniswapV2Factory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function pancakeCall(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        // PancakeSwapV2, APESWAP
        if (_uniswapV2Verity(pancakeSwapV1Factory) || _uniswapV2Verity(pancakeSwapV2Factory) || _uniswapV2Verity(apeswapFactory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function hook(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        // THENA
        if (_uniswapV2Verity(thenaFactory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function BiswapCall(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        if (_uniswapV2Verity(biswapFactory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function swapV2Call(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        // MDEX
        if (_uniswapV2Verity(mdexFactory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function babyCall(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        // BabySwap
        if (_uniswapV2Verity(babyswapFactory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function nomiswapCall(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        // NomiSwap
        if (_uniswapV2Verity(nomiswapFactory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function waultSwapCall(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        // WaultSwap
        if (_uniswapV2Verity(waultSwapFactory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function gibxCall(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external {
        // GibX
        if (_uniswapV2Verity(gibxFactory)) {
            _uniswapV2Call(sender, amount0, amount1, data);
        }
    }

    function _uniswapV2Verity(address factoryAddress) internal view returns (bool) {
        IUniswapV2Pair pool = IUniswapV2Pair(msg.sender);
        address token0 = pool.token0();
        address token1 = pool.token1();
        IUniswapV2Factory factory = IUniswapV2Factory(factoryAddress);
        address pair = factory.getPair(token0, token1);
        return msg.sender == pair;
    }

    function _uniswapV2Call(address sender, uint256 amount0, uint256 amount1, bytes calldata data) internal {
        (uint8 _type, bytes memory data_) = abi.decode(data, (uint8, bytes));
        if (_type == 0) {
            (
                uint256 beforeBalance,
                uint256 amountIn,
                uint256 expectedAmountOut,
                uint8[] memory exchanges,
                address[] memory poolAddresses,
                address[] memory tokenAddresses
            ) = abi.decode(data_, (uint256, uint256, uint256, uint8[], address[], address[]));

            IUniswapV2Pair pool = IUniswapV2Pair(msg.sender);
            if (!(pool.token0() == tokenAddresses[0] || pool.token1() == tokenAddresses[0])) {
                revert('UniswapV2: INVALID_TOKEN');
            }

            uint256 i = 1;
            address toAddress;
            address fromAddress = address(this);
            uint256 amountOut = IERC20(tokenAddresses[1]).balanceOf(address(this)) - beforeBalance;
            require(amountOut * 100 >= expectedAmountOut * 95, 'UniswapV2: Slippage too high');

            for (; i < exchanges.length; i++) {
                if (i + 1 < exchanges.length && isPossibleToAddress(exchanges[i]) && isPossibleFromAddress(exchanges[i + 1])) {
                    toAddress = poolAddresses[i + 1];
                } else {
                    toAddress = address(this);
                }

                amountOut = swap(
                    exchanges[i],
                    poolAddresses[i],
                    fromAddress,
                    toAddress,
                    tokenAddresses[i],
                    tokenAddresses[i + 1],
                    amountOut
                );
                fromAddress = toAddress;
            }
            IERC20(tokenAddresses[0]).safeTransfer(msg.sender, amountIn);
        } else if (_type == 1) {
            (uint256 beforeBalance, uint256 amountIn, address poolAddress1, address token0, address token1) = abi.decode(
                data_,
                (uint256, uint256, address, address, address)
            );
            uint256 amountOut = IERC20(token0).balanceOf(address(this)) - beforeBalance;
            uniswapV2Swap(poolAddress1, address(this), token0, token1, amountOut);
            IERC20(token1).safeTransfer(msg.sender, amountIn);
        } else if (_type == 2) {
            (uint256 beforeBalance, uint256 amountIn, address poolAddress1, address token0, address token1) = abi.decode(
                data_,
                (uint256, uint256, address, address, address)
            );
            uint256 amountOut = IERC20(token0).balanceOf(address(this)) - beforeBalance;
            uniswapV3Swap(poolAddress1, address(this), token0, token1, amountOut);
            IERC20(token1).safeTransfer(msg.sender, amountIn);
        }
    }

    // ============ UniswapV3 ============

    function uniswapV3SwapCallback(int amount0, int amount1, bytes calldata data) external {
        if (_uniswapV3Verity(uniswapV3Factory)) {
            _uniswapV3SwapCallback(amount0, amount1, data);
        }
    }

    function pancakeV3SwapCallback(int amount0, int amount1, bytes calldata data) external {
        if (_uniswapV3Verity(pancakeSwapV3Factory)) {
            _uniswapV3SwapCallback(amount0, amount1, data);
        }
    }

    // THENA Fusion
    function algebraSwapCallback(int amount0, int amount1, bytes calldata data) external {
        if (_algebraVerity(algebraswapFactory)) {
            _uniswapV3SwapCallback(amount0, amount1, data);
        }
    }

    function _uniswapV3Verity(address factoryAddress) internal view returns (bool) {
        IUniswapV3Pool pool = IUniswapV3Pool(msg.sender);
        address token0 = pool.token0();
        address token1 = pool.token1();
        uint24 fee = pool.fee();
        IUniswapV3Factory factory = IUniswapV3Factory(factoryAddress);
        address pair = factory.getPool(token0, token1, fee);
        return msg.sender == pair;
    }

    function _algebraVerity(address factoryAddress) internal view returns (bool) {
        IUniswapV3Pool pool = IUniswapV3Pool(msg.sender);
        address token0 = pool.token0();
        address token1 = pool.token1();
        IAlgebraFactory factory = IAlgebraFactory(factoryAddress);
        address pair = factory.poolByPair(token0, token1);
        return msg.sender == pair;
    }

    function _uniswapV3SwapCallback(int amount0, int amount1, bytes calldata data) internal {
        (uint8 _type, bytes memory data_) = abi.decode(data, (uint8, bytes));

        if (_type == 0) {
            // Default UniswapV3
            (address tokenIn, bool zeroForOne) = abi.decode(data_, (address, bool));

            uint256 amountIn = zeroForOne ? uint256(amount0) : uint256(amount1);
            IERC20(tokenIn).safeTransfer(msg.sender, amountIn);
        } else if (_type == 1) {
            (
                uint256 beforeBalance,
                address fromAddress,
                uint256 amountIn,
                uint8[] memory exchanges,
                address[] memory poolAddresses,
                address[] memory tokenAddresses
            ) = abi.decode(data_, (uint256, address, uint256, uint8[], address[], address[]));

            IUniswapV3Pool pool = IUniswapV3Pool(msg.sender);
            if (!(pool.token0() == tokenAddresses[0] || pool.token1() == tokenAddresses[0])) {
                revert('UniswapV3: INVALID_TOKEN');
            }

            uint256 i = 1;
            address toAddress;
            uint256 amountOut = IERC20(tokenAddresses[1]).balanceOf(fromAddress) - beforeBalance;

            for (; i < exchanges.length; i++) {
                if (i + 1 < exchanges.length && isPossibleToAddress(exchanges[i]) && isPossibleFromAddress(exchanges[i + 1])) {
                    toAddress = poolAddresses[i + 1];
                } else {
                    toAddress = address(this);
                }
                amountOut = swap(
                    exchanges[i],
                    poolAddresses[i],
                    fromAddress,
                    toAddress,
                    tokenAddresses[i],
                    tokenAddresses[i + 1],
                    amountOut
                );
                fromAddress = toAddress;
            }

            IERC20(tokenAddresses[0]).safeTransfer(msg.sender, amountIn);
        } else if (_type == 2) {
            (uint256 beforeBalance, address fromAddress, uint256 amountIn, address tokenIn, address tokenOut) = abi.decode(
                data_,
                (uint256, address, uint256, address, address)
            );

            uint256 amountOut = IERC20(tokenIn).balanceOf(fromAddress) - beforeBalance;

            uniswapV2Swap(fromAddress, fromAddress, tokenIn, tokenOut, amountOut);
            IERC20(tokenOut).safeTransfer(msg.sender, amountIn);
        } else if (_type == 3) {
            (uint256 beforeBalance, address poolAddress, uint256 amountIn, address tokenIn, address tokenOut) = abi.decode(
                data_,
                (uint256, address, uint256, address, address)
            );

            uint256 amountOut = IERC20(tokenIn).balanceOf(address(this)) - beforeBalance;

            uniswapV3Swap(poolAddress, address(this), tokenIn, tokenOut, amountOut);
            IERC20(tokenOut).safeTransfer(msg.sender, amountIn);
        } else {
            revert('UniswapV3: INVALID_TOKEN');
        }
    }
}
