import {expect} from "chai";
import {ethers, network} from "hardhat";
import {time} from "@nomicfoundation/hardhat-network-helpers";
import path from "path";

const IERC20ABI = require('./abi/IERC20.json').abi;

export async function transferFrom(token: string, to: string, value: bigint) {
    network.provider.send('hardhat_setBalance', [token, '0x100000000000000000000']);

    const tokenHolderSigner = await ethers.getImpersonatedSigner(token);
    const tokenContractForTokenHolder = new ethers.Contract(token, IERC20ABI, tokenHolderSigner);

    let expectedValue: bigint;
    if (token === "0x59D9356E565Ab3A36dD77763Fc0d87fEaf85508C") {
        expectedValue = value - 1n;
    } else {
        expectedValue = value;
    }

    await expect(tokenContractForTokenHolder.transfer(to, value)).to.changeTokenBalances(tokenContractForTokenHolder, [token, to], [-expectedValue, expectedValue]);
}

export async function decimals(token: string) {
    const tokenContract = new ethers.Contract(token, IERC20ABI, ethers.provider);
    return BigInt(await tokenContract.decimals());
}
