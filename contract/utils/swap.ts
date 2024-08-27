import {expect} from "chai";
import {ethers, network} from "hardhat";
import {time} from "@nomicfoundation/hardhat-network-helpers";
import path from "path";

const IERC20ABI = require(path.resolve('utils/abi/IERC20.json')).abi;
const IUniswapV2RouterABI = require(path.resolve('utils/abi/IUniswapV2Router02.json')).abi;
const IUniswapV2PairABI = require(path.resolve('utils/abi/IUniswapV2Pair.json')).abi;
const IUniswapV3PoolABI = require(path.resolve('utils/abi/IUniswapV3Pool.json'),).abi;
const IUniswapV3RouterABI = require(path.resolve('utils/abi/IUniswapV3Router.json'),).abi;
const ISushiswapV3RouterABI = require(path.resolve('utils/abi/ISushiswapV3Router.json'),).abi;

const addressDead = "0x000000000000000000000000000000000000dEaD";
export async function uniswapV2Swap(uniswapV2RouterAddress: string, amount: bigint, poolAddress: string, path: string[]) {
    expect(path.length >= 2, 'UniswapV2Router: INVALID_PATH');
    network.provider.send('hardhat_setBalance', [path[0], '0x100000000000000000000']);
    const HolderSigner = await ethers.getSigner(path[0]);
    const TokenContractForHolder = new ethers.Contract(path[0], IERC20ABI, HolderSigner);
    const UniswapV2Router = new ethers.Contract(uniswapV2RouterAddress, IUniswapV2RouterABI, HolderSigner);

    await TokenContractForHolder.approve(poolAddress, amount);
    await TokenContractForHolder.approve(uniswapV2RouterAddress, amount);
    await UniswapV2Router.swapExactTokensForTokens(amount, 0, path, addressDead, (await time.latest()) + 1);
}

export async function uniswapV2GetAmountsOut(uniswapV2RouterAddress: string, amountIn: bigint, path: string[]) {
    expect(path.length >= 2, 'UniswapV2Router: INVALID_PATH');
    const UniswapV2Router = new ethers.Contract(uniswapV2RouterAddress, IUniswapV2RouterABI, ethers.provider);
    const amounts = await UniswapV2Router.getAmountsOut(amountIn, path);
    return amounts[1];
}

export async function uniswapV3Swap(uniswapV3RouterAddress: string, amount: bigint, poolAddress: string, path: string[], dex: string) {
    expect(path.length >= 2, 'UniswapV3Router: INVALID_PATH');
    network.provider.send('hardhat_setBalance', [path[0], '0x100000000000000000000']);
    const HolderSigner = await ethers.getImpersonatedSigner(path[0]);
    const TokenContractForHolder = new ethers.Contract(path[0], IERC20ABI, HolderSigner);

    let router;
    if (dex == "UniswapV3") {
        router = new ethers.Contract(uniswapV3RouterAddress, IUniswapV3RouterABI, HolderSigner);
    } else if (dex == "SushiswapV3") {
        router = new ethers.Contract(uniswapV3RouterAddress, ISushiswapV3RouterABI, HolderSigner);
    }
    await TokenContractForHolder.approve(poolAddress, amount);
    await TokenContractForHolder.approve(uniswapV3RouterAddress, amount);

    const UniswapV3Pool = new ethers.Contract(poolAddress, IUniswapV3PoolABI, HolderSigner);
    const fee = await UniswapV3Pool.fee();

    //Swap 함수 호출 후 교환된 토큰을 반환받아 저장
    const params = {
        tokenIn: path[0],
        tokenOut: path[1],
        fee: fee,
        recipient: addressDead,
        deadline: (await time.latest()) + 10,
        amountIn: amount,
        amountOutMinimum: 0,
        sqrtPriceLimitX96: 0,
    };
    await router.exactInputSingle(params);
}

export async function operationUniswapV2Pool(uniswapV2RouterAddress: string, poolAddress: string, path: string[]) {
    const HolderSigner = await ethers.getImpersonatedSigner(path[0]);
    const forgePairContract = new ethers.Contract(poolAddress, IUniswapV2PairABI, HolderSigner);
    const token0Address = await forgePairContract.token0();
    const token1Address = await forgePairContract.token1();

    let amount;
    if (token0Address.toLowerCase() === path[0].toLowerCase()) {
        const tokenContract = new ethers.Contract(token0Address, IERC20ABI, HolderSigner);
        amount = (await tokenContract.balanceOf(poolAddress)) / 50n;
    } else {
        const tokenContract = new ethers.Contract(token1Address, IERC20ABI, HolderSigner);
        amount = (await tokenContract.balanceOf(poolAddress)) / 50n;
    }

    await uniswapV2Swap(
        uniswapV2RouterAddress,
        amount,
        poolAddress,
        path,
    );
}

export async function operationUniswapV3Pool(uniswapV3RouterAddress: string, poolAddress: string, path: string[]) {
    const HolderSigner = await ethers.getImpersonatedSigner(path[0]);
    const forgePairContract = new ethers.Contract(poolAddress, IUniswapV3PoolABI, HolderSigner);
    const token0Address = await forgePairContract.token0();
    const token1Address = await forgePairContract.token1();

    let amount;
    if (token0Address.toLowerCase() == path[0].toLowerCase()) {
        const tokenContract = new ethers.Contract(token0Address, IERC20ABI, HolderSigner);
        amount = (await tokenContract.balanceOf(poolAddress)) / 100n;
    } else {
        const tokenContract = new ethers.Contract(token1Address, IERC20ABI, HolderSigner);
        amount = (await tokenContract.balanceOf(poolAddress)) / 100n;
    }

    await uniswapV3Swap(
        uniswapV3RouterAddress,
        amount,
        poolAddress,
        path,
        "UniswapV3"
    );
}

export async function operationSushiswapV3Pool(uniswapV3RouterAddress: string, poolAddress: string, path: string[]) {
    const HolderSigner = await ethers.getImpersonatedSigner(path[0]);
    const forgePairContract = new ethers.Contract(poolAddress, IUniswapV3PoolABI, HolderSigner);
    const token0Address = await forgePairContract.token0();
    const token1Address = await forgePairContract.token1();

    let amount;
    if (token0Address.toLowerCase() == path[0].toLowerCase()) {
        const tokenContract = new ethers.Contract(token0Address, IERC20ABI, HolderSigner);
        amount = (await tokenContract.balanceOf(poolAddress)) / 10n;
    } else {
        const tokenContract = new ethers.Contract(token1Address, IERC20ABI, HolderSigner);
        amount = (await tokenContract.balanceOf(poolAddress)) / 10n;
    }

    await uniswapV3Swap(
        uniswapV3RouterAddress,
        amount,
        poolAddress,
        path,
        "SushiswapV3"
    );
}
