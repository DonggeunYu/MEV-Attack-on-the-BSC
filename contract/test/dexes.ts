import { network, ethers } from 'hardhat';

import { expect } from 'chai';
import { transferFrom, decimals } from '../utils/token';
import path from 'path';

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

describe('Dexes Swap', function () {
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

  describe('uniswapV2Swap', function () {
    async function testUniswapV2Swap(data: any, fee: bigint = 0n) {
      const POOL_ADDRESS = data['POOL_ADDRESS'];
      const TOKEN_IN_ADDRESS = data['TOKEN_IN_ADDRESS'];
      const TOKEN_OUT_ADDRESS = data['TOKEN_OUT_ADDRESS'];
      const amountIn = BigInt(10n ** (await decimals(TOKEN_IN_ADDRESS)));
      const halfAmountIn = amountIn / BigInt(2);

      await transferFrom(TOKEN_IN_ADDRESS, contractAddress, amountIn);

      const tokenInContractForHolder = new ethers.Contract(TOKEN_IN_ADDRESS, IERC20ABI, owner);
      await expect(
        contract._uniswapV2Swap(POOL_ADDRESS, contractAddress, TOKEN_IN_ADDRESS, TOKEN_OUT_ADDRESS, halfAmountIn),
      ).to.changeTokenBalances(
        tokenInContractForHolder,
        [POOL_ADDRESS, contractAddress],
        [(halfAmountIn * (10000n - fee)) / 10000n, -halfAmountIn],
      );

      const uniswapV2PairContract = new ethers.Contract(POOL_ADDRESS, IUniswapV2PairABI, owner);
      await expect(
        contract._uniswapV2Swap(POOL_ADDRESS, contractAddress, TOKEN_IN_ADDRESS, TOKEN_OUT_ADDRESS, halfAmountIn),
      ).to.emit(uniswapV2PairContract, 'Swap');
    }

    it('UniswapV2', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['UNISWAP_V2']);
    });

    it('SushiswapV2', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['SUSHISWAP_V2']);
    });

    (chainID == 56 ? it : it.skip)('PancakeSwapV2', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['PANCAKESWAP_V2']);
    });

    (chainID == 56 ? it : it.skip)('THENA', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['THENA'], 20n);
    });

    (chainID == 56 ? it : it.skip)('BiswapV2', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['BISWAP_V2']);
    });

    (chainID == 56 ? it : it.skip)('ApeSwap', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['APESWAP']);
    });

    (chainID == 56 ? it : it.skip)('MDEX', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['MDEX']);
    });

    (chainID == 56 ? it : it.skip)('BabySwap', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['BABYSWAP']);
    });

    (chainID == 56 ? it : it.skip)('Nomiswap', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['NOMISWAP']);
    });

    (chainID == 56 ? it : it.skip)('WaultSwap', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['WAULTSWAP']);
    });

    (chainID == 56 ? it : it.skip)('GIBXSwap', async () => {
      await testUniswapV2Swap(VARIABLE['UNISWAP_V2_SWAP']['GIBXSWAP']);
    });
  });

  describe('uniswapV3Swap', function () {
    async function testUniswapV3Swap(data: any, dex: string) {
      const poolAddress = data['POOL_ADDRESS'];
      const tokenInAddress = data['TOKEN_IN_ADDRESS'];
      const tokenOutAddress = data['TOKEN_OUT_ADDRESS'];
      const amountIn = BigInt(10n ** (await decimals(tokenInAddress)));
      const halfAmountIn = amountIn / BigInt(2);

      await transferFrom(tokenInAddress, contractAddress, amountIn);

      const tokenInContractForHolder = new ethers.Contract(tokenInAddress, IERC20ABI, owner);
      await expect(
        contract._uniswapV3Swap(poolAddress, contractAddress, tokenInAddress, tokenOutAddress, halfAmountIn),
      ).to.changeTokenBalances(tokenInContractForHolder, [poolAddress, contractAddress], [halfAmountIn, -halfAmountIn]);

      let uniswapV3PairContract;
      if (dex === 'UniswapV3' || dex === 'SushiswapV3') {
        uniswapV3PairContract = new ethers.Contract(poolAddress, IUniswapV3PoolABI, owner);
      } else if (dex === 'PancakeSwapV3') {
        uniswapV3PairContract = new ethers.Contract(poolAddress, IPancakeV3PoolABI, owner);
      } else if (dex === 'THENAFUSION') {
        uniswapV3PairContract = new ethers.Contract(poolAddress, IAlgebraPoolABI, owner);
      } else {
        throw new Error('Unsupported dex');
      }
      await expect(
        contract._uniswapV3Swap(poolAddress, contractAddress, tokenInAddress, tokenOutAddress, halfAmountIn),
      ).to.emit(uniswapV3PairContract, 'Swap');
    }

    it('UniswapV3', async () => {
      await testUniswapV3Swap(VARIABLE['UNISWAP_V3_SWAP']['UNISWAP_V3'], 'UniswapV3');
    });

    (chainID == 1 ? it : it.skip)('SushiswapV3', async () => {
      await testUniswapV3Swap(VARIABLE['UNISWAP_V3_SWAP']['SUSHISWAP_V3'], 'SushiswapV3');
    });

    it('PancakeSwapV3', async () => {
      await testUniswapV3Swap(VARIABLE['UNISWAP_V3_SWAP']['PANCAKESWAP_V3'], 'PancakeSwapV3');
    });

    (chainID == 56 ? it : it.skip)('THENA FUSION', async () => {
      await testUniswapV3Swap(VARIABLE['UNISWAP_V3_SWAP']['THENA_FUSION'], 'THENAFUSION');
    });
  });

  (chainID == 56 ? describe : describe.skip)('BakerySwap', function () {
    async function testBakerySwap(data: any, fee: bigint = 0n) {
      const POOL_ADDRESS = data['POOL_ADDRESS'];
      const TOKEN_IN_ADDRESS = data['TOKEN_IN_ADDRESS'];
      const TOKEN_OUT_ADDRESS = data['TOKEN_OUT_ADDRESS'];
      const amountIn = BigInt(10n ** (await decimals(TOKEN_IN_ADDRESS)));
      const halfAmountIn = amountIn / BigInt(2);

      await transferFrom(TOKEN_IN_ADDRESS, contractAddress, amountIn);

      const tokenInContractForHolder = new ethers.Contract(TOKEN_IN_ADDRESS, IERC20ABI, owner);
      await expect(
        contract._bakerySwap(
          POOL_ADDRESS,
          contractAddress,
          contractAddress,
          TOKEN_IN_ADDRESS,
          TOKEN_OUT_ADDRESS,
          halfAmountIn,
        ),
      ).to.changeTokenBalances(
        tokenInContractForHolder,
        [POOL_ADDRESS, contractAddress],
        [(halfAmountIn * (10000n - fee)) / 10000n, -halfAmountIn],
      );

      const uniswapV2PairContract = new ethers.Contract(POOL_ADDRESS, IUniswapV2PairABI, owner);
      await expect(
        contract._bakerySwap(
          POOL_ADDRESS,
          contractAddress,
          contractAddress,
          TOKEN_IN_ADDRESS,
          TOKEN_OUT_ADDRESS,
          halfAmountIn,
        ),
      ).to.emit(uniswapV2PairContract, 'Swap');
    }

    it('BakerySwap', async () => {
      await testBakerySwap(VARIABLE['BAKERY_SWAP']['BAKERYSWAP']);
    });
  });

  (chainID == 1 ? describe : describe.skip)('Curve', function () {
    async function testCurve(data: any, funcName: string) {
      const poolAddress = data['POOL_ADDRESS'];
      const tokenInAddress = data['TOKEN_IN_ADDRESS'];
      const tokenOutAddress = data['TOKEN_OUT_ADDRESS'];
      const amountIn = BigInt(10n ** (await decimals(tokenInAddress)));
      const halfAmountIn = amountIn / BigInt(2);

      await transferFrom(tokenInAddress, contractAddress, amountIn);

      let func;
      let curveContract;
      let expectedEventName = '';
      if (funcName === 'curveStableSwapInterface1Plain') {
        func = contract._curveStableSwapInterface1Plain;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchange';
      } else if (funcName === 'curveStableSwapInterface1Underlying') {
        func = contract._curveStableSwapInterface1Underlying;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchangeUnderlying';
      } else if (funcName === 'curveStableSwapInterface2Plain') {
        func = contract._curveStableSwapInterface2Plain;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchange';
      } else if (funcName === 'curveStableSwapInterface2Underlying') {
        func = contract._curveStableSwapInterface2Underlying;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchangeUnderlying';
      } else if (funcName === 'curveStableSwapInterface2MetaPoolPlain') {
        func = contract._curveStableSwapInterface2MetaPoolPlain;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchange';
      } else if (funcName === 'curveStableSwapInterface2MetaPoolUnderlying') {
        func = contract._curveStableSwapInterface2MetaPoolUnderlying;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchangeUnderlying';
      } else if (funcName === 'curveStableSwapNGPlain') {
        func = contract._curveStableSwapNGPlain;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchange';
      } else if (funcName === 'curveStableSwapNGMetaPoolPlain') {
        func = contract._curveStableSwapNGMetaPoolPlain;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchange';
      } else if (funcName === 'curveStableSwapNGMetaPoolUnderlying') {
        func = contract._curveStableSwapNGMetaPoolUnderlying;
        curveContract = new ethers.Contract(poolAddress, ICurveStableSwapABI, owner);
        expectedEventName = 'TokenExchangeUnderlying';
      } else if (funcName === 'curveCryptoSwap') {
        func = contract._curveCryptoSwap;
        curveContract = new ethers.Contract(poolAddress, ICurveCryptoSwapABI, owner);
        expectedEventName = 'TokenExchange';
      } else {
        throw new Error('Unsupported function name');
      }

      const tokenInContractForHolder = new ethers.Contract(tokenInAddress, IERC20ABI, owner);
      await func(poolAddress, tokenInAddress, tokenOutAddress, halfAmountIn);

      await expect(func(poolAddress, tokenInAddress, tokenOutAddress, halfAmountIn)).to.emit(
        curveContract,
        expectedEventName,
      );
    }

    it('StableSwap Interface1 Plain', async () => {
      await testCurve(VARIABLE['CURVE']['CURVE_STABLE_SWAP_INTERFACE1_PLAIN'], 'curveStableSwapInterface1Plain');
    });

    it('StableSwap Interface1 Underlying', async () => {
      await testCurve(
        VARIABLE['CURVE']['CURVE_STABLE_SWAP_INTERFACE1_UNDERLYING'],
        'curveStableSwapInterface1Underlying',
      );
    });

    it('StableSwap Interface2 Plain', async () => {
      await testCurve(VARIABLE['CURVE']['CURVE_STABLE_SWAP_INTERFACE2_PLAIN'], 'curveStableSwapInterface2Plain');
    });

    it('StableSwap Interface2 Underlying', async () => {
      await testCurve(
        VARIABLE['CURVE']['CURVE_STABLE_SWAP_INTERFACE2_UNDERLYING'],
        'curveStableSwapInterface2Underlying',
      );
    });

    it('StableSwap Interface2 MetaPool Plain', async () => {
      await testCurve(
        VARIABLE['CURVE']['CURVE_STABLE_SWAP_INTERFACE2_META_POOL_PLAIN'],
        'curveStableSwapInterface2MetaPoolPlain',
      );
    });

    it('StableSwap Interface2 MetaPool Underlying', async () => {
      await testCurve(
        VARIABLE['CURVE']['CURVE_STABLE_SWAP_INTERFACE2_META_POOL_UNDERLYING'],
        'curveStableSwapInterface2MetaPoolUnderlying',
      );
    });

    it('StableSwap-NG Plain', async () => {
      await testCurve(VARIABLE['CURVE']['CURVE_STABLE_SWAP_NG_PLAIN'], 'curveStableSwapNGPlain');
    });

    it('StableSwap-NG MetaPool Plain', async () => {
      await testCurve(VARIABLE['CURVE']['CURVE_STABLE_SWAP_NG_META_POOL_PLAIN'], 'curveStableSwapNGMetaPoolPlain');
    });

    it('StableSwap-NG MetaPool Underlying', async () => {
      await testCurve(
        VARIABLE['CURVE']['CURVE_STABLE_SWAP_NG_META_POOL_UNDERLYING'],
        'curveStableSwapNGMetaPoolUnderlying',
      );
    });

    it('CryptoSwap', async () => {
      await testCurve(VARIABLE['CURVE']['CURVE_CRYPTO_SWAP'], 'curveCryptoSwap');
    });

    it('TwoCrypto-NG', async () => {
      await testCurve(VARIABLE['CURVE']['CURVE_TWO_CRYPTO_SWAP'], 'curveCryptoSwap');
    });

    it('TriCrypto-NG', async () => {
      await testCurve(VARIABLE['CURVE']['CURVE_TRI_CRYPTO_SWAP'], 'curveCryptoSwap');
    });
  });
});
