"""Base Web3 functionality and blockchain interaction layer"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
import json
from pathlib import Path

from app.core.logging import logger
from app.core.config import settings

class NetworkType(Enum):
    """Supported blockchain networks"""
    ETHEREUM_MAINNET = "ethereum_mainnet"
    ETHEREUM_SEPOLIA = "ethereum_sepolia"
    ETHEREUM_GOERLI = "ethereum_goerli"
    POLYGON_MAINNET = "polygon_mainnet"
    POLYGON_MUMBAI = "polygon_mumbai"
    BSC_MAINNET = "bsc_mainnet"
    BSC_TESTNET = "bsc_testnet"
    ARBITRUM_MAINNET = "arbitrum_mainnet"
    ARBITRUM_SEPOLIA = "arbitrum_sepolia"
    OPTIMISM_MAINNET = "optimism_mainnet"
    OPTIMISM_SEPOLIA = "optimism_sepolia"
    LOCAL_GANACHE = "local_ganache"
    LOCAL_HARDHAT = "local_hardhat"

class ContractType(Enum):
    """Supported smart contract types"""
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    MULTISIG = "MultiSig"
    DAO = "DAO"
    DEFI_VAULT = "DeFiVault"
    NFT_MARKETPLACE = "NFTMarketplace"
    STAKING = "Staking"
    CUSTOM = "Custom"

class TransactionStatus(Enum):
    """Transaction status types"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"

class NetworkConfig(BaseModel):
    """Network configuration model"""
    name: str
    network_type: NetworkType
    rpc_url: str
    chain_id: int
    currency_symbol: str
    block_explorer_url: Optional[str] = None
    gas_price_gwei: Optional[float] = None
    is_testnet: bool = False

class ContractConfig(BaseModel):
    """Smart contract configuration model"""
    name: str
    contract_type: ContractType
    solidity_version: str = "0.8.19"
    features: List[str] = Field(default_factory=list)
    constructor_params: Dict[str, Any] = Field(default_factory=dict)
    custom_functions: List[Dict[str, Any]] = Field(default_factory=list)
    security_features: List[str] = Field(default_factory=list)
    optimization_enabled: bool = True
    optimization_runs: int = 200

class DeploymentConfig(BaseModel):
    """Contract deployment configuration"""
    network: NetworkType
    gas_limit: Optional[int] = None
    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    nonce: Optional[int] = None
    value: int = 0
    verify_contract: bool = False
    etherscan_api_key: Optional[str] = None

class TransactionInfo(BaseModel):
    """Transaction information model"""
    hash: str
    status: TransactionStatus
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    transaction_fee: Optional[str] = None
    confirmation_count: int = 0
    created_at: str
    confirmed_at: Optional[str] = None

class ContractInfo(BaseModel):
    """Deployed contract information"""
    address: str
    name: str
    contract_type: ContractType
    network: NetworkType
    deployment_tx: str
    abi: List[Dict[str, Any]]
    bytecode: str
    source_code: Optional[str] = None
    compiler_version: str
    optimization_enabled: bool
    deployed_at: str
    verified: bool = False

