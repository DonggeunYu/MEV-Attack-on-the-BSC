import {ethers} from 'hardhat';

async function main() {
    await ethers.provider.send("evm_mine");
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
