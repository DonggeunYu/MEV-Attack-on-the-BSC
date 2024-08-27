import { HardhatUserConfig } from 'hardhat/config';
import 'hardhat-exposed/dist/type-extensions';
import '@nomicfoundation/hardhat-toolbox';
import '@nomicfoundation/hardhat-ethers';

require('hardhat-exposed');

const config: HardhatUserConfig = {
  solidity: {
        version: '0.8.20',
        settings: {
            optimizer: {
                enabled: true,
                runs: 100,
            },
            viaIR: true,
        },
    },
  networks: {
    hardhat: {
      chainId: 42161,
      gas: 21000000,
      forking: {
        url: 'https://arb-mainnet.g.alchemy.com/v2/AGuVoWLd4m5gYOggVk3itf-9wGn2okpp',
        blockNumber: 173057406,
      },
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
  },
  mocha: {
    timeout: 600000,
  },
};

export default config;
