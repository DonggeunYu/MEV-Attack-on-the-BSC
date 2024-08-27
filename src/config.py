from typing import Dict, Optional, List, Union
from web3 import Web3
from eth_typing import ChecksumAddress


def to_checksum_address(address: Optional[str]) -> Optional[ChecksumAddress]:
    if address:
        return Web3.to_checksum_address(address)
    else:
        return None


class AddressConfig:
    def __init__(
        self,
        uniswap_v2_factory_address: Optional[str],
        uniswap_v3_factory_address: str,
        sushiswap_v2_factory_address: Optional[List[str]],
    ):
        self.uniswap_v2_factory_address: Optional[
            ChecksumAddress
        ] = to_checksum_address(uniswap_v2_factory_address)
        self.uniswap_v3_factory_address: ChecksumAddress = to_checksum_address(
            uniswap_v3_factory_address
        )
        if sushiswap_v2_factory_address:
            self.sushiswap_v2_factory_address: Optional[ChecksumAddress] = [
                to_checksum_address(i) for i in sushiswap_v2_factory_address
            ]


class BuilderConfig:
    def __init__(self, builders: Dict[str, str]):
        self.builders = builders


class CoinMarketCapConfig:
    url: str
    dex_query_map: Dict[str, str]
    min_txns24h: int

    def __init__(self, url: str, dex_query_map: Dict[str, str], min_txns24h: int = 5):
        self.url = url
        self.dex_query_map = dex_query_map
        self.min_txns24h = min_txns24h


class Config:
    def __init__(
        self,
        http_endpoint: str,
        bloxroute_ws_endpoint: str,
        bloxroute_authorization: str,
        account_address: str,
        account_private_key: str,
        contract_address: Optional[str],
        wrapped_native_token_address: str,
        factory_config: Dict[str, Dict[str, str]],
        coinmarketcap_config: CoinMarketCapConfig,
    ):
        self.http_endpoint = http_endpoint
        self.bloxroute_ws_endpoint = bloxroute_ws_endpoint
        self.bloxroute_authorization = bloxroute_authorization
        self.account_address = Web3.to_checksum_address(account_address)
        self.account_private_key = account_private_key
        self.contract_address = to_checksum_address(contract_address)
        self.wrapped_native_token_address = Web3.to_checksum_address(
            wrapped_native_token_address
        )
        self.factory_config = self.checksum_factory_address(factory_config)
        self.coinmarketcap_config = coinmarketcap_config

    def checksum_factory_address(
        self, factory_address
    ) -> Dict[str, Dict[str, Union[ChecksumAddress, List[ChecksumAddress]]]]:
        new_factory_address = {}
        for key, value in factory_address.items():
            for k, v in value.items():
                if isinstance(v, list):
                    value[k] = [Web3.to_checksum_address(i) for i in v]
                else:
                    value[k] = Web3.to_checksum_address(v)
            new_factory_address[key] = value
        return new_factory_address


bsc_local_to_gcp_config = Config(
    http_endpoint="https://nd-616-829-754.p2pify.com/9e71f21781b22b259103e4a7c0cf2b74",
    bloxroute_ws_endpoint="wss://virginia.bsc.blxrbdn.com/ws",
    bloxroute_authorization="ZGViNzE1MTgtOTFkOC00NjRlLWEzNDctZDZkZGU5ZThmYjdhOmNjYjZjN2E5ZmVhOGVlYWNlMTYyNDRlYmY3YTQxYTZi",
    account_address="0x007fc398a4d8fEaBcDa8eD17dB92976a7E0Dba00",
    account_private_key="0x703c4b799f2137ce78e902484f674010d3dca796641bdc1224fd4a85f50404fb",
    contract_address="0xe1b73338fc95a938587ab4fca07f7f311ecc45c9",
    wrapped_native_token_address="0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    factory_config={
        "getPair": {
            "UNISWAP_V2": "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6",
            "SUSHISWAP_V2": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
            "PANCAKESWAP_V2": ["0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73", "0xBCfCcbde45cE874adCB698cC183deBcF17952812"],
            "BISWAP_V2": "0x858E3312ed3A876947EA49d572A7C42DE08af7EE",
            "APESWAP": "0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6",
            "MDEX": "0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8",
            "BABYSWAP": "0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da",
            "NOMISWAP": "0xd6715A8be3944ec72738F0BFDC739d48C3c29349",
            "BAKERYSWAP": "0x01bF7C66c6BD861915CdaaE475042d3c4BaE16A7",
            "WAULTSWAP": "0xB42E3FE71b7E0673335b3331B3e1053BD9822570",
            "GIBXSWAP": "0x97bCD9BB482144291D77ee53bFa99317A82066E8"
        },
        "getPairWithBool": {
            "THENA": "0xAFD89d21BdB66d00817d4153E055830B1c2B3970",
        },
        "getPool": {
            "UNISWAP_V3": "0xdB1d10011AD0Ff90774D0C6Bb92e5C5c8b4461F7",
            "PANCAKESWAP_V3": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
        },
        "poolByPair": {
            "THENA_FUSION": "0x306F06C147f064A010530292A1EB6737c3e378e4",
        },
    },
    coinmarketcap_config=CoinMarketCapConfig(
        "https://coinmarketcap.com/dexscan/networks/bnb-smart-chain-bep20/?page=",
        {
            # "Curve": "curve-ethereum"
        },
    ),
)
"""
            "BAKERYSWAP": "bakeryswap"
            "UNISWAP_V3": "uniswap-v3-bsc",
         "UNISWAP_V2": "uniswap-v2",
         "SUSHISWAP_V2": "sushiswap-bsc",
         "PANCAKESWAP_V2": "pancakeswap-v2-bsc",
         "PANCAKESWAP_V3": "pancakeswap-v3-bsc",
         "THENA_FUSION": "thena-fusion",
         "BISWAP_V2": "biswap-v2",
         "APESWAP": "apeswap-bsc",
         "MDEX": "mdex-bsc",
         "THENA": "thena",
         "NOMISWAP": "nomiswap",
         "BABYSWAP": "babyswap",
         "BABYDOGESWAP": "baby-doge-swap",
"""

