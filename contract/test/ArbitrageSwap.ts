import { network, ethers } from 'hardhat';

import { expect } from 'chai';
import { transferFrom, decimals } from '../utils/token';
import path from 'path';
import { dex2id, dex2name } from '../utils/dex2id';
import { operationSushiswapV3Pool, operationUniswapV2Pool, operationUniswapV3Pool } from '../utils/swap';

const IERC20ABI = require('../utils/abi/IERC20.json').abi;
const IUniswapV2PairABI = require('../utils/abi/IUniswapV2Pair.json').abi;
const IUniswapV3PoolABI = require('../utils/abi/IUniswapV3Pool.json').abi;
const IPancakeV3PoolABI = require('../utils/abi/IPancakeV3Pool.json').abi;
const IAlgebraPoolABI = require('../utils/abi/IAlgebraPool.json').abi;
const ICurveStableSwapABI = require('../utils/abi/ICurveStableSwap.json').abi;
const ICurveCryptoSwapABI = require('../utils/abi/ICurveCryptoSwap.json').abi;

const chainAddressVariables: Record<number, any> = {
  1: require(path.resolve('test/variable_by_chain/eth.json')),
  56: require(path.resolve('test/variable_by_chain/bsc.json')),
};

const chainID = network.config.chainId !== undefined ? network.config.chainId : 0;
const VARIABLE =
  chainAddressVariables[chainID] ||
  (() => {
    throw new Error('Unsupported chainID');
  })();

