import {HardhatUserConfig} from 'hardhat/config';
import 'hardhat-exposed/dist/type-extensions';
import '@nomicfoundation/hardhat-toolbox';
import '@nomicfoundation/hardhat-ethers';

require('hardhat-exposed');
require("hardhat-gas-reporter");
require("@solidstate/hardhat-bytecode-exporter");

const config: HardhatUserConfig = {
    solidity: {
        version: '0.8.20',
        settings: {
            optimizer: {
                enabled: true,
                runs: 100,
            },
            viaIR: false,
        },
    },
    defaultNetwork: 'hardhat',
    networks: {
        hardhat: {
            chainId: 1,
            gas: 21000000,
            forking: {
                url: 'https://eth-mainnet.g.alchemy.com/v2/nYfATDWALLC6aLyyCrweNYFjkBxXSTlM',
                blockNumber: 19523856,
            },
        },
        mainnet: {
            url: 'https://eth-mainnet.g.alchemy.com/v2/nYfATDWALLC6aLyyCrweNYFjkBxXSTlM',
            chainId: 1,
            accounts: ["0x703c4b799f2137ce78e902484f674010d3dca796641bdc1224fd4a85f50404fb"]
        },
        "sepolia": {
            url: "https://eth-sepolia.g.alchemy.com/v2/OJ_kc5aBfDEgXWr1u8ah0LetcRU2oPuP",
            chainId: 11155111,
            accounts: ["49a6c1dab5db7e3b5aca37b1865a427610f84bebec04099e99ad6bc0ea8d7156"]
        }
    },
    paths: {
        sources: './contracts',
        tests: './test',
        cache: './cache',
        artifacts: './artifacts',
    },
    exposed: {
        outDir: 'contracts-exposed',
        prefix: '_',
    },
    mocha: {
        timeout: 600000,
    },
    gasReporter: {
        enabled: true,
        showMethodSig: true,
        currency: 'USD',
        gasPrice: 40,

        coinmarketcap: '87ae62f0-107e-426b-b938-f2bfb4d09c52'
    }
};

export default config;