bsc_gcp_config = Config(
    http_endpoint="http://localhost:8545",
    bloxroute_ws_endpoint="wss://virginia.bsc.blxrbdn.com/ws",
    bloxroute_authorization="ZGViNzE1MTgtOTFkOC00NjRlLWEzNDctZDZkZGU5ZThmYjdhOmNjYjZjN2E5ZmVhOGVlYWNlMTYyNDRlYmY3YTQxYTZi",
    account_address="0x007fc398a4d8fEaBcDa8eD17dB92976a7E0Dba00",
    account_private_key="0x703c4b799f2137ce78e902484f674010d3dca796641bdc1224fd4a85f50404fb",
    contract_address="0xe1b73338fc95a938587ab4fca07f7f311ecc45c9",
    wrapped_native_token_address="0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    factory_config={
        "getPair": {
            "UNISWAP_V2": "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6",
            "SUSHISWAP_V2": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
            "PANCAKESWAP_V2": ["0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73", "0xBCfCcbde45cE874adCB698cC183deBcF17952812"],
            "BISWAP_V2": "0x858E3312ed3A876947EA49d572A7C42DE08af7EE",
            "APESWAP": "0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6",
            "MDEX": "0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8",
            "BABYSWAP": "0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da",
            "NOMISWAP": "0xd6715A8be3944ec72738F0BFDC739d48C3c29349",
            "BAKERYSWAP": "0x01bF7C66c6BD861915CdaaE475042d3c4BaE16A7",
            "WAULTSWAP": "0xB42E3FE71b7E0673335b3331B3e1053BD9822570",
            "GIBXSWAP": "0x97bCD9BB482144291D77ee53bFa99317A82066E8"
        },
        "getPairWithBool": {
            "THENA": "0xAFD89d21BdB66d00817d4153E055830B1c2B3970",
        },
        "getPool": {
            "UNISWAP_V3": "0xdB1d10011AD0Ff90774D0C6Bb92e5C5c8b4461F7",
            "PANCAKESWAP_V3": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
        },
        "poolByPair": {
            "THENA_FUSION": "0x306F06C147f064A010530292A1EB6737c3e378e4",
        },
    },
    coinmarketcap_config=CoinMarketCapConfig(
        "https://coinmarketcap.com/dexscan/networks/bnb-smart-chain-bep20/?page=",
        {
            # "Curve": "curve-ethereum"
        },
    ),
)