class BaseWeb3Provider(ABC):
    """Abstract base class for Web3 providers"""
    
    def __init__(self, network_config: NetworkConfig):
        self.network_config = network_config
        self.w3: Optional[Web3] = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Web3 connection"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.network_config.rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to {self.network_config.name}")
            
            logger.info(f"Connected to {self.network_config.name} (Chain ID: {self.network_config.chain_id})")
            
        except Exception as e:
            logger.error(f"Error connecting to {self.network_config.name}: {str(e)}")
            raise
    
    @abstractmethod
    async def deploy_contract(
        self, 
        contract_config: ContractConfig,
        deployment_config: DeploymentConfig,
        private_key: str
    ) -> ContractInfo:
        """Deploy a smart contract"""
        pass
    
    @abstractmethod
    async def call_contract_function(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: List[Any] = None,
        private_key: Optional[str] = None
    ) -> Any:
        """Call a contract function"""
        pass
    
    @abstractmethod
    async def get_transaction_status(self, tx_hash: str) -> TransactionInfo:
        """Get transaction status"""
        pass
    
    @abstractmethod
    async def estimate_gas(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: List[Any] = None,
        from_address: Optional[str] = None
    ) -> int:
        """Estimate gas for a transaction"""
        pass
    
    def get_account_from_private_key(self, private_key: str) -> Account:
        """Get account from private key"""
        return Account.from_key(private_key)
    
    def get_balance(self, address: str) -> float:
        """Get account balance in native currency"""
        if not self.w3:
            raise ConnectionError("Web3 connection not initialized")
        
        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance_wei, 'ether')
    
    def get_gas_price(self) -> int:
        """Get current gas price"""
        if not self.w3:
            raise ConnectionError("Web3 connection not initialized")
        
        return self.w3.eth.gas_price
    
    def get_latest_block(self) -> Dict[str, Any]:
        """Get latest block information"""
        if not self.w3:
            raise ConnectionError("Web3 connection not initialized")
        
        block = self.w3.eth.get_block('latest')
        return {
            "number": block.number,
            "hash": block.hash.hex(),
            "timestamp": block.timestamp,
            "gas_limit": block.gasLimit,
            "gas_used": block.gasUsed,
            "transaction_count": len(block.transactions)
        }
    
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address"""
        if not self.w3:
            raise ConnectionError("Web3 connection not initialized")
        
        return self.w3.is_address(address)
    
    def to_checksum_address(self, address: str) -> str:
        """Convert address to checksum format"""
        if not self.w3:
            raise ConnectionError("Web3 connection not initialized")
        
        return self.w3.to_checksum_address(address)
    
    def get_contract_instance(self, address: str, abi: List[Dict[str, Any]]) -> Contract:
        """Get contract instance"""
        if not self.w3:
            raise ConnectionError("Web3 connection not initialized")
        
        return self.w3.eth.contract(address=address, abi=abi)
    
    async def wait_for_transaction_receipt(
        self, 
        tx_hash: str, 
        timeout: int = 120,
        poll_latency: float = 0.1
    ) -> Dict[str, Any]:
        """Wait for transaction receipt"""
        if not self.w3:
            raise ConnectionError("Web3 connection not initialized")
        
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash, 
                timeout=timeout, 
                poll_latency=poll_latency
            )
            
            return {
                "transactionHash": receipt.transactionHash.hex(),
                "blockNumber": receipt.blockNumber,
                "gasUsed": receipt.gasUsed,
                "status": receipt.status,
                "contractAddress": receipt.contractAddress,
                "logs": [dict(log) for log in receipt.logs]
            }
            
        except Exception as e:
            logger.error(f"Error waiting for transaction receipt: {str(e)}")
            raise

class NetworkManager:
    """Manager for different blockchain networks"""
    
    def __init__(self):
        self.networks: Dict[NetworkType, NetworkConfig] = {}
        self._initialize_default_networks()
    
    def _initialize_default_networks(self):
        """Initialize default network configurations"""
        default_networks = {
            NetworkType.ETHEREUM_MAINNET: NetworkConfig(
                name="Ethereum Mainnet",
                network_type=NetworkType.ETHEREUM_MAINNET,
                rpc_url="https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
                chain_id=1,
                currency_symbol="ETH",
                block_explorer_url="https://etherscan.io",
                is_testnet=False
            ),
            NetworkType.ETHEREUM_SEPOLIA: NetworkConfig(
                name="Ethereum Sepolia",
                network_type=NetworkType.ETHEREUM_SEPOLIA,
                rpc_url="https://sepolia.infura.io/v3/YOUR_PROJECT_ID",
                chain_id=11155111,
                currency_symbol="ETH",
                block_explorer_url="https://sepolia.etherscan.io",
                is_testnet=True
            ),
            NetworkType.POLYGON_MAINNET: NetworkConfig(
                name="Polygon Mainnet",
                network_type=NetworkType.POLYGON_MAINNET,
                rpc_url="https://polygon-rpc.com",
                chain_id=137,
                currency_symbol="MATIC",
                block_explorer_url="https://polygonscan.com",
                is_testnet=False
            ),
            NetworkType.POLYGON_MUMBAI: NetworkConfig(
                name="Polygon Mumbai",
                network_type=NetworkType.POLYGON_MUMBAI,
                rpc_url="https://rpc-mumbai.maticvigil.com",
                chain_id=80001,
                currency_symbol="MATIC",
                block_explorer_url="https://mumbai.polygonscan.com",
                is_testnet=True
            ),
            NetworkType.LOCAL_HARDHAT: NetworkConfig(
                name="Local Hardhat",
                network_type=NetworkType.LOCAL_HARDHAT,
                rpc_url="http://127.0.0.1:8545",
                chain_id=31337,
                currency_symbol="ETH",
                is_testnet=True
            )
        }
        
        # Update with environment-specific RPC URLs if available
        if hasattr(settings, 'ETHEREUM_RPC_URL') and settings.ETHEREUM_RPC_URL:
            default_networks[NetworkType.ETHEREUM_MAINNET].rpc_url = settings.ETHEREUM_RPC_URL
        
        if hasattr(settings, 'POLYGON_RPC_URL') and settings.POLYGON_RPC_URL:
            default_networks[NetworkType.POLYGON_MAINNET].rpc_url = settings.POLYGON_RPC_URL
        
        self.networks.update(default_networks)
    
    def add_network(self, network_config: NetworkConfig):
        """Add a custom network configuration"""
        self.networks[network_config.network_type] = network_config
        logger.info(f"Added network configuration: {network_config.name}")
    
    def get_network(self, network_type: NetworkType) -> Optional[NetworkConfig]:
        """Get network configuration"""
        return self.networks.get(network_type)
    
    def list_networks(self) -> List[NetworkConfig]:
        """List all available networks"""
        return list(self.networks.values())
    
    def get_testnet_networks(self) -> List[NetworkConfig]:
        """Get all testnet configurations"""
        return [config for config in self.networks.values() if config.is_testnet]
    
    def get_mainnet_networks(self) -> List[NetworkConfig]:
        """Get all mainnet configurations"""
        return [config for config in self.networks.values() if not config.is_testnet]

# Global network manager instance
network_manager = NetworkManager()