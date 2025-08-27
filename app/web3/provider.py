"""Web3 provider implementation for blockchain interactions"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
import json
from pathlib import Path

from web3 import Web3
from web3.contract import Contract
from web3.exceptions import TransactionNotFound, BlockNotFound
from eth_account import Account
from solcx import compile_source, install_solc, set_solc_version

from app.web3.base import (
    BaseWeb3Provider, NetworkConfig, ContractConfig, DeploymentConfig,
    ContractInfo, TransactionInfo, TransactionStatus, NetworkType
)
from app.web3.contract_generator import contract_generator
from app.core.logging import logger
from app.core.config import settings

class Web3Provider(BaseWeb3Provider):
    """Concrete Web3 provider implementation"""
    
    def __init__(self, network_config: NetworkConfig):
        super().__init__(network_config)
        self.deployed_contracts: Dict[str, ContractInfo] = {}
        self._ensure_solc_version()
    
    def _ensure_solc_version(self):
        """Ensure Solidity compiler is available"""
        try:
            # Install and set default Solidity version
            install_solc('0.8.19')
            set_solc_version('0.8.19')
            logger.info("Solidity compiler initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Solidity compiler: {str(e)}")
    
    async def deploy_contract(
        self, 
        contract_config: ContractConfig,
        deployment_config: DeploymentConfig,
        private_key: str
    ) -> ContractInfo:
        """Deploy a smart contract"""
        try:
            if not self.w3:
                raise ConnectionError("Web3 connection not initialized")
            
            logger.info(f"Starting deployment of {contract_config.name} contract")
            
            # Generate contract code
            contract_code, abi = contract_generator.generate_contract(contract_config)
            
            # Compile contract
            compiled_contract = self._compile_contract(contract_code, contract_config.name)
            
            # Get account from private key
            account = self.get_account_from_private_key(private_key)
            
            # Prepare constructor arguments
            constructor_args = self._prepare_constructor_args(contract_config, abi)
            
            # Create contract instance
            contract = self.w3.eth.contract(
                abi=abi,
                bytecode=compiled_contract['bytecode']
            )
            
            # Build transaction
            transaction = contract.constructor(*constructor_args).build_transaction({
                'from': account.address,
                'gas': deployment_config.gas_limit or 3000000,
                'gasPrice': deployment_config.gas_price or self.get_gas_price(),
                'nonce': deployment_config.nonce or self.w3.eth.get_transaction_count(account.address),
                'value': deployment_config.value
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Contract deployment transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = await self.wait_for_transaction_receipt(tx_hash.hex())
            
            if receipt['status'] != 1:
                raise Exception("Contract deployment failed")
            
            # Create contract info
            contract_info = ContractInfo(
                address=receipt['contractAddress'],
                name=contract_config.name,
                contract_type=contract_config.contract_type,
                network=self.network_config.network_type,
                deployment_tx=tx_hash.hex(),
                abi=abi,
                bytecode=compiled_contract['bytecode'],
                source_code=contract_code,
                compiler_version=contract_config.solidity_version,
                optimization_enabled=contract_config.optimization_enabled,
                deployed_at=datetime.utcnow().isoformat()
            )
            
            # Store deployed contract info
            self.deployed_contracts[contract_info.address] = contract_info
            
            logger.info(f"Contract {contract_config.name} deployed successfully at {contract_info.address}")
            
            return contract_info
            
        except Exception as e:
            logger.error(f"Error deploying contract: {str(e)}")
            raise
    
    def _compile_contract(self, source_code: str, contract_name: str) -> Dict[str, Any]:
        """Compile Solidity contract"""
        try:
            # Compile the contract
            compiled_sol = compile_source(source_code)
            
            # Get the contract interface
            contract_id = f'<stdin>:{contract_name}'
            contract_interface = compiled_sol[contract_id]
            
            return {
                'abi': contract_interface['abi'],
                'bytecode': contract_interface['bin']
            }
            
        except Exception as e:
            logger.error(f"Error compiling contract: {str(e)}")
            raise
    
    def _prepare_constructor_args(self, config: ContractConfig, abi: List[Dict[str, Any]]) -> List[Any]:
        """Prepare constructor arguments from config"""
        constructor_args = []
        
        # Find constructor in ABI
        constructor = next((item for item in abi if item.get('type') == 'constructor'), None)
        
        if constructor and constructor.get('inputs'):
            for input_param in constructor['inputs']:
                param_name = input_param['name']
                param_type = input_param['type']
                
                # Get value from constructor params or use defaults
                if param_name in config.constructor_params:
                    value = config.constructor_params[param_name]
                else:
                    # Provide default values based on type
                    if param_type == 'string':
                        value = config.name if param_name == 'name' else 'DEFAULT'
                    elif param_type.startswith('uint'):
                        value = 1000000 if 'supply' in param_name.lower() else 0
                    elif param_type == 'address':
                        value = '0x0000000000000000000000000000000000000000'
                    else:
                        value = 0
                
                constructor_args.append(value)
        
        return constructor_args
    
    async def call_contract_function(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: List[Any] = None,
        private_key: Optional[str] = None
    ) -> Any:
        """Call a contract function"""
        try:
            if not self.w3:
                raise ConnectionError("Web3 connection not initialized")
            
            contract = self.get_contract_instance(contract_address, abi)
            function = getattr(contract.functions, function_name)
            
            if args is None:
                args = []
            
            if private_key:
                # This is a transaction (state-changing function)
                account = self.get_account_from_private_key(private_key)
                
                # Build transaction
                transaction = function(*args).build_transaction({
                    'from': account.address,
                    'gas': 300000,
                    'gasPrice': self.get_gas_price(),
                    'nonce': self.w3.eth.get_transaction_count(account.address)
                })
                
                # Sign and send transaction
                signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                logger.info(f"Transaction sent: {tx_hash.hex()}")
                
                # Wait for receipt
                receipt = await self.wait_for_transaction_receipt(tx_hash.hex())
                
                return {
                    'transaction_hash': tx_hash.hex(),
                    'status': 'success' if receipt['status'] == 1 else 'failed',
                    'gas_used': receipt['gasUsed'],
                    'block_number': receipt['blockNumber']
                }
            else:
                # This is a call (read-only function)
                result = function(*args).call()
                return result
                
        except Exception as e:
            logger.error(f"Error calling contract function {function_name}: {str(e)}")
            raise
    
    async def get_transaction_status(self, tx_hash: str) -> TransactionInfo:
        """Get transaction status"""
        try:
            if not self.w3:
                raise ConnectionError("Web3 connection not initialized")
            
            try:
                # Try to get transaction receipt
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                
                # Get transaction details
                tx = self.w3.eth.get_transaction(tx_hash)
                
                # Calculate transaction fee
                gas_used = receipt.gasUsed
                gas_price = tx.gasPrice
                tx_fee = self.w3.from_wei(gas_used * gas_price, 'ether')
                
                # Determine status
                if receipt.status == 1:
                    status = TransactionStatus.CONFIRMED
                else:
                    status = TransactionStatus.REVERTED
                
                # Get confirmation count
                latest_block = self.w3.eth.block_number
                confirmation_count = latest_block - receipt.blockNumber + 1
                
                return TransactionInfo(
                    hash=tx_hash,
                    status=status,
                    block_number=receipt.blockNumber,
                    gas_used=gas_used,
                    gas_price=gas_price,
                    transaction_fee=str(tx_fee),
                    confirmation_count=confirmation_count,
                    created_at=datetime.utcnow().isoformat(),
                    confirmed_at=datetime.utcnow().isoformat()
                )
                
            except TransactionNotFound:
                # Transaction not found, might be pending
                return TransactionInfo(
                    hash=tx_hash,
                    status=TransactionStatus.PENDING,
                    confirmation_count=0,
                    created_at=datetime.utcnow().isoformat()
                )
                
        except Exception as e:
            logger.error(f"Error getting transaction status: {str(e)}")
            raise
    
    async def estimate_gas(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: List[Any] = None,
        from_address: Optional[str] = None
    ) -> int:
        """Estimate gas for a transaction"""
        try:
            if not self.w3:
                raise ConnectionError("Web3 connection not initialized")
            
            contract = self.get_contract_instance(contract_address, abi)
            function = getattr(contract.functions, function_name)
            
            if args is None:
                args = []
            
            # Estimate gas
            gas_estimate = function(*args).estimate_gas({
                'from': from_address or '0x0000000000000000000000000000000000000000'
            })
            
            return gas_estimate
            
        except Exception as e:
            logger.error(f"Error estimating gas: {str(e)}")
            raise
    
    def get_contract_events(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        event_name: str,
        from_block: int = 0,
        to_block: str = 'latest'
    ) -> List[Dict[str, Any]]:
        """Get contract events"""
        try:
            if not self.w3:
                raise ConnectionError("Web3 connection not initialized")
            
            contract = self.get_contract_instance(contract_address, abi)
            event_filter = getattr(contract.events, event_name).create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            
            events = event_filter.get_all_entries()
            
            return [
                {
                    'event': event_name,
                    'args': dict(event.args),
                    'transaction_hash': event.transactionHash.hex(),
                    'block_number': event.blockNumber,
                    'log_index': event.logIndex
                }
                for event in events
            ]
            
        except Exception as e:
            logger.error(f"Error getting contract events: {str(e)}")
            raise
    
    def get_deployed_contract(self, address: str) -> Optional[ContractInfo]:
        """Get deployed contract info"""
        return self.deployed_contracts.get(address)
    
    def list_deployed_contracts(self) -> List[ContractInfo]:
        """List all deployed contracts"""
        return list(self.deployed_contracts.values())
    
    async def verify_contract(
        self,
        contract_address: str,
        source_code: str,
        compiler_version: str,
        optimization_enabled: bool = True,
        etherscan_api_key: Optional[str] = None
    ) -> bool:
        """Verify contract on block explorer (placeholder implementation)"""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would integrate with Etherscan API
            # or other block explorer APIs for contract verification
            
            logger.info(f"Contract verification requested for {contract_address}")
            
            # Update contract info if it exists
            if contract_address in self.deployed_contracts:
                self.deployed_contracts[contract_address].verified = True
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying contract: {str(e)}")
            return False
    
    def save_contract_artifacts(
        self,
        contract_info: ContractInfo,
        output_dir: str = "./contracts/artifacts"
    ):
        """Save contract artifacts to files"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            contract_dir = output_path / contract_info.name
            contract_dir.mkdir(exist_ok=True)
            
            # Save source code
            if contract_info.source_code:
                with open(contract_dir / f"{contract_info.name}.sol", 'w') as f:
                    f.write(contract_info.source_code)
            
            # Save ABI
            with open(contract_dir / f"{contract_info.name}.abi.json", 'w') as f:
                json.dump(contract_info.abi, f, indent=2)
            
            # Save deployment info
            deployment_info = {
                'address': contract_info.address,
                'network': contract_info.network.value,
                'deployment_tx': contract_info.deployment_tx,
                'deployed_at': contract_info.deployed_at,
                'compiler_version': contract_info.compiler_version,
                'optimization_enabled': contract_info.optimization_enabled
            }
            
            with open(contract_dir / 'deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info(f"Contract artifacts saved to {contract_dir}")
            
        except Exception as e:
            logger.error(f"Error saving contract artifacts: {str(e)}")
            raise
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get current network information"""
        if not self.w3:
            raise ConnectionError("Web3 connection not initialized")
        
        latest_block = self.get_latest_block()
        
        return {
            'network_name': self.network_config.name,
            'network_type': self.network_config.network_type.value,
            'chain_id': self.network_config.chain_id,
            'currency_symbol': self.network_config.currency_symbol,
            'is_testnet': self.network_config.is_testnet,
            'rpc_url': self.network_config.rpc_url,
            'latest_block': latest_block,
            'gas_price': self.get_gas_price(),
            'is_connected': self.w3.is_connected()
        }

class Web3ProviderManager:
    """Manager for multiple Web3 providers"""
    
    def __init__(self):
        self.providers: Dict[NetworkType, Web3Provider] = {}
    
    def get_provider(self, network_type: NetworkType) -> Optional[Web3Provider]:
        """Get provider for a specific network"""
        return self.providers.get(network_type)
    
    def add_provider(self, network_config: NetworkConfig) -> Web3Provider:
        """Add a new provider"""
        provider = Web3Provider(network_config)
        self.providers[network_config.network_type] = provider
        logger.info(f"Added Web3 provider for {network_config.name}")
        return provider
    
    def remove_provider(self, network_type: NetworkType):
        """Remove a provider"""
        if network_type in self.providers:
            del self.providers[network_type]
            logger.info(f"Removed Web3 provider for {network_type.value}")
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """List all providers"""
        return [
            {
                'network_type': network_type.value,
                'network_info': provider.get_network_info()
            }
            for network_type, provider in self.providers.items()
        ]
    
    def get_all_deployed_contracts(self) -> Dict[str, List[ContractInfo]]:
        """Get all deployed contracts across all networks"""
        all_contracts = {}
        
        for network_type, provider in self.providers.items():
            contracts = provider.list_deployed_contracts()
            if contracts:
                all_contracts[network_type.value] = contracts
        
        return all_contracts

# Global provider manager instance
web3_provider_manager = Web3ProviderManager()