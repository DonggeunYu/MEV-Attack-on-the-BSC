import {ethers, network} from 'hardhat';
import * as fs from 'fs';
import path from "path";

const IERC20ABI = require(path.resolve('utils/abi/IERC20.json'),).abi;
const IUniswapV2PairABI = require(path.resolve('utils/abi/IUniswapV2Pair.json'),).abi;
const IUniswapV3PoolABI = require(path.resolve('utils/abi/IUniswapV3Pool.json'),).abi;

import {
    ThrowOffUniswapV2Pool,
    ThrowOffUniswapV3Pool,
    uniswapV2Swap,
    uniswapV3Swap
} from '../utils/swap.ts';
import {expect} from "chai";
import {time} from "@nomicfoundation/hardhat-network-helpers";

async function main() {
    const data = fs.readFileSync('/tmp/arbitrage_pool_operation.json', 'utf8');
    const poolOperation = JSON.parse(data);
    const exchanges = poolOperation.exchanges;
    const poolAddresses = poolOperation.poolAddresses;
    const tokenAddresses = poolOperation.tokenAddresses;
    const holderAddresses = poolOperation.holderAddresses;

    for (let i = 0; i < exchanges.length; i++) {
        if (i == 0) {
            await ThrowOffUniswapV2Pool('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', poolAddresses[i], tokenAddresses[i], holderAddresses[i]);
        } else if (i == 1) {
            await ThrowOffUniswapV3Pool(
                '0xE592427A0AEce92De3Edee1F18E0157C05861564', poolAddresses[i], tokenAddresses[i], holderAddresses[i]);
        }
        console.log('Executed operation for pool ' + poolAddresses[i] + ' with exchange ' + exchanges[i] + ' and holder ' + holderAddresses[i] + ' and token ' + tokenAddresses[i] + '.');
    }
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