describe('ArbitrageSwap', function () {
  let contract: any;
  let contractAddress: string;

  let owner: any;
  before(async () => {
    [owner] = await ethers.getSigners();

    if (chainID == 1) {
      const ExchangeSwap = await ethers.getContractFactory('_ETH');
      contract = await ExchangeSwap.deploy();
    } else if (chainID == 56) {
      const ExchangeSwap = await ethers.getContractFactory('_BSC');
      contract = await ExchangeSwap.deploy();
    } else {
      throw new Error('Unsupported chainID');
    }
    await contract.waitForDeployment();
    contractAddress = await contract.getAddress();
  });

  let snapshotId: string;
  beforeEach(async () => {
    snapshotId = await network.provider.send('evm_snapshot');
  });

  afterEach(async () => {
    await network.provider.send('evm_revert', [snapshotId]);
  });

  (chainID == 56 ? describe : describe.skip)('withdrawProfitWithBloxroute', function () {
    it('withdrawProfitWithBloxroute', async function () {
      await transferFrom(VARIABLE['WRAPPED_NATIVE_TOKEN_ADDRESS'], contractAddress, 10n ** 18n);
      const beforeMSGSenderBalance = await ethers.provider.getBalance(owner.address);
      const beforeBloxrouteBalance = await ethers.provider.getBalance('0x965Df5Ff6116C395187E288e5C87fb96CfB8141c');
      const tokenInContract = new ethers.Contract(VARIABLE['WRAPPED_NATIVE_TOKEN_ADDRESS'], IERC20ABI, owner);
      await expect(contract._withdrawProfitWithBloxroute({value: 10n ** 17n})).to.changeTokenBalance(
        tokenInContract,
        contract,
        -(10n ** 18n),
      );
      const afterMSGSenderBalance = await ethers.provider.getBalance(owner.address);
      expect(afterMSGSenderBalance).to.equal(beforeMSGSenderBalance);
      const afterBloxrouteBalance = await ethers.provider.getBalance('0x965Df5Ff6116C395187E288e5C87fb96CfB8141c');
      expect(afterBloxrouteBalance).to.equal(beforeBloxrouteBalance + 10n ** 17n);
    });
  });

  describe('multiHopArbitrage', function () {
    async function testMultiHopArbitrage(data: any[], exchanges: any, operationTarget: string) {
      const OPERATION_TARGET_ROUTER_ADDRESS = data.at(-1)['ROUTER_ADDRESS'];
      const OPERATION_TARGET_POOL_ADDRESS = data.at(-1)['POOL_ADDRESS'];
      const OPERATION_TARGET_TOKEN_ADDRESSES = [data.at(-1)['TOKEN_IN_ADDRESS'], data.at(-1)['TOKEN_OUT_ADDRESS']];
      const POOL_ADDRESSES = data.map((d: any) => d['POOL_ADDRESS']);
      let TOKEN_ADDRESSES: any[] = [];
      for (let i = 0; i < data.length; i++) {
        if (i % 2 == 0) {
          TOKEN_ADDRESSES.push(data[i]['TOKEN_IN_ADDRESS']);
        } else {
          TOKEN_ADDRESSES.push(data[i]['TOKEN_OUT_ADDRESS']);
        }
      }
      TOKEN_ADDRESSES.push(data.length % 2 == 0 ? data.at(-1)['TOKEN_IN_ADDRESS'] : data.at(-1)['TOKEN_OUT_ADDRESS']);
      const amountIn = BigInt(10n ** ((await decimals(data.at(-1)['TOKEN_IN_ADDRESS'])) / 2n));

      if (operationTarget === 'UniswapV2') {
        await operationUniswapV2Pool(
          OPERATION_TARGET_ROUTER_ADDRESS,
          OPERATION_TARGET_POOL_ADDRESS,
          OPERATION_TARGET_TOKEN_ADDRESSES,
        );
      } else if (operationTarget === 'UniswapV3') {
        await operationUniswapV3Pool(
          OPERATION_TARGET_ROUTER_ADDRESS,
          OPERATION_TARGET_POOL_ADDRESS,
          OPERATION_TARGET_TOKEN_ADDRESSES,
        );
      } else if (operationTarget === 'SuhsiswapV3' || operationTarget === 'PancakeSwapV3') {
        await operationSushiswapV3Pool(
          OPERATION_TARGET_ROUTER_ADDRESS,
          OPERATION_TARGET_POOL_ADDRESS,
          OPERATION_TARGET_TOKEN_ADDRESSES,
        );
      }
      //await transferFrom(TOKEN_IN_ADDRESS, TOKEN_IN_HOLDER, contractAddress, amountIn);
      await contract.multiHopArbitrageWithBloxroute(0, amountIn, exchanges, POOL_ADDRESSES, TOKEN_ADDRESSES, {value:10n ** 1n});
    }

    const TEST_CASE = VARIABLE['MultiHop'];
    for (const key in TEST_CASE) {
      for (let i = 0; i < TEST_CASE[key]['TEST_CASE'].length; i++) {
        const titile = TEST_CASE[key]['TEST_CASE'][i].map((dex: string) => dex2name(dex)).join('->');

        const exchanges = TEST_CASE[key]['TEST_CASE'][i].map((d: any) => dex2id(d));
        let data: any[] = [];
        let operationTarget = '';
        for (let j = 0; j < TEST_CASE[key]['TEST_CASE'][i].length; j++) {
          if (TEST_CASE[key]['TEST_CASE'][i][j] in VARIABLE['UNISWAP_V2_SWAP']) {
            data.push(VARIABLE['UNISWAP_V2_SWAP'][TEST_CASE[key]['TEST_CASE'][i][j]]);
            operationTarget = 'UniswapV2';
          }
          if (TEST_CASE[key]['TEST_CASE'][i][j] in VARIABLE['UNISWAP_V3_SWAP']) {
            data.push(VARIABLE['UNISWAP_V3_SWAP'][TEST_CASE[key]['TEST_CASE'][i][j]]);
            if (TEST_CASE[key]['TEST_CASE'][i][j] === 'UNISWAP_V3') {
              operationTarget = 'UniswapV3';
            } else if (TEST_CASE[key]['TEST_CASE'][i][j] === 'SUSHISWAP_V3') {
              operationTarget = 'SuhsiswapV3';
            } else if (TEST_CASE[key]['TEST_CASE'][i][j] === 'PANCAKESWAP_V3') {
              operationTarget = 'PancakeSwapV3';
            }
          }
        }

        it(`${titile}`, async () => {
          await testMultiHopArbitrage(data, exchanges, operationTarget);
        });
      }
    }
  });

  describe('optimizedArbitrageUniswapV2UniswapV2FlashSwap', function () {
    async function testOptimizedArbitrageUniswapV2UniswapV2FlashSwap(
      firstPoolInfo: any,
      secondPoolInfo: any,
      exchanges: any,
    ) {
      const OPERATION_TARGET_ROUTER_ADDRESS = secondPoolInfo['ROUTER_ADDRESS'];
      const OPERATION_TARGET_POOL_ADDRESS = secondPoolInfo['POOL_ADDRESS'];
      const OPERATION_TARGET_TOKEN_ADDRESSES = [
        secondPoolInfo['TOKEN_IN_ADDRESS'],
        secondPoolInfo['TOKEN_OUT_ADDRESS'],
      ];
      const TOKEN_IN_HOLDER = firstPoolInfo['TOKEN_IN_HOLDER'];
      const TOKEN_IN_ADDRESS = firstPoolInfo['TOKEN_IN_ADDRESS'];
      const EXCHANGES = exchanges;
      const POOL_ADDRESSES = [firstPoolInfo['POOL_ADDRESS'], secondPoolInfo['POOL_ADDRESS']];
      const TOKEN_ADDRESSES = [firstPoolInfo['TOKEN_IN_ADDRESS'], firstPoolInfo['TOKEN_OUT_ADDRESS']];
      const amountIn = BigInt(10n ** ((await decimals(firstPoolInfo['TOKEN_IN_ADDRESS'])) / 2n));

      await operationUniswapV2Pool(
        OPERATION_TARGET_ROUTER_ADDRESS,
        OPERATION_TARGET_POOL_ADDRESS,
        OPERATION_TARGET_TOKEN_ADDRESSES,
      );

      //await transferFrom(TOKEN_IN_ADDRESS, TOKEN_IN_HOLDER, contractAddress, amountIn);

      const tokenInContractForHolder = new ethers.Contract(TOKEN_IN_ADDRESS, IERC20ABI, owner);
      await contract.optimizedArbitrageUniswapV2UniswapV2FlashSwap(
        amountIn,
        POOL_ADDRESSES[0],
        POOL_ADDRESSES[1],
        TOKEN_ADDRESSES[0],
        TOKEN_ADDRESSES[1],
      );
    }

    const TEST_CASE = VARIABLE['MultiHop']['UniswapV2UniswapV2']['TEST_CASE'];
    for (let i = 0; i < TEST_CASE.length; i++) {
      it(`${dex2name(TEST_CASE[i][0])}->${dex2name(TEST_CASE[i][1])}`, async () => {
        const firstPoolInfo = VARIABLE['UNISWAP_V2_SWAP'][TEST_CASE[i][0]];
        const secondPoolInfo = VARIABLE['UNISWAP_V2_SWAP'][TEST_CASE[i][1]];
        const exchanges = [dex2id(TEST_CASE[i][0]), dex2id(TEST_CASE[i][1])];
        await testOptimizedArbitrageUniswapV2UniswapV2FlashSwap(firstPoolInfo, secondPoolInfo, exchanges);
      });
    }
  });

  describe('optimizedArbitrageUniswapV2UniswapV3FlashSwap', function () {
    async function testOptimizedArbitrageUniswapV2UniswapV3FlashSwap(
      firstPoolInfo: any,
      secondPoolInfo: any,
      exchanges: any,
    ) {
      const OPERATION_TARGET_ROUTER_ADDRESS = firstPoolInfo['ROUTER_ADDRESS'];
      const OPERATION_TARGET_POOL_ADDRESS = firstPoolInfo['POOL_ADDRESS'];
      const OPERATION_TARGET_TOKEN_ADDRESSES = [firstPoolInfo['TOKEN_OUT_ADDRESS'], firstPoolInfo['TOKEN_IN_ADDRESS']];
      const TOKEN_IN_HOLDER = firstPoolInfo['TOKEN_IN_HOLDER'];
      const TOKEN_IN_ADDRESS = firstPoolInfo['TOKEN_IN_ADDRESS'];
      const EXCHANGES = exchanges;
      const POOL_ADDRESSES = [firstPoolInfo['POOL_ADDRESS'], secondPoolInfo['POOL_ADDRESS']];
      const TOKEN_ADDRESSES = [firstPoolInfo['TOKEN_IN_ADDRESS'], firstPoolInfo['TOKEN_OUT_ADDRESS']];
      const amountIn = BigInt(10n ** ((await decimals(firstPoolInfo['TOKEN_IN_ADDRESS'])) / 2n));

      await operationUniswapV2Pool(
        OPERATION_TARGET_ROUTER_ADDRESS,
        OPERATION_TARGET_POOL_ADDRESS,
        OPERATION_TARGET_TOKEN_ADDRESSES,
      );

      //await transferFrom(TOKEN_IN_ADDRESS, TOKEN_IN_HOLDER, contractAddress, amountIn);

      const tokenInContractForHolder = new ethers.Contract(TOKEN_IN_ADDRESS, IERC20ABI, owner);
      await contract.optimizedArbitrageUniswapV2UniswapV3FlashSwap(
        amountIn,
        POOL_ADDRESSES[0],
        POOL_ADDRESSES[1],
        TOKEN_ADDRESSES[0],
        TOKEN_ADDRESSES[1],
      );
    }

    const TEST_CASE = VARIABLE['MultiHop']['UniswapV2UniswapV3']['TEST_CASE'];
    for (let i = 0; i < TEST_CASE.length; i++) {
      it(`${dex2name(TEST_CASE[i][0])}->${dex2name(TEST_CASE[i][1])}`, async () => {
        const firstPoolInfo = VARIABLE['UNISWAP_V2_SWAP'][TEST_CASE[i][0]];
        const secondPoolInfo = VARIABLE['UNISWAP_V3_SWAP'][TEST_CASE[i][1]];
        const exchanges = [dex2id(TEST_CASE[i][0]), dex2id(TEST_CASE[i][1])];
        await testOptimizedArbitrageUniswapV2UniswapV3FlashSwap(firstPoolInfo, secondPoolInfo, exchanges);
      });
    }
  });

  describe('optimizedArbitrageUniswapV3UniswapV2FlashSwap', function () {
    async function testOptimizedArbitrageUniswapV3UniswapV2FlashSwap(
      firstPoolInfo: any,
      secondPoolInfo: any,
      exchanges: any,
    ) {
      const OPERATION_TARGET_ROUTER_ADDRESS = secondPoolInfo['ROUTER_ADDRESS'];
      const OPERATION_TARGET_POOL_ADDRESS = secondPoolInfo['POOL_ADDRESS'];
      const OPERATION_TARGET_TOKEN_ADDRESSES = [
        secondPoolInfo['TOKEN_IN_ADDRESS'],
        secondPoolInfo['TOKEN_OUT_ADDRESS'],
      ];
      const TOKEN_IN_HOLDER = firstPoolInfo['TOKEN_IN_HOLDER'];
      const TOKEN_IN_ADDRESS = firstPoolInfo['TOKEN_IN_ADDRESS'];
      const EXCHANGES = exchanges;
      const POOL_ADDRESSES = [firstPoolInfo['POOL_ADDRESS'], secondPoolInfo['POOL_ADDRESS']];
      const TOKEN_ADDRESSES = [firstPoolInfo['TOKEN_IN_ADDRESS'], firstPoolInfo['TOKEN_OUT_ADDRESS']];
      const amountIn = BigInt(10n ** ((await decimals(firstPoolInfo['TOKEN_IN_ADDRESS'])) / 2n));

      await operationUniswapV2Pool(
        OPERATION_TARGET_ROUTER_ADDRESS,
        OPERATION_TARGET_POOL_ADDRESS,
        OPERATION_TARGET_TOKEN_ADDRESSES,
      );

      //await transferFrom(TOKEN_IN_ADDRESS, TOKEN_IN_HOLDER, contractAddress, amountIn);

      const tokenInContractForHolder = new ethers.Contract(TOKEN_IN_ADDRESS, IERC20ABI, owner);
      await contract.optimizedArbitrageUniswapV3UniswapV2FlashSwap(
        amountIn,
        POOL_ADDRESSES[0],
        POOL_ADDRESSES[1],
        TOKEN_ADDRESSES[0],
        TOKEN_ADDRESSES[1],
      );
    }

    const TEST_CASE = VARIABLE['MultiHop']['UniswapV3UniswapV2']['TEST_CASE'];
    for (let i = 0; i < TEST_CASE.length; i++) {
      it(`${dex2name(TEST_CASE[i][0])}->${dex2name(TEST_CASE[i][1])}`, async () => {
        const firstPoolInfo = VARIABLE['UNISWAP_V3_SWAP'][TEST_CASE[i][0]];
        const secondPoolInfo = VARIABLE['UNISWAP_V2_SWAP'][TEST_CASE[i][1]];
        const exchanges = [dex2id(TEST_CASE[i][0]), dex2id(TEST_CASE[i][1])];
        await testOptimizedArbitrageUniswapV3UniswapV2FlashSwap(firstPoolInfo, secondPoolInfo, exchanges);
      });
    }
  });

  describe('optimizedArbitrageUniswapV3UniswapV3FlashSwap', function () {
    async function testOptimizedArbitrageUniswapV3UniswapV3FlashSwap(
      firstPoolInfo: any,
      secondPoolInfo: any,
      exchanges: any,
    ) {
      const OPERATION_TARGET_ROUTER_ADDRESS = secondPoolInfo['ROUTER_ADDRESS'];
      const OPERATION_TARGET_POOL_ADDRESS = secondPoolInfo['POOL_ADDRESS'];
      const OPERATION_TARGET_TOKEN_ADDRESSES = [
        secondPoolInfo['TOKEN_IN_ADDRESS'],
        secondPoolInfo['TOKEN_OUT_ADDRESS'],
      ];
      const TOKEN_IN_HOLDER = firstPoolInfo['TOKEN_IN_HOLDER'];
      const TOKEN_IN_ADDRESS = firstPoolInfo['TOKEN_IN_ADDRESS'];
      const EXCHANGES = exchanges;
      const POOL_ADDRESSES = [firstPoolInfo['POOL_ADDRESS'], secondPoolInfo['POOL_ADDRESS']];
      const TOKEN_ADDRESSES = [firstPoolInfo['TOKEN_IN_ADDRESS'], firstPoolInfo['TOKEN_OUT_ADDRESS']];
      const amountIn = BigInt(10n ** ((await decimals(firstPoolInfo['TOKEN_IN_ADDRESS'])) / 2n));

      await operationUniswapV3Pool(
        OPERATION_TARGET_ROUTER_ADDRESS,
        OPERATION_TARGET_POOL_ADDRESS,
        OPERATION_TARGET_TOKEN_ADDRESSES,
      );

      //await transferFrom(TOKEN_IN_ADDRESS, TOKEN_IN_HOLDER, contractAddress, amountIn);

      const tokenInContractForHolder = new ethers.Contract(TOKEN_IN_ADDRESS, IERC20ABI, owner);
      await contract.optimizedArbitrageUniswapV3UniswapV3FlashSwap(
        amountIn,
        POOL_ADDRESSES[0],
        POOL_ADDRESSES[1],
        TOKEN_ADDRESSES[0],
        TOKEN_ADDRESSES[1],
      );
    }

    const TEST_CASE = VARIABLE['MultiHop']['UniswapV3UniswapV3']['TEST_CASE'];
    for (let i = 0; i < TEST_CASE.length; i++) {
      it(`${dex2name(TEST_CASE[i][0])}->${dex2name(TEST_CASE[i][1])}`, async () => {
        const firstPoolInfo = VARIABLE['UNISWAP_V3_SWAP'][TEST_CASE[i][0]];
        const secondPoolInfo = VARIABLE['UNISWAP_V3_SWAP'][TEST_CASE[i][1]];
        const exchanges = [dex2id(TEST_CASE[i][0]), dex2id(TEST_CASE[i][1])];
        await testOptimizedArbitrageUniswapV3UniswapV3FlashSwap(firstPoolInfo, secondPoolInfo, exchanges);
      });
    }
  });
});
