# MEV Attack on the BSC

<h4 align="center">
    <p>
        <b>English</b> |
                <a href="https://github.com/DonggeunYu/MEV-Attack-on-the-BSC/blob/main/README_ko.md">한국어</a>
    </p>
</h4>

## Overview
This repository implements how to profit from a Maximal Extractable Value (MEV) attack against a Decentralized Exchange (DEX) on the Binance Smart Chain (BSC) network.
- Since MEV development is directly tied to monetary gain, it's not easy to find resources that are actually helpful. I hope this resource will inspire other developers and add real value to their projects.
- The project was developed and operational from January 2024 to May 2024.
- For technical questions and feedback, please use the Issues page in the repository, and for all other inquiries, please contact ddonggeunn@gmail.com.

<br>
<br>
<br>

## Content
- [MEV Attack Bot on BSC](#mev-attack-bot-on-bsc)
  * [Overview](#overview)
  * [Content](#content)
  * [Transaction Sample for Sandwich Attack](#transaction-sample-for-sandwich-attack)
    + [Sandwich Attack used bloXroute](#sandwich-attack-used-bloxroute)
    + [Sandwich Attack used 48 Club](#sandwich-attack-used-48-club)
    + [Sandwich Attack used General](#sandwich-attack-used-general)
  * [Theoretical Explanation of MEV](#theoretical-explanation-of-mev)
    + [Acronym](#acronym)
    + [The Ideal Flow of the Expected Blockchain](#the-ideal-flow-of-the-expected-blockchain)
    + [Vulnerabilities of DEX Swap](#vulnerabilities-of-dex-swap)
    + [How to Protect from MEV Attacker](#how-to-protect-from-mev-attacker)
      - [Are the Block Proposer and Builder Separated?](#are-the-block-proposer-and-builder-separated-)
  * [Detailed Explanation of Source Code and Formulas](#detailed-explanation-of-source-code-and-formulas)
    + [Project Structure](#project-structure)
      - [Directory Structure](#directory-structure)
    + [IAC Tips](#iac-tips)
    + [About MEV-Relay](#about-mev-relay)
    + [Explain the Solidity Code](#explain-the-solidity-code)
      - [What is the difference between sandwichFrontRun and sandwichFrontRunDifficult?](#what-is-the-difference-between-sandwichfrontrun-and-sandwichfrontrundifficult-)
      - [About the BackRun Function](#about-the-backrun-function)
      - [Swap Router](#swap-router)
      - [Supported DEX List](#supported-dex-list)
      - [Solidity Test Code](#solidity-test-code)
    + [Explain the Python Code](#explain-the-python-code)
      - [Important Note](#important-note)
      - [Explain the Process in Writing](#explain-the-process-in-writing)
      - [Why is Arbitrage Only Used for General Path?](#why-is-arbitrage-only-used-for-general-path-)
      - [Trace Transaction](#trace-transaction)
    + [Formula Parts](#formula-parts)
      - [Reasons Why Understanding DEX AMM is Important](#reasons-why-understanding-dex-amm-is-important)
      - [Structure of Uniswap V2, V3](#structure-of-uniswap-v2--v3)
      - [Optimize the Uniswap V2 Swap to the Extreme](#optimize-the-uniswap-v2-swap-to-the-extreme)
        * [1. Uniswap V2 Amount Out Formula](#1-uniswap-v2-amount-out-formula)
        * [2. Analyze Uniswap V2 Swap](#2-analyze-uniswap-v2-swap)
        * [3. Optimization of Swap Formula](#3-optimization-of-swap-formula)
        * [4. Verification of the Formula Optimized to the Extreme](#4-verification-of-the-formula-optimized-to-the-extreme)
      - [Multi-hop Arbitrage Formula](#multi-hop-arbitrage-formula)
        * [1. 2-hop Arbitrage Formula](#1-2-hop-arbitrage-formula)
        * [2. Multi-hop Arbitrage Formula](#2-multi-hop-arbitrage-formula)
  * [EigenPhi is Overhyped](#eigenphi-is-overhyped)
    + [When Sandwich is Recognized as Arbitrage](#when-sandwich-is-recognized-as-arbitrage)
    + [When Doing Sandwich Using 48 Club](#when-doing-sandwich-using-48-club)
  * [Frequently Asked Questions](#frequently-asked-questions)
      - [Why you select the BSC network?](#why-you-select-the-bsc-network-)
      - [Do you plan to continue developing arbitrage or MEV in the future?](#do-you-plan-to-continue-developing-arbitrage-or-mev-in-the-future-)
  * [More Information](#more-information)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

<br>
<br>
<br>

## Transaction Sample for Sandwich Attack

### Sandwich Attack used bloXroute

|    Type   | Position | Transaction Hash                                                                                                                                                                                                                    | Transfer (WBNB) | MEV-Relay (BNB) | Transaction Fee (BNB) | Profit (BNB)     |
|:---------:|:--------:|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------|-----------------------|------------------|
| Front Run |     0    | 0.21913 WBNB<br> -> 0xE3...3E90C -> 35,489.53984 IRT <br> [0x906bf0f8bd71319bfb2938d6a07f29c823011d8d30a3afa306afb52773f38203](https://eigenphi.io/mev/eigentx/0x906bf0f8bd71319bfb2938d6a07f29c823011d8d30a3afa306afb52773f38203)  | -0.21913        |                 | -0.00013              |                  |
|   Victim  |     1    | 0.362844 WBNB  <br> -> 0xE3...3E90C -> 58,272.54022 IRT <br> [0x3f63df509a8708f75f7280a38ee7b70ac18817eb0c8c9d18c100d2dc73e48380](https://eigenphi.io/mev/eigentx/0x3f63df509a8708f75f7280a38ee7b70ac18817eb0c8c9d18c100d2dc73e48380)    |                 |                 |                       |                  |
|  Back Run |     2    | 35,489.53984 IRT <br> -> 0xE3...3E90C -> 0.22019 WBNB <br> [0x1737935a6ade5e3c0cbfa1fa2bb75dce27d3d1a7312e5b2c093bdab20cd369e0](https://eigenphi.io/mev/eigentx/0x1737935a6ade5e3c0cbfa1fa2bb75dce27d3d1a7312e5b2c093bdab20cd369e0) | +0.22019        | -0.00005        | -0.00077              |                  |
|           |          |                                                                                                                                                                                                                                     | +0.00106        | -0.00005        | -0.0009               | +0.00012 (+$0.7) |

|    Type   | Position | Transaction Hash                                                                                                                                                                                                                                                                   | Transfer (WBNB) | MEV-Relay (BNB) | Transaction Fee (BNB) | Profit (BNB)      |
|:---------:|:--------:|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------|-----------------------|-------------------|
| Front Run |     0    | 0.48336 WBNB <br> -> 0x37...8a8dc -> 37,926,166,753,754.67 PROMISE <br> [0x3b8f2e39dddbb6decf2c1e8b15549b7312835503f3eeddcb19bb242c77c9366c](https://eigenphi.io/mev/eigentx/0x3b8f2e39dddbb6decf2c1e8b15549b7312835503f3eeddcb19bb242c77c9366c)                                   | -0.48336        |                 | -0.00013              |                   |
|   Victim  |     1    | 488 USDT <br> -> 0x16...b0daE -> 0.81841 WBNB <br> -> 0x37...8a8dc -> 63,607,618,504,143.055 PROMISE <br> [0xab8f068806754ec0c0ac33570aed59901d3a71873c9d2b84bf440e0da016866b](https://eigenphi.io/mev/eigentx/0xab8f068806754ec0c0ac33570aed59901d3a71873c9d2b84bf440e0da016866b) |                 |                 |                       |                   |
|  Back Run |     2    | 37,926,166,753,754.67 PROMISE <br> -> 0x37...8a8dc -> 0.486725 WBNB <br> [0x01ae865a8e199a41acb5a57071610ee5b60fc241f181d7e08f70c8fa520afed2](https://eigenphi.io/mev/eigentx/0x01ae865a8e199a41acb5a57071610ee5b60fc241f181d7e08f70c8fa520afed2)                                  | +0.48672        | -0.00273        | -0.00039              |                   |
|           |          |                                                                                                                                                                                                                                                                                    | +0.00336        | -0.00273        | -0.00052              | +0.00011 (+$0.066) |

<br>

### Sandwich Attack used 48 Club

|     Type     | Position | Transaction Hash                                                                                                                                                                                                                 | Transfer (WBNB) | MEV-Relay (BNB) | Transaction Fee (BNB) | Profit (BNB)      |
|:------------:|:--------:|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------|-----------------------|-------------------|
| Transfer Fee |     0    | [0x5eee8dce6d7314ef53261f81c3afb6d3e0c2f26955e67197b22a431a7cf989f2](https://eigenphi.io/mev/eigentx/0x5eee8dce6d7314ef53261f81c3afb6d3e0c2f26955e67197b22a431a7cf989f2)                                                         |                 | -0.00248    |                       |                   |
|   Front Run  |     1    | 0.03326 WBNB <br> -> 0x9D...103A5 -> 45.30036 LFT <br> [0xfd0528069b42a762c77a1dd311fa073149f6068e63325011cff77cf3c13f2969](https://eigenphi.io/mev/eigentx/0xfd0528069b42a762c77a1dd311fa073149f6068e63325011cff77cf3c13f2969)  | -0.03326        |                 | -0.00066              |                   |
|    Victim    |     2    | 0.31134 WBNB <br> -> 0x9D...103A5 -> 397.67103 LFT <br> [0xc76f1a83452ce383fa6cc49f0183172f79eb345538c760448f4afd8e51489f60](https://eigenphi.io/mev/eigentx/0xc76f1a83452ce383fa6cc49f0183172f79eb345538c760448f4afd8e51489f60) |                 |                 |                       |                   |
|   Back Run   |    3     | 45.30036 LFT <br> -> 0x9D...103A5 -> 0.03658 WBNB <br> [0xc4ac3154678e594615cc97bcb3a924bf65ef58a5c033394cf158c0b21b4bc619](https://eigenphi.io/mev/eigentx/0xc4ac3154678e594615cc97bcb3a924bf65ef58a5c033394cf158c0b21b4bc619)  | +0.03658        |                 | -0.00014              |                   |
|              |          |                                                                                                                                                                                                                                  | +0.00332        | -0.00248        | -0.00080              | +0.00004 (+$0.02) |

| Type         | Position | Transaction Hash                                                                                                                                                                                                                            | Transfer (WBNB) | MEV-Relay (BNB) | Transaction Fee (BNB) | Profit (BNB)      |
|:------------:|:--------:|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------|-----------------------|-------------------|
| Transfer Fee | 0        | [0xb8adc24e0ff82126b6f6dbecf38098ea69fec8704454d5b2d6c43d5c79f52c62](https://eigenphi.io/mev/eigentx/0xb8adc24e0ff82126b6f6dbecf38098ea69fec8704454d5b2d6c43d5c79f52c62)                                                                    |                 | -0.00306        |                       |                   |
| Front Run    | 26        | 0.93624 WBNB <br>-> 0x84...E4A73 -> 7,851,389,136,191.288 DoveCoin    <br>[0x77df425af519f8f7a0f276fe18506f5994ce3a40a345b33c123cb43637391ef3](https://eigenphi.io/mev/eigentx/0x77df425af519f8f7a0f276fe18506f5994ce3a40a345b33c123cb43637391ef3) | -0.93624        |                 | -0.00060              |                   |
| Victim       | 27        | 0.022 WBNB <br>-> 0x84...E4A73 -> 164,582,801,699.83146 DoveCoin <br>[0x16f893d195bfdc461bb0d98e4c997d55c04ff21fb52bf3249bae8ea1383e2866](https://eigenphi.io/mev/eigentx/0x16f893d195bfdc461bb0d98e4c997d55c04ff21fb52bf3249bae8ea1383e2866)                  |                 |                 |                       |                   |
| Back Run     | 90        | 7,851,389,136,191.288 DoveCoin <br>-> 0x84...E4A73 -> 0.93976 WBNB <br>[0x3d2ebf6d5bf6574fc59383dfc11013794c7c14f560c2083bcaa80258910b84a8](https://eigenphi.io/mev/eigentx/0x3d2ebf6d5bf6574fc59383dfc11013794c7c14f560c2083bcaa80258910b84a8) | +0.93976        |                 | -0.00017              |                   |
|              |          |                                                                                                                                                                                                                                             | +0.00352        | -0.00306        | -0.00077              | -0.00031 (-$0.18) |

<br>

### Sandwich Attack used General

|             Type             | Position | Transaction Hash                                                                                                                                                                                                                                                         | Transfer (WBNB) | MEV-Relay (BNB) | Transaction Fee (BNB) | Profit (BNB)       |
|:----------------------------:|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------|-----------------------|--------------------|
|           Front Run          |     0    | 0.69236 WBNB <br> -> 0x36...52050 -> 419.05221 USDT <br> -> 0xCB...50043 -> 829.78960 ARTY <br> [0x19228eff3516d7b868994a64d7800c01f2ab0a8f8dfa3d2548c74b050c62978d](https://eigenphi.io/mev/eigentx/0x19228eff3516d7b868994a64d7800c01f2ab0a8f8dfa3d2548c74b050c62978d) | -0.69236        |                 | -0.00386              |                    |
| Victim (Maybe Try Front Run) |     1    | 914.41511 USDT <br> -> 0xCB...50043 -> 1,768.01385 ARTY <br> [0x5a54f193680c5cfe34bc1729f9047975d059a0463156191c3ee3e8c34bc5c959](https://eigenphi.io/mev/eigentx/0x5a54f193680c5cfe34bc1729f9047975d059a0463156191c3ee3e8c34bc5c959)                                    |                 |                 |                       |                    |
|            Victim            |     2    | 244.84935 USDT  <br> -> 0xCB...50043 -> 470.47796 ARTY  <br> [0xc88560c1b4dae7289f4d788a591a3385020d41814b6b9e8f41b5776b9d202513](https://eigenphi.io/mev/eigentx/0xc88560c1b4dae7289f4d788a591a3385020d41814b6b9e8f41b5776b9d202513)                                    |                 |                 |                       |                    |
| Victim (Maybe Try Front Run) |     3    | 489.27772 USDT  <br> -> 0xCB...50043 -> 931.07042 ARTY  <br> [0x36c74124c73fe589e62b1a8f6ccd08f9bca6b702c2a932db13b30b2ef6dc9397](https://eigenphi.io/mev/eigentx/0x36c74124c73fe589e62b1a8f6ccd08f9bca6b702c2a932db13b30b2ef6dc9397)                                    |                 |                 |                       |                    |
|           Back Run           |     4    | 829.78960 ARTY <br> -> 0xCB...50043 -> 434.07649 USDT <br> -> 0x36...52050 -> 0.71646 WBNB <br> [0x01cf62f0434cb1afebec9b2cfae79cac199c2901f2891e1f1a7dc6bb2f38a5f1](https://eigenphi.io/mev/eigentx/0x01cf62f0434cb1afebec9b2cfae79cac199c2901f2891e1f1a7dc6bb2f38a5f1) | +0.71646        |                 | -0.00335              |                    |
|                              |          |                                                                                                                                                                                                                                                                          | +0.02410        |                 | -0.00721              | +0.01689 (+$10.13) |

|    Type   | Position | Transaction Hash                                                                                                                                                                                                                                                         | Transfer (WBNB) | MEV-Relay (BNB) | Transaction Fee (BNB) | Profit (BNB)       |
|:---------:|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------|-----------------------|--------------------|
| Front Run |     0    | 0.42776 WBNB <br> -> 0x25...E3fE6 -> 741.06721 QORPO <br> [0xd327fbc24c6bbf39e93692daa06e149e00441160cae16e5936d11a9c2275f92b](https://eigenphi.io/mev/eigentx/0xd327fbc24c6bbf39e93692daa06e149e00441160cae16e5936d11a9c2275f92b)                                       | -0.42776        |                 | -0.00582              |                    |
|   Victim  |    72    | 3,780 USDT <br> -> 0x17...6f849 -> 6.27670 WBNB <br> -> 0x25...E3fE6 -> 10,543.53051 QORPO <br> [0x556e50fe2625706c949d0b071f80bb7f9a9b730561d065f4e5efeb2fa27a8e65](https://eigenphi.io/mev/eigentx/0x556e50fe2625706c949d0b071f80bb7f9a9b730561d065f4e5efeb2fa27a8e65) |                 |                 |                       |                    |
|  Back Run |    86    | 741.06721 QORPO <br> -> 0x25...E3fE6 -> 0.45089 WBNB <br> [0xbc5a1c5107f4f40b4e3c091d94339dbd863883018eaa9bd2aa2021154baf2f74](https://eigenphi.io/mev/eigentx/0xbc5a1c5107f4f40b4e3c091d94339dbd863883018eaa9bd2aa2021154baf2f74)                                       | +0.45089        |                 | -0.00046              |                    |
|           |          |                                                                                                                                                                                                                                                                          | +0.02313        |                 | -0.00628              | +0.01685 (+$10.11) |


| Type      | Position | Transaction Hash                                                                                                                                                                                                                                                                   | Transfer (WBNB) | MEV-Relay (BNB) | Transaction Fee (BNB) | Profit (BNB)            |
|:-----------:|:----------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|-----------|-----------------|-------------------|
| Front Run | 17       | 0.42469 WBNB <br> -> 0x6e6...90A278 -> 175.20479 METFI <br> -> 0x562...08F3d -> 0.46990 MOGUL <br> [0xc422d6687869388727d3a41c0697039fa9ddf4f6e48be3feecd4e5a92b5a0248](https://eigenphi.io/mev/eigentx/0xc422d6687869388727d3a41c0697039fa9ddf4f6e48be3feecd4e5a92b5a0248)    | -0.42469 |           | -0.00074        |                   |
| Victim    | 23       | 1592.55603 METFI <br> -> 0x562...08F3d -> 4.12 MOGUL <br> [0x7f03c55bbf741e9781cffd80040bbfec3b21b1d8eb173f47afb7d38890b6d537](https://eigenphi.io/mev/eigentx/0x7f03c55bbf741e9781cffd80040bbfec3b21b1d8eb173f47afb7d38890b6d537)                                             |          |           |                 |                   |
| Back Run  | 38       | 0.46990 MOGUL <br> -> 0x562...08F3d -> 180.349207 MOGUL <br> -> 0x6e6...90A278 -> 0.434972 WBNB <br>  [0x4dea3aa40d1c651fc6cb7f8c8a93f8fe116fe67ac3647cf163621969a6b280ce](https://eigenphi.io/mev/eigentx/0x4dea3aa40d1c651fc6cb7f8c8a93f8fe116fe67ac3647cf163621969a6b280ce) | +0.43497 |           | -0.00070        |                   |
|           |          |                                                                                                                                                                                                                                                                                | +0.01028 |           | -0.00144        | +0.00884 ($+5.30) |

|    Type   | Position | Transaction Hash                                                                                                                                                                                                                                                             | Transfer (WBNB) | MEV-Relay (BNB) | Transaction Fee (BNB) | Profit (BNB)      |
|:---------:|:--------:|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------|-----------------------|-------------------|
| Front Run |     0    | 0.42622 WBNB <br> -> 0x36...52050 -> 255.56599 USDT <br> -> 0xdb...252D4 -> 12,605.92082 ZEBEC <br> [0x80153922bc5451d890cfe882f37c77ff4465dc23a76df592c450f444f4951166](https://eigenphi.io/mev/eigentx/0x80153922bc5451d890cfe882f37c77ff4465dc23a76df592c450f444f4951166) | -0.42622        |                 | -0.00557              |                   |
|   Victim  |    42    | 293.28351 USDT <br> -> 0xdb...252D4 -> 14,371.14467 ZEBEC <br> [0x74cedb99bedfa47b2c281707ebef3918f318a05ad802f567e9d2d657dc44f720](https://eigenphi.io/mev/eigentx/0x74cedb99bedfa47b2c281707ebef3918f318a05ad802f567e9d2d657dc44f720)                                      |                 |                 |                       |                   |
|  Back Run |    54    | 12,605.92082 ZEBEC <br> -> 0xdb...252D4 -> 256.36776 USDT <br> -> 0x36...52050 -> 0.42713 WBNB <br> [0x6068134cea60f8f0d81422b54d35a12c90ec814f9342a1175046f990963f0644](https://eigenphi.io/mev/eigentx/0x6068134cea60f8f0d81422b54d35a12c90ec814f9342a1175046f990963f0644) | +0.42713        |                 | -0.00074              |                   |
|           |          |                                                                                                                                                                                                                                                                              | +0.00091        |                 | -0.00631              | -0.00540 (-$3.24) |

<br>
<br>
<br>

## Theoretical Explanation of MEV

### Acronym
- EL: Execution Layer
- CL: Consensus Layer
- DEX: Decentralized Exchange
- MEV: Maximal Extractable Value

<br>
<br>

### The Ideal Flow of the Expected Blockchain
This section is theoretical in nature and contains only the core information needed to develop an MEV attack. For specific implementation details, please refer to the other sections.

The theoretically expected block creation process on a blockchain is as follows:

1. User Transaction Creation:
  - The user creates a transaction and signs it with the private key of their wallet.
2. Transaction Submission:
  - The signed transaction is sent to an Execution Layer (EL) node (e.g., Geth, Erigon) via Remote Procedure Call (RPC) or other communication protocols.
3. Transaction Validation and Pooling:
  - The EL node validates the transaction and adds it to its local transaction pool (also known as the mempool).
4. Peer-to-Peer Synchronization:
  - The EL node synchronizes with peer nodes in a decentralized network, sharing the mempool. Note that while the mempool is shared, the contents may not be fully consistent across all nodes due to network latency and synchronization delays.
5. Validator Selection:
  - The Beacon Chain randomly selects a Validator (A) for block production. This selection process involves randomness, with each Validator’s chance of being selected proportional to the amount of Staking ETH they have.
6. Block Construction:
  - Validator (A) retrieves transactions from the EL node and constructs a block. The block is constructed to maximize profit by including transactions with higher fees. The EL and Consensus Layer (CL) are integrated to exchange necessary information. If a transaction submitted to the EL by a user does not reach the EL node of Validator (A), it might not be included in the block.
7. Attestation Collection:
  Validator (A) prepares the block and seeks attestations from other Validators (B). These attestations confirm that other Validators agree with the block proposed by Validator (A).
8. Block Validation and Attestation Submission:
  - Validators (B) review the proposed block and validate its correctness. They then submit their attestations to support the block.
9. Block Finalization:
  - Once enough attestations are collected, the block is added to the Beacon Chain. This step typically involves finalizing the block based on consensus rules and the required number of attestations.

<br>
<br>

### Vulnerabilities of DEX Swap
On the blockchain, DEXs make it easier to exchange various tokens. However, users who use DEXs to exchange tokens risk losing their assets. The key to this vulnerability lies in the order of transactions within a block, which can be manipulated to create a security hole.


**Arbigrage Attack**

- Definition: Arbitrage is a technique that exploits the price difference between two exchanges to make a profit.
- The process
  1. When someone trades on a decentralized exchange (DEX), a price change occurs.
  2. You can detect the price change and submit a transaction in the next block that takes advantage of the price difference to make a profit.
- However, to make a profit, you must always be ahead of others.
- The optimization process
  1. You can analyze transactions submitted by others in the Mempool, a collection of transactions that are not yet part of a block. You can calculate whether the transaction calls the DEX and what the expected price change will be.
  2. Once you analyze the transaction, you can calculate the maximum expected profit by taking advantage of the price change opportunity.
  3. The attacker's transaction must follow immediately after the victim's transaction in order to beat the competition from other attackers and make a profit.

**Sandwich Attack**

![https://medium.com/coinmonks/demystify-the-dark-forest-on-ethereum-sandwich-attacks-5a3aec9fa33e](images/sandwich.jpg)

[image source](https://medium.com/coinmonks/demystify-the-dark-forest-on-ethereum-sandwich-attacks-5a3aec9fa33e)

- Definition: A technique that manipulates the liquidity of a DEX pool by placing attack transactions in front of or behind the victim's transactions in order to profit from the victim's transactions.
- Note: This technique is a more complex attack than arbitrage, and unlike arbitrage, it results in a monetary loss to the victim. Victims of a sandwich attack actually suffer a loss of assets.
- The process
  1. The attacker artificially increases the price by placing a front-running transaction before the victim's transaction. (The larger the price increase in this process, the more the attacker may also lose money.)
  2. The victim places a transaction at a higher price than the price expected before the transaction. At this point, the price increase is equal to the difference between the front-running volume and the victim's volume.
  3. The attacker places a back-running transaction directly after the victim's transaction. This allows the attacker to recover the losses incurred during the front-running process and make additional profits.

<br>
<br>

### How to Protect from MEV Attacker
MEV attacks have a serious adverse impact on the blockchain ecosystem, but blockchain's structural limitations make it difficult to solve this problem fundamentally. Currently, there are only technologies that partially mitigate these issues.

MEV attackers need to know the victim's transaction information to launch an attack, and this information is exposed to the attacker at the Mempool stage. Therefore, the following strategies can be used to protect the victim's transactions.


Steps

1. select a Block Proposer and a Block Builder to build the proposed block.
2. The victim submits transactions to the private mempool instead of the public mempool.
3. the attacker analyzes the victim's transactions in the public or private mempool to identify profit opportunities.
4. The attacker bundles their front-running and back-running transactions with the victim's transactions and submits them to the private Orderflow.
5. The process involves the attacker returning a portion of the profit gained from the victim (e.g., the attacker may submit MEV fees as gas fees or pay fees to a specific contract address).
6. Validate the bundle's execution and the appropriateness of the fees to be paid. If multiple bundles are submitted for the same victim's transaction, the bundle with the highest fee is selected.
7. The Block Proposer looks up transactions in the public mempool and private orderflow. It then organizes and proposes a block that will bring the highest benefit to the Validator.
8. The selected Validator builds the block proposed by the Block Proposer.
9. The victim receives a portion of the profit returned by the attacker in step 5.

These services benefit all participants.

- Victim: Losses can be reduced.
- Attacker: By fixing the order of transactions into a bundle, they can eliminate the risk of failures and errors due to the order of transactions. The risk of errors is eliminated because when you submit a bundle, you test it to make sure it runs without errors. (However, you may incur some losses because you must return some profit to the victim).
- Validator: You can maximize your profits. (The Flashbots team [claims](https://hackmd.io/@flashbots/mev-in-eth2) that validators using MEV-Boost can increase their profits by over 60%).


Services such as [Flashbots on ETH](https://www.flashbots.net), [bloXroute on BSC](https://bloxroute.com), and [48 Club on BSC](https://docs.48.club/buidl/infrastructure/puissant-builder) provide this functionality. However, in the case of bloXroute, some have claimed that it destroys the BSC ecosystem (see the [More Information](#more-information) page below for more details).

<br>

#### Are the Block Proposer and Builder Separated?
Yes. The concept of separating the Block Proposer and Builder is called Proposer/Builder Separation (PBS).

A good place to start is with Ethereum's MEV-Boost.

![https://docs.flashbots.net/flashbots-mev-boost/introduction](images/mev-boost-integration-overview.jpg)
PBS promotes decentralization of the Ethereum network, increasing the overall benefit to network participants through competition among block builders.

<br>
<br>
<br>

## Detailed Explanation of Source Code and Formulas
The cost of using the node server and bloXroute was significant, and the need to see results quickly prevented us from giving enough thought or refactoring to the structure of the project. I apologize if the code is hard to read. 🙇
### Project Structure
#### Directory Structure
- **contract**: This is a Solidity project based on **Hardhat**.
  * **contracts**: Solidity code to perform **MEV** is included.
  * **test**: I wrote the Solidity test code in TypeScript.

- **docker**
  * **node**: The Dockerfile required to run the node.
  * **source**: A Dockerfile for running Python source code (not used for production).

- **iac**: Infrastructure as Code (IAC) written in **Pulumi** for running nodes.
  * **aws**: IAC in an AWS environment.
    + **gcp**: IAC in a GCP environment (Deprecated in development).

- **pyrevm**: This is a Python wrapper of REVM, a Rust implementation of the **Ethereum Virtual Machine** (EVM). The original can be found at [paradigmxyz/pyrevm](https://github.com/paradigmxyz/pyrevm).

- **src**: Python code to capture MEV opportunities.
  * **dex**: This is the initial code for a Python implementation of the DEX AMM. It is now deprecated as legacy code, and we have fully implemented AMM for Uniswap V2 and V3. For Uniswap V3, we refer to [ucsb-seclab/goldphish](https://github.com/ucsb-seclab/goldphish/blob/main/pricers/uniswap_v3.py). Curve's AMM has a ±1 error in calculations per pool. See `tests/test_dex/test_curve_*.py` for details on supported Curve pools.
  * **multicall**: Provides MultiCall functionality. The original can be found at [banteg/multicall.py](https://github.com/banteg/multicall.py).

- **tests**: This is code to test the `src` code.


<br>
<br>

### IAC Tips

- For the region, I recommend New York, the USA, or Germany.
  * By running your node as close as possible to other nodes that publicly receive transactions, you can quickly get your mempool shared in a limited amount of time.

- Do not separate clients and nodes performing MEV attacks from load balancers, etc.
  * While you may want to decentralize your network for the safety of your RPC servers, network speed between MEV clients and nodes is critical.
  * I ran the MEV client and nodes on the same EC2 instance to minimize network loss.

- It's important to utilize snapshots.
  * `geth` can be somewhat less reliable.
  * I have had several experiences with chain data corruption when geth crashes, so I recommend actively using the snapshot feature.


<br>
<br>

### About MEV-Relay

The project supports three paths

- **General**: Go through Public Mempool without using MEV-Relay.
- **48 Club**: Use the Puissant API to perform MEV operations.
- **bloXroute**: There is a base cost, and you must pay a separate fee for each bundle.

|Name|Support Bundle|Base Price|
|------|:---:|---|
| General|X|-|
|[48 Club](https://docs.48.club/buidl/infrastructure/puissant-builder/send-bundle)|O|-|
| [bloXroute](https://docs.bloxroute.com/apis/mev-solution/bsc-bundle-submission)|O|$5,000/Month|
|[TxBoost](http://txboost.com)|O|-|

<br>

In [Transaction Sample for Sandwich Attack] (#transaction-sample-for-sandwich-attack), you can see that bloXroute and 48 Club have lower profits compared to General. Since MEV attacks are not carried out in isolation, there is inevitably competition from other competitors, which comes at a cost.

First, let's analyze General: General does not use MEV-Relay, so transaction execution and order are not guaranteed during an attack. If you fail to perform DEX transactions in the proper transaction order, you may be victimized by other attackers. If you try to attack after the MEV attack is complete, you may lose the transaction fee. Also, if the amount of tokens in the pool you tried to attack changes, the transaction may fail (assuming another attacker has already tried). Even if it fails, you will still incur gas costs.

Next, let's look at bloXroute and 48 Club. There are two main advantages to using MEV-Relay. First, you are guaranteed the order of your transactions, and second, you are not charged if a transaction fails. To eliminate this risk, you need to pay a de-risking fee. The cost of de-risking basically includes the fee you pay to MEV-Relay and the cost of bidding to win the competition.

For this reason, the cost of General may not be apparent when analyzing a single transaction.


More information

- [BSC MEV Overview on the bnbchain docs](https://docs.bnbchain.org/bnb-smart-chain/validator/mev/overview/)
- [bloxroute exploiting users for MEV on the bnb-chain/bsc GitHub issue](https://github.com/bnb-chain/bsc/issues/1706)

<br>
<br>

### Explain the Solidity Code

#### What is the difference between sandwichFrontRun and sandwichFrontRunDifficult?
Let's assume that Pool A and Pool B exist.

- **sandwichFrontRun**: The transactions are performed in the following order `My Contract -> A Pool -> My Contract -> B Pool -> My Contract`.

- **sandwichFrontRunDifficult**: The transaction is performed in the following order: `My Contract -> A Pool -> B Pool -> My Contract`. In this case, each pool needs to verify that it can send tokens to the next pool and that the next pool can receive tokens, which can reduce the number of token transfers.







<br>

#### About the BackRun Function
There are three functions

- **sandwichBackRunWithBloxroute**: This function performs a BackRun, and then the fee is paid via bloXroute.

- **sandwichBackRun**: This function performs a BackRun. It is functionally equivalent to `sandwichBackRunWithBloxroute`, except that it does not involve paying a fee.

- **sandwichBackRunDifficult**: This function performs a BackRun similar to `sandwichBackRun`, but requires each pool to validate that it can send and receive tokens before the transaction can proceed.







#### Swap Router
The contract `contract/contracts/dexes/SwapRouter.sol` facilitates swaps at a high level. This contract can execute swaps with just the DEX ID, pool address, token address, and amount information.

<br>

#### Supported DEX List
Swap supports the following DEXs

- **Uniswap V2 Family**: UniswapV2, SushiswapV2, PancakeSwapV2, THENA, BiswapV2, ApeSwap, MDEX, BabySwap, Nomiswap, WaultSwap, GibXSwap
- **Uniswap V3 Family**: UniswapV3, SushiswapV3, PancakeSwapV3, THENA FUSION
- **Curve (ETH)**: Supports most major pools.

<br>

#### Solidity Test Code

When writing Solidity test code, i considered the following:

- Make sure DEX swaps are working properly
- Connection state when swapping across multiple pools in succession (arbitrage)
- Works with different chains
- Utilize [hardhat-exposed](https://www.npmjs.com/package/hardhat-exposed) to test private functions as well as public functions

The test code is located in the following files:

- `contract/test/dexes.ts`
- `contract/test/ArbitrageSwap.ts`


<br>
<br>

### Explain the Python Code

#### Important Note
- Follow along using the `main_sandwich.py` file as a reference. This project contains several unused files or functions.
- This code was working as of May 2024, and due to the nature of the blockchain space, things can change quickly, most notably the way 48 Club uses Puissant.

<br>

#### Explain the Process in Writing
1. on startup, the following features are enabled
   - Fetch blocks and Mempools from bloXroute as streams (experimentally, Mempools from bloXroute are about 200ms faster than local nodes).
   - In bloXroute, stream the address of the validator that will build the next block.
   - Run the `main` function with the MEV function as a multiprocess.

2. Filter transactions received from the Mempool stream are based on the presence of gas information and data. (If data is empty, the contract function is not called.)

3. Trace the transaction using `debug_traceCall`:
   1. If an error occurs during the trace, remove the transaction.
   2. in `src/apis/trace_tx.py::search_dex_transaction`, verify if the transaction involves a DEX swap. (You can get the exchange type, pool address, and amount information.) If there are multiple calls by the same swap, merge them into a single `SwapEvent`.
   3. The `Transaction` class contains not only the `SwapEvent` but also several pieces of information about the transaction.
   4. export the `Transaction` through the queue pipe.

4. pull a `Transaction` out of the queue from each `main` that ran as a multiprocess.

5. Analyze if the transaction can be attacked for profit:
   1. If the transaction contains a swap from the Uniswap V2 family, quickly validate it using the `calculate_uniswap_v2_sandwich` function.
   2. swaps in the Uniswap V3 series are validated using EVM (pyREVM).

6. If the transaction is determined to have a profit potential, get the validator information to build the next block. Based on the validator address, determine whether to route the attack transaction as General, 48 Club, or bloXroute:
   - Validators for bloXroute can be found with [bsc_mev_validators method](https://docs.bloxroute.com/apis/mev-solution/bsc-bundle-submission/list-of-bsc-validators).
   - 48 Club's can be determined by calling [contract function](https://bscscan.com/address/0x5cc05fde1d231a840061c1a2d7e913cedc8eabaf). (48 Club's Puissant has been deprecated.)
   - Other validator addresses use the General path. (This leaves them open to attack by others and does not guarantee transaction order.)

7. Create a sandwich transaction and send the bundle via the selected path.

**Note**: Steps 2-3 and 4-7 are split into different processes.

<br>

#### Why is Arbitrage Only Used for General Path?
The MEV analysis revealed a few important trends:

- **Arbitrage vs. Sandwich Attacks**: When given the opportunity to attack, sandwich attacks tended to yield higher profits than arbitrage. Therefore, when submitting a bundle to MEV-Relay with arbitrage, it was likely to lose in competition with other sandwich attack bundles.

- **Cautions for General Paths**: If you submit Arbitrage with the General path, the transaction will always be executed unless canceled. This will always result in a GAS cost. If your transaction is placed right after the victim's transaction, you may benefit, but if you lose the race to other arbitrage attackers, you may lose money due to the GAS cost.

- **Speed up Mempool registration**: Due to the lack of node optimization, we did not have enough opportunity to compete with other attackers via the generic path. Researching ways to make it faster for attackers to register their arbitrage transactions to the mempool could increase profits (however, the large cost outlay prevented continued experimentation).


<br>

#### Trace Transaction

When you trace a transaction, the results are provided on a per-function call basis. This allows you to see if the swap function is called and analyze the values passed as arguments to the function.

~~~ json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "action": {
        "callType": "call",
        "from": "0x83806d539d4ea1c140489a06660319c9a303f874",
        "gas": "0x1a1f8",
        "input": "0x",
        "to": "0x1c39ba39e4735cb65978d4db400ddd70a72dc750",
        "value": "0x7a16c911b4d00000"
      },
      "blockHash": "0x7eb25504e4c202cf3d62fd585d3e238f592c780cca82dacb2ed3cb5b38883add",
      "blockNumber": 3068185,
      "result": {
        "gasUsed": "0x2982",
        "output": "0x"
      },
      "subtraces": 2,
      "traceAddress": [],
      "transactionHash": "0x17104ac9d3312d8c136b7f44d4b8b47852618065ebfa534bd2d3b5ef218ca1f3",
      "transactionPosition": 2,
      "type": "call"
    },
    {
      "action": {
        "callType": "call",
        "from": "0x1c39ba39e4735cb65978d4db400ddd70a72dc750",
        "gas": "0x13e99",
        "input": "0x16c72721",
        "to": "0x2bd2326c993dfaef84f696526064ff22eba5b362",
        "value": "0x0"
      },
      "blockHash": "0x7eb25504e4c202cf3d62fd585d3e238f592c780cca82dacb2ed3cb5b38883add",
      "blockNumber": 3068185,
      "result": {
        "gasUsed": "0x183",
        "output": "0x0000000000000000000000000000000000000000000000000000000000000001"
      },
      "subtraces": 0,
      "traceAddress": [
        0
      ],
      "transactionHash": "0x17104ac9d3312d8c136b7f44d4b8b47852618065ebfa534bd2d3b5ef218ca1f3",
      "transactionPosition": 2,
      "type": "call"
    },
    {
      "action": {
        "callType": "call",
        "from": "0x1c39ba39e4735cb65978d4db400ddd70a72dc750",
        "gas": "0x8fc",
        "input": "0x",
        "to": "0x70faa28a6b8d6829a4b1e649d26ec9a2a39ba413",
        "value": "0x7a16c911b4d00000"
      },
      "blockHash": "0x7eb25504e4c202cf3d62fd585d3e238f592c780cca82dacb2ed3cb5b38883add",
      "blockNumber": 3068185,
      "result": {
        "gasUsed": "0x0",
        "output": "0x"
      },
      "subtraces": 0,
      "traceAddress": [
        1
      ],
      "transactionHash": "0x17104ac9d3312d8c136b7f44d4b8b47852618065ebfa534bd2d3b5ef218ca1f3",
      "transactionPosition": 2,
      "type": "call"
    }
  ],
  "id": 0
}
~~~
[source alchemy example](https://docs.alchemy.com/reference/trace-transaction)

This repo detects three kinds of swaps. A value expressed as a hexadecimal number, such as `0x022c0d9f`, is called a Function Selector. Each function has a unique Function Selector value, which can be found in the [Ethereum Signature Database](https://www.4byte.directory/signatures/?bytes4_signature=0x022c0d9f). The Function Selector is located at the very beginning of `call[“input”]`. If detected, it is assumed that a swap event will occur in that transaction.

The `call[“to”]` represents the contract address where the function is executed, and since swaps take place in a pool, it means the pool address. The extracted DEX type and pool address are combined and recorded in `swap_events`.



~~~ python
    from_ = call["from"]
    to = call["to"]
    input = call["input"]

    if "input" not in call:
        return []

    if input.startswith("0x022c0d9f"):
        swap_events = set_swap_event("UNISWAP_V2", swap_events, to)
    if input.startswith("0x6d9a640a"):
        swap_events = set_swap_event("BAKERYSWAP", swap_events, to)
    if input.startswith("0x128acb08"):
        swap_events = set_swap_event("UNISWAP_V3", swap_events, to)
~~~

The only remaining necessary information is the token address and token amount. The complicated part is that the token transfer function is not called inside the swap function.

**Uniswap V2 Swap cases**

- **In case 1**
  1. Call swap function
  2. Transfer from pool to recipient
  3. Transfer from msg.sender to pool

- **In case 2*
  1. Transfer from token sender to pool
  2. Call swap function
  3. Transfer from pool to recipient

**Uniswap V3 Swap cases**

- **In case 1**
  1. Call swap function
  2. Transfer from pool to recipient
  3. Transfer from msg.sender to pool

Depending on the order of the swap, extracting the required values can be difficult. Therefore, we detect the `transfer` and `transferFrom` function calls and extract the sender, recipient, and value from `call[“input”]`. Simply extracting the value is not enough; we need to validate that the token transfer is associated with a pool swap. To do this, we utilize a union with the `swap_events` variable.

~~~ python
    # transfer
    is_in_transfer = False
    if input.startswith("0xa9059cbb"):
        recipient = "0x" + input[2 + 32: 2 + 32 + 40]
        value = hex_to_uint256(input[2 + 32 + 40: 2 + 32 + 40 + 64])
        if value > 0:
            swap_events = set_transfer_event(swap_events, from_, to, recipient, value)
            is_in_transfer = True
    # transferFrom
    if input.startswith("0x23b872dd"):
        sender = "0x" + input[2 + 32: 2 + 32 + 40]
        recipient = "0x" + input[2 + 32 + 40 + 64 - 40: 2 + 32 + 40 + 64]
        value = hex_to_uint256(input[2 + 32 + 40 + 64: 2 + 32 + 40 + 64 + 64])
        if value > 0:
            swap_events = set_transfer_event(swap_events, sender, to, recipient, value)
            is_in_transfer = True
~~~

The result of extracting the required data from the `swap function` and `token transfer function` and combining them is accumulated in the form `swap_events: List[SwapEvent]`.

~~~ python
class SwapEvent:
    def __init__(self, dex=None, address=None, token_in=None, token_out=None, amount_in=0, amount_out=0):
        self.dex = dex
        self.address = address
        self.token_in = token_in
        self.token_out = token_out
        self.amount_in = amount_in
        self.amount_out = amount_out
~~~

The following cases exist:

- **Normal Swap**: If `dex`, `address`, `token_in`, `token_out`, `amount_in`, and `amount_out` are all present in the `SwapEvent`, this indicates a normal swap.
- If **Not a Token Transfer**: If only `token_out`, `amount_in`, and `amount_out` exist in a `SwapEvent`, it is removed because it is not a token transfer for a swap.
- Problem**: If the `SwapEvent` only has `dex`, `address`, there may be a problem with the data or code.

Trace the transaction as above to catch the swap event.

<br>
<br>

### Formula Parts
#### Reasons Why Understanding DEX AMM is Important
The fundamental reason attackers can seize profit opportunities lies within DEX AMMs. This is because the same trade can yield different profits depending on the AMM's calculation.

In this part, we will analyze the AMMs on the DEX and implement an efficient formula to maximize profit.

<br>

#### Structure of Uniswap V2, V3
While Uniswap V2 and V3 have similar overall structures, their main difference is their Automated Market Makers (AMMs).

Uniswap has three main contract addresses:

- **Router Address**
  - When a swap is performed in the standard way, such as through the Uniswap web interface, it goes through the router contract.
  - This contract receives the tokens to trade, calculates the quote, and forwards the swap request to the pair (pool) contract.

- **Factory Address**
  - Manages pair(pool) contracts.
  - Used when creating a new pair(pool) contract.
  - You can create an address for a pair(pool) contract based on two token addresses.

- **Pair (Pool) Address**
  - Minted tokens are stored here.
  - Receive and execute swap calls.


<br>

#### Optimize the Uniswap V2 Swap to the Extreme
The official formula for calculating the number of tokens obtained during a swap on Uniswap V2 is as follows.

##### 1. Uniswap V2 Amount Out Formula
Variable definitions

- $x$ = the amount of token that you want to trade
- $y$ = the amount of token that you want to receive
- $R_{in}$ = the reserve of the input token
- $R_{out}$ = the reserve of the output token

Formula

- $y = \frac{997R_{out} x}{1000 R_{in} + 997 x}$

Source code (Solidity)

~~~ Solidity
function getAmountOut(uint amountIn, uint reserveIn, uint reserveOut) internal pure returns (uint amountOut) {
    require(amountIn > 0, 'UniswapV2Library: INSUFFICIENT_INPUT_AMOUNT');
    require(reserveIn > 0 && reserveOut > 0, 'UniswapV2Library: INSUFFICIENT_LIQUIDITY');
    uint amountInWithFee = amountIn.mul(997);
    uint numerator = amountInWithFee.mul(reserveOut);
    uint denominator = reserveIn.mul(1000).add(amountInWithFee);
    amountOut = numerator / denominator;
}
~~~
[function getAmountOut](https://github.com/Uniswap/v2-periphery/blob/master/contracts/libraries/UniswapV2Library.sol#L43-L50)


Many MEV open-source projects use the formula above, but the swap formula can be optimized to even greater extremes.

The main goal is to optimize the formula so that there are no errors during the swap transaction and the maximum number of tokens are received. To do this, we need to analyze how we can validate that the proper tokens are coming in and going out when performing a swap transaction on a DEX contract.


<br>

##### 2. Analyze Uniswap V2 Swap
Source code (Solidity)

When calling the function, specify the quantity of tokens to receive as `argument`.


~~~ Solidity
function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external lock {
~~~

Sends the requested amount of tokens (`amount0Out` or `amount1Out`) to the user.


~~~ Solidity
    uint balance0;
    uint balance1;
    { // scope for _token{0,1}, avoids stack too deep errors
    address _token0 = token0;
    address _token1 = token1;
    require(to != _token0 && to != _token1, 'UniswapV2: INVALID_TO');
    if (amount0Out > 0) _safeTransfer(_token0, to, amount0Out); // optimistically transfer tokens
    if (amount1Out > 0) _safeTransfer(_token1, to, amount1Out); // optimistically transfer tokens
~~~

You can send the token to pay directly to the `pair address` before requesting the `swap` function, or you can call the `uniswapV2Call` callback function to send it to the `pair address` as shown below.

~~~ Solidity
    if (data.length > 0) IUniswapV2Callee(to).uniswapV2Call(msg.sender, amount0Out, amount1Out, data);
~~~

The following code validates that the appropriate amount of tokens were sent to the user for the tokens received from the user in `pair contract`. If the amount of tokens returned is not appropriate, the transaction will fail.

~~~ Solidity
    balance0 = IERC20(_token0).balanceOf(address(this));
    balance1 = IERC20(_token1).balanceOf(address(this));
    }
    uint amount0In = balance0 > _reserve0 - amount0Out ? balance0 - (_reserve0 - amount0Out) : 0;
    uint amount1In = balance1 > _reserve1 - amount1Out ? balance1 - (_reserve1 - amount1Out) : 0;
    require(amount0In > 0 || amount1In > 0, 'UniswapV2: INSUFFICIENT_INPUT_AMOUNT');
    { // scope for reserve{0,1}Adjusted, avoids stack too deep errors
    uint balance0Adjusted = balance0.mul(1000).sub(amount0In.mul(3));
    uint balance1Adjusted = balance1.mul(1000).sub(amount1In.mul(3));
    require(balance0Adjusted.mul(balance1Adjusted) >= uint(_reserve0).mul(_reserve1).mul(1000**2), 'UniswapV2: K');
    }

    _update(balance0, balance1, _reserve0, _reserve1);
    emit Swap(msg.sender, amount0In, amount1In, amount0Out, amount1Out, to);
}
~~~
[swap function](https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol#L159-L187)

<br>

##### 3. Optimization of Swap Formula

Variable definitions

The values of $n$ and $s$ are different for different exchanges (e.g. Uniswap, SushiSwap, etc.). More information can be found in the `src/apis/contract.py:L431`.

- $x$ = amount in
- $y$ = optimized amount out
- $n$ = 1000 where Uniswap V2
- $s$ = 3 where Uniswap V2
- $R_{in}$ = reserve in of pool
- $R_{out}$ = reserve out of pool
- $B_{in}$ = balance in after swap
- $B_{out}$ = balance out after swap
- $B_{in, adj}$ = balance in adjusted
- $B_{out, adj}$ = balance out adjusted

Simplifying

- $B_{in} = R_{in} + x$
- $B_{out} = R_{out} - y$
- $B_{in, adj} = 1000B_{in} - 3x$
- $B_{out, adj} = 1000B_{out} - 0$
- $B_{in, adj}B_{out, adj} >= 1000^2 R_{in} R_{out}$
- $B_{out, adj} = 1000(R_{out} - y)$
- $1000b_{in, adj}(R_{out} - y) >= 1000^2 R_{in} R_{out}$
- $B_{in, adj}(R_{out} - y) >= R_{in} R_{out} * 1000$
- $-y >= \lfloor \frac{R_{in} R_{out} * 1000} {B_{in, adj}} \rfloor - R_o$
- $y <= R_{out} - \lfloor \frac{1000 R_{in} R_{out}} {B_{in, adj}} \rfloor$
- $y <= R_{out} - \lfloor \frac{1000 R_{in} R_{out}} {1000(R_i + x) - 3x} \rfloor$
- $y <= R_{out} - \lfloor \frac{nR_{in} R_{out}} {n(R_{in} + x) - sx} \rfloor$

Formula

- $y <= R_{out} - \lfloor \frac{nR_{in} R_{out}} {n(R_{in} + x) - sx} \rfloor$

Formula implement (Python)

~~~ python
def _get_optimal_amount_out(amount_in, n, s, reserve_in, reserve_out):
    try:
        return reserve_out - ((reserve_in * reserve_out * n) // (n *(reserve_in + amount_in) - s * amount_in))
    except ZeroDivisionError:
        return 0
~~~

<br>

##### 4. Verification of the Formula Optimized to the Extreme
Validate optimized formulas.

- block number = 39744974
- Uniswap V2 USDT/WBNB address = 0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE
- input token = WBNB
- output token = DAI
- $n$ = 10000
- $s$ = 25
- $R_{in}$ = 12124290984572619906122
- $R_{out}$ = 7262381719977943429386502

When using the official formula

- $x$ = 10000000000000000000 (10 WBNB)
- $y$ = 5967066790489861652480 (5967.06 DAI)

When using the formula optimized to the extreme

- $x$ = 10000000000000000000 (10 WBNB)
- $y$ = 5970056841417710950357 (5970.05 DAI)


<br>

#### Multi-hop Arbitrage Formula

##### 1. 2-hop Arbitrage Formula
Suppose you have two pools with the same pair of tokens. The process of putting $x$ into the first pool, and then putting the tokens obtained into the second pool to get $y$, which is the same token as $x$, is as follows:

$x \rightarrow R_{1, in} \rightarrow R_{1, out} \rightarrow R_{2, in} \rightarrow R_{2, out} \rightarrow y$

In this case, find a formula to calculate the value of $x$ for maximum profit.

Variable definitions

- $x$ = amount in
- $y_1$ = amount out of 1st pool
- $y_2$ = amount out of 2nd pool
- $n$ = 1000 where Uniswap V2
- $s$ = 3 where Uniswap V2
- $R_{1, in}$ = reserve in of 1st pool
- $R_{1, out}$ = reserve out of 1st pool
- $R_{2, in}$ = reserve in of 2nd pool
- $R_{2, out}$ = reserve out of 2nd pool

Simplifying

- $y_1 = \frac{(n - s)R_{1, out}x}{nR_{1, in} + (n - s)x}$
- $y_2 = \frac{(n - s)R_{2, out}y_1}{nR_{2, in} + (n - s)y_1}$
- $y_2 = 	\{ (n - s)R_{2, out} \times \frac{(n - s)R_{1, out}x}{nR_{1, in} + (n - s)x} \} \div \{ nR_{2, in} + (n - s) \frac{(n - s)R_{1, out}x}{nR_{1, in} + (n - s)x} \}$
- $y_2 = 	\{ (n - s)R_{2, out} \times (n - s)R_{1, out}x \} \div [ nR_{2, in} \{ nR_{1, in} + (n - s)x \} + (n - s) (n - s)R_{1, out}x ]$
- $y_2 = 	\{ (n - s)^2R_{1, out}R_{2, out}x \} \div \{ n^2R_{1, in}R_{2, in} + (n - s)nR_{2, in}x + (n - s)^2R_{1, out}x \}$
- $y_2 =  \frac	{(n - s)^2R_{1, out}R_{2, out}x} {n^2R_{1, in}R_{2, in} + x \{ (n - s)nR_{2, in} + (n - s)^2R_{1, out} \}}$
- $F(x) = y_2 - x$
- $F^{\prime}(x) = y^{\prime}_1 - 1$
- $f = (n - s)^2R_{1, out}R_{2, out}x$
- $g = n^2R_{1, in}R_{2, in} + x \{ (n - s)nR_{2, in} + (n - s)^2R_{1, out} \}$
- $y^{\prime}_1 = \frac {f^{\prime}g - fg^{\prime}} {g^2}$
- $g^2 = f^{\prime}g - fg^{\prime}$
- $f^{\prime}g - fg^{\prime} = (n - s)^2R_{1, out}R_{2, out} [ n^2R_{1, in}R_{2, in} + x \{ (n - s)nR_{2, in} + (n - s)^2R_{1, out} \} ] - (n - s)^2R_{1, out}R_{2, out}x \{ (n - s)nR_{2, in} + (n - s)^2R_{1, out} \}$
- $f^{\prime}g - fg^{\prime} = (n - s)^2R_{1, out}R_{2, out} \{ n^2R_{1, in}R_{2, in} + (n - s)nR_{2, in} x \} + (n - s)^4R^2_{1, out}R_{2, out} x - (n - s)^3nR_{2, in}R_{1, out}R_{2, out}x - (n - s)^4R^2_{1, out}R_{2, out}x$
- $f^{\prime}g - fg^{\prime} = (n - s)^2R_{1, out}R_{2, out} \{ n^2R_{1, in}R_{2, in} + (n - s)nR_{2, in} x \} - (n - s)^3nR_{2, in}R_{1, out}R_{2, out}x$
- $f^{\prime}g - fg^{\prime} = (n - s)^2n^2R_{1, in}R_{2, in}R_{1, out}R_{2, out}$
- $g^2 = [ n^2R_{1, in}R_{2, in} + x \{ (n - s)nR_{2, in} + (n - s)^2R_{1, out} \}]^2$
- $k = (n - s)nR_{2, in} + (n - s)^2R_{1, out}$
- $g^2 = (n^2R_{1, in}R_{2, in} + kx)^2$
- $g^2 = (n^2R_{1, in}R_{2, in})^2 + 2n^2R_{1, in}R_{2, in} kx + (kx)^2$
- $(n^2R_{1, in}R_{2, in})^2 + 2n^2R_{1, in}R_{2, in} kx + (kx)^2 = (n - s)^2n^2R_{1, in}R_{2, in}R_{1, out}R_{2, out}$
- $k^2x^2 + 2n^2R_{1, in}R_{2, in} kx + (n^2R_{1, in}R_{2, in})^2 - (n - s)^2n^2R_{1, in}R_{2, in}R_{1, out}R_{2, out} = 0$
- $a = k^2$
- $b = 2n^2R_{1, in}R_{2, in} k$
- $c = (n^2R_{1, in}R_{2, in})^2 - (n - s)^2n^2R_{1, in}R_{2, in}R_{1, out}R_{2, out}$
- $x^* = \frac {-b + \sqrt {b^2 - 4ac}} {2a}$

Validate the formula

- The formula expanded above is validated.
  - Consider a situation where there is a 2x price difference between the two pools.
  - Variable
    - $n = 1000$
    - $s = 3$
    - $R_{1, in}=100 * 10^{18}$
    - $R_{1, out}=1000 * 10^{18}$
    - $R_{2, in}=1000 * 10^{18}$
    - $R_{2, out}=200 * 10^{18}$
  - [Calculate and graph on desmos](https://www.desmos.com/calculator/ltanp7fyvt)
    - In the graph below, we can see that the expected value of the arbitrage profit is $8.44176 \times 10^{18}$. We can also see that the quantity of tokens that should be put into the first pool to get the maximum profit is $20.5911 \times 10^{18}$. These values are consistent with the results derived from the root formula, so we can say that the formula is validated.

![](images/2-hop-arbitrage-formula.png)

<br>

##### 2. Multi-hop Arbitrage Formula

What if there are $n$ pools instead of two pools? Generalize the arbitrage formula above to a formula for maximizing profit from $n$ pools.


3-hop

- $k = (n - s)n^2R_{2, in}R_{3, in} + (n - s)^2nR_{1, out}R_{3, in} + (n-s)^3R_{1, out}R_{2, out}$
- $a = k^2$
- $b = 2n^3R_{0, in}R_{1, in}R_{2, in} k$
- $c = (n^3R_{1, in}R_{2, in}R_{3, in})^2 - (n - s)^3n^3R_{1, in}R_{2, in}R_{3, in}R_{1, out}R_{2, out}R_{3, out}$
- $x^* = \frac {-b + \sqrt {b^2 - 4ac}} {2a}$

4-hop

- $k = (n - s)n^3R_{2, in}R_{3, in}R_{4, in} + (n - s)^2n^2R_{1, out}R_{3, in}R_{4, in} + (n-s)^3nR_{1, out}R_{2, out}R_{4, in} + (n - s)^4R_{1, out}R_{2, out}R_{3, out}$
- $a = k^2$
- $b = 2n^4R_{1, in}R_{2, in}R_{3, in}R_{4, in} k$
- $c = (n^4R_{1, in}R_{2, in}R_{3, in}R_{4, in})^2 - (n - s)^4n^4R_{1, in}R_{2, in}R_{23 in}R_{4, in}R_{1, out}R_{2, out}R_{3, out}R_{4, out}$
- $x^* = \frac {-b + \sqrt {b^2 - 4ac}} {2a}$

Generalize the formula

- $h$ = hops
- $k = (n - s)n^h \prod_{i=2}^{h} R_{i, in} + \sum_{j=2}^{h} [ (n - s)^{j}n^{h-j} \prod_{i=1}^{j - 1} R_{i, out} \prod_{i=1}^{h-j} R_{i + j, in} ]$
- $a = k^2$
- $b = 2n^{h} \prod_{i=1}^{h} R_{i, in} k$
- $c = (n^{h} \prod_{i=1}^{h} R_{i, in})^2 - (n - s)^{h}n^{h} \prod_{i=1}^{h} R_{i, in} \prod_{i=1}^{h} R_{i, out}$
- $x^* = \frac {-b + \sqrt {b^2 - 4ac}} {2a}$

Formula implement

~~~ python
def get_multi_hop_optimal_amount_in(data: List[Tuple[int, int, int, int]]):
    """
    data: List[Tuple[int, int, int, int]]
        Tuple of (N, S, reserve_in, reserve_out)

    """
    h = len(data)
    n = 0
    s = 0
    prod_reserve_in_from_second = 1
    prod_reserve_in_all = 1
    prod_reserve_out_all = 1
    for idx, (N, S, reserve_in, reserve_out) in enumerate(data):
        if S > s:
          n = N
          s = S
        
        if idx > 0:
          prod_reserve_in_from_second *= reserve_in
        
        prod_reserve_in_all *= reserve_in
        prod_reserve_out_all *= reserve_out
    
    sum_k_value = 0
    for j in range(1, h):
      prod_reserve_out_without_latest = prod([r[3] for r in data[:-1]])
      prod_reserve_in_ = 1
      for i in range(0, h-j - 1):
        prod_reserve_in_ *= data[i + j + 1][2]
      sum_k_value += (n - s) ** (j + 1) * n ** (h - j - 1) * prod_reserve_out_without_latest * prod_reserve_in_
    k = (n - s) * n ** (h - 1) * prod_reserve_in_from_second + sum_k_value
    
    a = k ** 2
    b = 2 * n ** h * prod_reserve_in_all * k
    c = (n ** h * prod_reserve_in_all ) ** 2 - (n - s) ** h * n ** h * prod_reserve_in_all * prod_reserve_out_all
    
    numerator = -b + math.sqrt(b ** 2 - 4 * a * c)
    denominator = 2 * a
    return math.floor(numerator / denominator)
~~~

<br>
<br>
<br>

## EigenPhi is Overhyped
### When Sandwich is Recognized as an Arbitrage
[EigenPhi](https://eigenphi.io) is a web service that allows you to track and analyze MEV attacks. The main page shows the profit per address. For example, it says that one address made a profit of \$30,803,554.37 in one week. Is this true?


![](images/eigenphi_1.png)

<br>

If you click on that address, you'll see a history of MEV attacks. Let's analyze one of these attacks.

![](images/eigenphi_2.png)

<br>

Analyze the token flow below.
![](images/eigenphi_3.png)
[0xadd318f803ff19bd5fc60a719bd9857610100066cb0e96108f2c1b0cbf74f7a5](https://eigenphi.io/mev/bsc/tx/0xadd318f803ff19bd5fc60a719bd9857610100066cb0e96108f2c1b0cbf74f7a5)

Token Flow

- 814.37543 WBNB -> 0x6D...8c81B(Cake-LP) -> 19,766,994,987.85470 CAT -> 0x58...eA735(PancakeV3Pool) -> 1424.92365 WBNB
- 5.26888 WBNB -> 0x6D...8c81B(Cake-LP) -> 118479117.67801 CAT -> 0x58...eA735(PancakeV3Pool) -> 5.28327 WBNB
- 0.00823WBNB  -> 0x6D...8c81B(Cake-LP) -> 185044.49375 CAT -> 0x58...eA735(PancakeV3Pool) -> 0.00823 WBNB
- 2.96989 BNB -> 0x48...84848

<br>

In the above transaction, the position in the block is number 3. Position 2 is most likely the victim's transaction. Let's find transaction 1. You can find transaction 1 at [this link](https://eigenphi.io/mev/eigentx/0xe5611d60eb6105d1d45aeeb90b09f8e309fc185cf679998e6ef1de97271b1eca).


<br>

![](images/eigenphi_4.png)

Do you see the same number we saw in transaction 3? That's adjusting the depth of liquidity. The attack labeled as arbitrage was actually a sandwich attack. Let's actually calculate the profit.

$1424.92365 \text{ WBNB} - 1421.26829 \text{ WBNB} + (5.28327 \text{ WBNB} - 5.26888 \text{ WBNB}) - 2.96989 \text{ BNB} = 0.69986 \text{ WBNB}$

The attacker's actual profit was $419.916 ($0.69986 \times 600$), not the $821,381.16 shown in EigenPhi.

<br>
<br>

### When Doing Sandwich Using 48 Club


The attack recorded in [transaction](https://eigenphi.io/mev/bsc/tx/0x8231ec4d8105694d404ec64ce7f08807c86f7a8dcb4e90dbbeee50ee8ae98110) is a sandwich attack. The profit, after subtracting the cost from the revenue of this transaction, amounts to $22.455143.


![](images/eigenphi_5.png)

Looking at all transactions in the block, there is a suspicious transaction at position 0, as shown below. This transaction is suspicious because the sending address and receiving address are the same, and the sending address matches the sending address of the transaction that performed the sandwich attack.

<br>

![](images/eigenphi_6.png)

[transactions at block](https://eigenphi.io/mev/eigentx/0x6ab43c8eda05d9ff09f11fd466d991bf4c98b7ae90208e0dc6c92a8470aa45d1,0x652dd0c03f1111611506fda141f9453fcc9d09919198c8ce2550086ae2bd92e0,0xf1b532b5de679c2498841c0aecc88d292a224869bcd9767e786d0e8e4eb1b820?tab=block)

Let's take a closer look at the suspicious transaction: It was a transfer to yourself and didn't contain any data. It also paid 1,715.244527903 Gwei for gas.

<br>

![](images/eigenphi_7.png)
[0th transaction at BscScan](https://bscscan.com/tx/0x57159629b44d1f2e9383b1f21ef7a223696026094146b25503b995fc6b41b308)

The Sandwich attacker reduced the profit from $22.455143 to $2.155413 with the 0th transaction.

The cost of the gas submitted is paid to the Validator. The Sandwich attacker won the bundle for the victim's transactions by outbidding the other attackers. Transaction 0 was used to pay for the gas to secure the winning bid in the 48 Club bidding process.

This may raise a question: why did we separate the transaction that pays the fee? We could have included the fee in transaction 1, but the transaction cost is calculated as $\frac{Gas Usage \times Gas Price}{10^9} \text{BNB}$. While $GasPrice$ can be used to control the fee, it is difficult to accurately calculate $Gas Usage$ quickly enough. This is why we fixed $GasUsage=21,000$ in transaction 0 and controlled the fee with $GasPrice$.

<br>
<br>
<br>

## Frequently Asked Questions

#### Why did you select the BSC network?
The fees on the Ethereum network can be excessively high, which prompted my choice of the BSC network, where gas is fixed at 1 Gwei.

To further optimize transaction costs, you can use the 48 Club's Soul Point feature to perform transactions at 0 Gwei.

#### Do you plan to continue developing arbitrage or MEV in the future?
I can no longer operate due to insufficient funds. I determined that $100K to $1M worth of tokens were necessary to make a net profit from sandwich attacks.



<br>
<br>
<br>

## More Information
- Page
  - [Flashbots main page](https://www.flashbots.net)
  - [MEV: The First Five Years
](https://medium.com/@Prestwich/mev-c417d9a5eb3d)
  - [Improving front running resistance of x*y=k market makers written by Vitalik Buterin](https://ethresear.ch/t/improving-front-running-resistance-of-x-y-k-market-makers/1281)
  - [TxBoost](http://txboost.com)
- GitHub BSC Repo Issue
  - About bloXroute
    - [bloxroute exploiting users for MEV](https://github.com/bnb-chain/bsc/issues/1706)
    - [bloxroute continues to destabilize BSC](https://github.com/bnb-chain/bsc/issues/1871)
    - [1Gwei but Position In Block 0 !!!](https://github.com/bnb-chain/bsc/issues/1831)
    - [Tx position in mev service provided by BloxRoute not respecting the official gwei ordering](https://github.com/bnb-chain/bsc/issues/1728)
  - About gasPrice
    - [Transactions with 0 gwei are back](https://github.com/bnb-chain/bsc/issues/1746)
    - [Transactions with 0 gwei are back²](https://github.com/bnb-chain/bsc/issues/2371)

<br>
<br>
<br>

## Star History

<a href="https://star-history.com/#DonggeunYu/MEV-Attack-on-the-BSC&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=DonggeunYu/MEV-Attack-on-the-BSC&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=DonggeunYu/MEV-Attack-on-the-BSC&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=DonggeunYu/MEV-Attack-on-the-BSC&type=Date" />
 </picture>
</a>
