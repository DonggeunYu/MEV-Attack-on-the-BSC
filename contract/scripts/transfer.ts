import {ethers, network} from 'hardhat';
import * as fs from 'fs';
import path from "path";

const IERC20ABI = require(path.resolve('utils/abi/IERC20.json'),).abi;
const IUniswapV2PairABI = require(path.resolve('utils/abi/IUniswapV2Pair.json'),).abi;
const IUniswapV3PoolABI = require(path.resolve('utils/abi/IUniswapV3Pool.json'),).abi;

import {uniswapV2Swap, uniswapV3Swap} from '../utils/swap.ts';
import {expect} from "chai";
import {time} from "@nomicfoundation/hardhat-network-helpers";

async function main() {
    await network.provider.send("evm_setAutomine", [true]);
    const tokenAddress = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c';
    const tokenHolderAddress = '0x8894e0a0c962cb723c1976a4421c95949be2d4e3';
    const spenderAddress = '0x7edfa77b21afd2a5d79cf5ce3ff3412da689108c';

      await hre.network.provider.request({
    method: "hardhat_impersonateAccount",
    params: [tokenHolderAddress],
  });
    network.provider.send('hardhat_setBalance', [tokenHolderAddress, '0x100000000000000000000']);

    const HolderSigner = await ethers.getSigner(tokenHolderAddress);
    const TokenContractForHolder = new ethers.Contract(tokenAddress, IERC20ABI, HolderSigner);
    await TokenContractForHolder.approve(spenderAddress, BigInt(10 ** 18 * 10));
    await TokenContractForHolder.transfer(spenderAddress, BigInt(10 ** 18 * 10));
    const amount = await TokenContractForHolder.balanceOf(spenderAddress);
    console.log(amount);
    await network.provider.send("evm_setAutomine", [false]);

}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