"""
sepolia_config = Config(
    http_endpoint="https://eth-sepolia.g.alchemy.com/v2/OJ_kc5aBfDEgXWr1u8ah0LetcRU2oPuP",
    ws_endpoint="wss://eth-sepolia.g.alchemy.com/v2/OJ_kc5aBfDEgXWr1u8ah0LetcRU2oPuP",
    account_address="0x2a426E21E6CF0Bfd16965F2a570241bF3d86DD0A",
    account_private_key="0x49a6c1dab5db7e3b5aca37b1865a427610f84bebec04099e99ad6bc0ea8d7156",
    contract_address="0xD08C91bDF390Dd50796231CB961D0DCec15dB945",
    address_config=AddressConfig(
        uniswap_v2_factory_address=None,
        uniswap_v3_factory_address="0x0227628f3F023bb0B980b67D528571c95c6DaC1c",
        sushiswap_v2_factory_address=None,
    ),
    builder_config=BuilderConfig(
        builders={"flashbots": "https://relay-sepolia.flashbots.net"}
    ),
)


eth_local_config = Config(
    http_endpoint="http://localhost:8545",
    ws_endpoint="ws://localhost:8546",
    account_address="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    account_private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    contract_address=None,
    address_config=AddressConfig(
        uniswap_v2_factory_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        uniswap_v3_factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        sushiswap_v2_factory_address=["0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac",
                                      "0x115934131916C8b277DD010Ee02de363c09d037c"],
    ),
    builder_config=BuilderConfig(
        builders={
            "flashbots": "https://relay.flashbots.net",
            "beaverbuild": "https://rpc.beaverbuild.org",
            "rsync": "https://rsync-builder.xyz",
            "titanbuilder": "https://rpc.titanbuilder.xyz",
            "builder0x69": "https://builder0x69.io",
            "f1b": "https://rpc.f1b.io",
            "lokibuilder": "https://rpc.lokibuilder.xyz",
            "eden": "https://api.edennetwork.io/v1/rpc",
            "penguinbuild": "https://rpc.penguinbuild.org",
            "gambit": "https://builder.gmbit.co/rpc",
            "idcmev": "https://rpc.idcmev.xyz",
        }
    ),
    arbitrage_config=ArbitrageConfig(
        dex_from_coinmarketcap={
            "UniswapV3": "uniswap-v3-ethereum",
            "UniswapV2": "uniswap-v2",
            "SushiswapV3": "sushiswap-v3-ethereum",
            "SushiswapV2": "sushiswap-ethereum",
            # "Curve": "curve-ethereum"
        }
    ),
)

eth_local_to_gcp_config = Config(
    http_endpoint="http://34.22.99.244:8545",
    ws_endpoint="ws://34.22.99.244:8546",
    account_address="0x007fc398a4d8fEaBcDa8eD17dB92976a7E0Dba00",
    account_private_key="0x703c4b799f2137ce78e902484f674010d3dca796641bdc1224fd4a85f50404fb",
    contract_address="0xf55539ba79448e990a4f15d8b43a19bd34b66358",
    address_config=AddressConfig(
        uniswap_v2_factory_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        uniswap_v3_factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        sushiswap_v2_factory_address=["0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac",
                                      "0x115934131916C8b277DD010Ee02de363c09d037c"],
    ),
    builder_config=BuilderConfig(
        builders={
            "flashbots": "https://relay.flashbots.net",
            "beaverbuild": "https://rpc.beaverbuild.org",
            "rsync": "https://rsync-builder.xyz",
            "titanbuilder": "https://rpc.titanbuilder.xyz",
            "builder0x69": "https://builder0x69.io",
            "f1b": "https://rpc.f1b.io",
            "lokibuilder": "https://rpc.lokibuilder.xyz",
            "eden": "https://api.edennetwork.io/v1/rpc",
            "penguinbuild": "https://rpc.penguinbuild.org",
            "gambit": "https://builder.gmbit.co/rpc",
            "idcmev": "https://rpc.idcmev.xyz",
        }
    ),
    arbitrage_config=ArbitrageConfig(
        dex_from_coinmarketcap={
            "UniswapV3": "uniswap-v3-ethereum",
            "UniswapV2": "uniswap-v2",
            "SushiswapV3": "sushiswap-v3-ethereum",
            "SushiswapV2": "sushiswap-ethereum",
            # "Curve": "curve-ethereum"
        }
    ),
)

eth_gcp_config = Config(
    http_endpoint="http://10.0.1.0:8545",
    ws_endpoint="ws://10.0.1.0:8546",
    account_address="0x007fc398a4d8fEaBcDa8eD17dB92976a7E0Dba00",
    account_private_key="0x703c4b799f2137ce78e902484f674010d3dca796641bdc1224fd4a85f50404fb",
    contract_address="0xf55539ba79448e990a4f15d8b43a19bd34b66358",
    address_config=AddressConfig(
        uniswap_v2_factory_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        uniswap_v3_factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        sushiswap_v2_factory_address=["0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac",
                                      "0x115934131916C8b277DD010Ee02de363c09d037c"],
    ),
    builder_config=BuilderConfig(
        builders={
            "flashbots": "https://relay.flashbots.net",
            "beaverbuild": "https://rpc.beaverbuild.org",
            "rsync": "https://rsync-builder.xyz",
            "titanbuilder": "https://rpc.titanbuilder.xyz",
            "builder0x69": "https://builder0x69.io",
            "f1b": "https://rpc.f1b.io",
            "lokibuilder": "https://rpc.lokibuilder.xyz",
            "eden": "https://api.edennetwork.io/v1/rpc",
            "penguinbuild": "https://rpc.penguinbuild.org",
            "gambit": "https://builder.gmbit.co/rpc",
            "idcmev": "https://rpc.idcmev.xyz",
        }
    ),
    arbitrage_config=ArbitrageConfig(
        dex_from_coinmarketcap={
            "UniswapV3": "uniswap-v3-ethereum",
            "UniswapV2": "uniswap-v2",
            "SushiswapV3": "sushiswap-v3-ethereum",
            "SushiswapV2": "sushiswap-ethereum",
            # "Curve": "curve-ethereum"
        }
    ),
)
"""
