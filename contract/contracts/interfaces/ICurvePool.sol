// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

interface ICurveStableSwapPoolInterface1 {
  function coins(int128 arg0) external view returns (address);

  function base_coins(int128 arg0) external view returns (address);

  function underlying_coins(int128 arg0) external view returns (address);

  function exchange(int128 i, int128 j, uint256 dx, uint256 min_dy) external;

  function exchange_underlying(int128 i, int128 j, uint256 dx, uint256 min_dy) external;

  function get_dy(int128 i, int128 j, uint256 dx) external view returns (uint256);

  function get_dy_underlying(int128 i, int128 j, uint256 dx) external view returns (uint256);
}

interface ICurveStableSwapPoolInterface2 {
  function coins(uint256 i) external view returns (address);

  function base_coins(uint256 i) external view returns (address);

  function underlying_coins(uint256 i) external view returns (address);

  function exchange(int128 i, int128 j, uint256 dx, uint256 min_dy) external;

  function exchange_underlying(int128 i, int128 j, uint256 dx, uint256 min_dy) external;

  function get_dy(int128 i, int128 j, uint256 dx) external view returns (uint256);

  function get_dy_underlying(int128 i, int128 j, uint256 dx) external view returns (uint256);
}

interface ICurveStablePoolNG {
  function coins(uint256 arg0) external view returns (address);

  function BASE_COINS(uint256 arg0) external view returns (address);

  function exchange(int128 i, int128 j, uint256 _dx, uint256 _min_dy, address _receiver) external;

  function exchange_underlying(int128 i, int128 j, uint256 _dx, uint256 _min_dy, address _receiver) external;

  function get_dy(int128 i, int128 j, uint256 dx) external view returns (uint256);

  function get_dy_underlying(int128 i, int128 j, uint256 dx) external view returns (uint256);
}

interface ICurveCryptoPool {
  function coins(uint256 arg0) external view returns (address);

  function exchange(uint256 i, uint256 j, uint256 dx, uint256 min_dy) external;

  function get_dy(uint256 i, uint256 j, uint256 dx) external view returns (uint256);
}
