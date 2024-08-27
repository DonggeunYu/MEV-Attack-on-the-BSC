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
            chainId: 56,
            chains: {
                56: {
                    hardforkHistory: {
                        london: 35490444
                    }
                }
            },
            mining: {
                auto: false,
                mempool: {
                    //order: 'fifo'
                }
            },
            gas: 21000000,
            forking: {
                url: 'https://go.getblock.io/',
                blockNumber: 38881874,
            },
            allowUnlimitedContractSize: true,
        },
        mainnet: {
            url: 'https://go.getblock.io/',
            chainId: 56,
            accounts: ["0x703c4b799f2137ce78e902484f674010d3dca796641bdc1224fd4a85f50404fb"]
        },
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
