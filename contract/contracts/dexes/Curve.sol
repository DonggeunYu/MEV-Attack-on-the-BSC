// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {CurveStableSwapInterface1} from './curve/CurveStableSwapInterface1.sol';
import {CurveStableSwapInterface2} from './curve/CurveStableSwapInterface2.sol';
import {CurveStableSwapNG} from './curve/CurveStableSwapNG.sol';
import {CurveCryptoSwap} from './curve/CurveCryptoSwap.sol';

contract Curve is CurveStableSwapInterface1, CurveStableSwapInterface2, CurveStableSwapNG, CurveCryptoSwap {}
