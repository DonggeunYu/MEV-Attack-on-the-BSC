import {ethers} from 'hardhat';
import * as fs from 'fs';

async function main() {
    const lock = await ethers.deployContract('BSC', []);


}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
