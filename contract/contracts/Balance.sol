// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IERC20} from './safeERC20/IERC20.sol';
import {ISafeERC20} from './safeERC20/ISafeERC20.sol';

contract Balance {
    address public owner_balance = msg.sender;
    using ISafeERC20 for IERC20;

    function withdraw(address token, address to, uint256 amount) external {
        require(msg.sender == owner_balance, "only owner can withdraw");
        IERC20(token).safeTransfer(to, amount);
    }

    function deposit(address token, uint256 amount) external {
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
    }
}
