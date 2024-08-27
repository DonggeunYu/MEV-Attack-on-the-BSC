from src.config import bsc_local_to_gcp_config
from src.evm import EVM


evm = EVM(
    "https://bsc-mainnet.core.chainstack.com/8b86535e4243bdf9a37eea574a6f3ae3",
    bsc_local_to_gcp_config.account_address,
    bsc_local_to_gcp_config.contract_address,
)
evm.set("37414354")
checkpoint = evm._evm.snapshot()
import time

now = time.time()
before = evm.balance("0x8894E0a0c962CB723c1976a4421c95949bE2D4E3")
print(
    evm.balance_of(
        "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",
        "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    )
)
evm.transfer(
    "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",
    bsc_local_to_gcp_config.contract_address,
    "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    1,
)
print(before - evm.balance("0x8894E0a0c962CB723c1976a4421c95949bE2D4E3"))
print(
    evm.balance_of(
        "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",
        "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    )
)

evm._evm.revert(checkpoint)
checkpoint = evm._evm.snapshot()
print(
    evm.balance_of(
        "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",
        "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    )
)

evm.transfer(
    "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",
    bsc_local_to_gcp_config.contract_address,
    "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    1,
)

print(
    evm.balance_of(
        "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",
        "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    )
)

evm._evm.revert(checkpoint)
