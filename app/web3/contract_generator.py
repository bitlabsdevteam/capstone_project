"""Smart contract code generation module"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
from pathlib import Path
import re
import json

from app.web3.base import ContractType, ContractConfig
from app.core.logging import logger

class SecurityFeature(Enum):
    """Available security features for contracts"""
    OWNABLE = "Ownable"
    PAUSABLE = "Pausable"
    REENTRANCY_GUARD = "ReentrancyGuard"
    ACCESS_CONTROL = "AccessControl"
    MULTISIG = "MultiSig"
    TIMELOCK = "Timelock"
    RATE_LIMITING = "RateLimiting"
    WHITELIST = "Whitelist"

class ContractFeature(Enum):
    """Available contract features"""
    MINTABLE = "Mintable"
    BURNABLE = "Burnable"
    CAPPED = "Capped"
    SNAPSHOT = "Snapshot"
    VOTES = "Votes"
    FLASH_MINT = "FlashMint"
    PERMIT = "Permit"
    ROYALTY = "Royalty"
    ENUMERABLE = "Enumerable"
    URI_STORAGE = "URIStorage"
    BATCH_TRANSFER = "BatchTransfer"

class ContractTemplate:
    """Base contract template class"""
    
    def __init__(self, config: ContractConfig):
        self.config = config
        self.imports: List[str] = []
        self.inheritance: List[str] = []
        self.state_variables: List[str] = []
        self.constructor_params: List[str] = []
        self.constructor_body: List[str] = []
        self.functions: List[str] = []
        self.events: List[str] = []
        self.modifiers: List[str] = []
    
    def add_import(self, import_statement: str):
        """Add import statement"""
        if import_statement not in self.imports:
            self.imports.append(import_statement)
    
    def add_inheritance(self, contract_name: str):
        """Add contract inheritance"""
        if contract_name not in self.inheritance:
            self.inheritance.append(contract_name)
    
    def add_state_variable(self, variable: str):
        """Add state variable"""
        self.state_variables.append(variable)
    
    def add_constructor_param(self, param: str):
        """Add constructor parameter"""
        self.constructor_params.append(param)
    
    def add_constructor_body(self, statement: str):
        """Add constructor body statement"""
        self.constructor_body.append(statement)
    
    def add_function(self, function: str):
        """Add function"""
        self.functions.append(function)
    
    def add_event(self, event: str):
        """Add event"""
        self.events.append(event)
    
    def add_modifier(self, modifier: str):
        """Add modifier"""
        self.modifiers.append(modifier)
    
    def generate_contract(self) -> str:
        """Generate complete contract code"""
        lines = []
        
        # SPDX License and pragma
        lines.append("// SPDX-License-Identifier: MIT")
        lines.append(f"pragma solidity ^{self.config.solidity_version};")
        lines.append("")
        
        # Imports
        for import_stmt in self.imports:
            lines.append(import_stmt)
        if self.imports:
            lines.append("")
        
        # Contract declaration
        inheritance_str = ""
        if self.inheritance:
            inheritance_str = f" is {', '.join(self.inheritance)}"
        
        lines.append(f"contract {self.config.name}{inheritance_str} {{")
        
        # Events
        if self.events:
            lines.append("    // Events")
            for event in self.events:
                lines.append(f"    {event}")
            lines.append("")
        
        # State variables
        if self.state_variables:
            lines.append("    // State variables")
            for var in self.state_variables:
                lines.append(f"    {var}")
            lines.append("")
        
        # Modifiers
        if self.modifiers:
            lines.append("    // Modifiers")
            for modifier in self.modifiers:
                lines.append(f"    {modifier}")
            lines.append("")
        
        # Constructor
        if self.constructor_params or self.constructor_body:
            constructor_params = ", ".join(self.constructor_params)
            lines.append(f"    constructor({constructor_params}) {{")
            for statement in self.constructor_body:
                lines.append(f"        {statement}")
            lines.append("    }")
            lines.append("")
        
        # Functions
        if self.functions:
            lines.append("    // Functions")
            for function in self.functions:
                lines.append(f"    {function}")
                lines.append("")
        
        lines.append("}")
        
        return "\n".join(lines)

class ERC20Template(ContractTemplate):
    """ERC20 token contract template"""
    
    def __init__(self, config: ContractConfig):
        super().__init__(config)
        self._setup_base_erc20()
        self._apply_features()
        self._apply_security_features()
    
    def _setup_base_erc20(self):
        """Setup base ERC20 functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC20/ERC20.sol";')
        self.add_inheritance("ERC20")
        
        # Constructor parameters
        name = self.config.constructor_params.get("name", self.config.name)
        symbol = self.config.constructor_params.get("symbol", "TKN")
        initial_supply = self.config.constructor_params.get("initial_supply", "1000000")
        
        self.add_constructor_param(f'string memory name')
        self.add_constructor_param(f'string memory symbol')
        self.add_constructor_param(f'uint256 initialSupply')
        
        self.add_constructor_body('ERC20(name, symbol) {')
        self.add_constructor_body('    _mint(msg.sender, initialSupply * 10**decimals());')
        self.add_constructor_body('}')
    
    def _apply_features(self):
        """Apply selected features"""
        for feature in self.config.features:
            if feature == ContractFeature.MINTABLE.value:
                self._add_mintable()
            elif feature == ContractFeature.BURNABLE.value:
                self._add_burnable()
            elif feature == ContractFeature.CAPPED.value:
                self._add_capped()
            elif feature == ContractFeature.SNAPSHOT.value:
                self._add_snapshot()
            elif feature == ContractFeature.VOTES.value:
                self._add_votes()
            elif feature == ContractFeature.PERMIT.value:
                self._add_permit()
    
    def _apply_security_features(self):
        """Apply security features"""
        for feature in self.config.security_features:
            if feature == SecurityFeature.OWNABLE.value:
                self._add_ownable()
            elif feature == SecurityFeature.PAUSABLE.value:
                self._add_pausable()
            elif feature == SecurityFeature.ACCESS_CONTROL.value:
                self._add_access_control()
    
    def _add_mintable(self):
        """Add mintable functionality"""
        self.add_function('''
function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }''')
    
    def _add_burnable(self):
        """Add burnable functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";')
        self.add_inheritance("ERC20Burnable")
    
    def _add_capped(self):
        """Add capped supply functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol";')
        self.add_inheritance("ERC20Capped")
        
        cap = self.config.constructor_params.get("cap", "10000000")
        self.add_constructor_param(f'uint256 cap')
        self.add_constructor_body(f'ERC20Capped(cap * 10**decimals())')
    
    def _add_snapshot(self):
        """Add snapshot functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Snapshot.sol";')
        self.add_inheritance("ERC20Snapshot")
        
        self.add_function('''
function snapshot() public onlyOwner {
        _snapshot();
    }''')
    
    def _add_votes(self):
        """Add voting functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";')
        self.add_inheritance("ERC20Votes")
        
        self.add_function('''
function _afterTokenTransfer(address from, address to, uint256 amount)
        internal
        override(ERC20, ERC20Votes)
    {
        super._afterTokenTransfer(from, to, amount);
    }

    function _mint(address to, uint256 amount)
        internal
        override(ERC20, ERC20Votes)
    {
        super._mint(to, amount);
    }

    function _burn(address account, uint256 amount)
        internal
        override(ERC20, ERC20Votes)
    {
        super._burn(account, amount);
    }''')
    
    def _add_permit(self):
        """Add permit functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";')
        self.add_inheritance("ERC20Permit")
        
        self.add_constructor_body('ERC20Permit(name)')
    
    def _add_ownable(self):
        """Add ownable functionality"""
        self.add_import('import "@openzeppelin/contracts/access/Ownable.sol";')
        self.add_inheritance("Ownable")
        
        self.add_constructor_body('Ownable(msg.sender)')
    
    def _add_pausable(self):
        """Add pausable functionality"""
        self.add_import('import "@openzeppelin/contracts/security/Pausable.sol";')
        self.add_inheritance("Pausable")
        
        self.add_function('''
function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function _beforeTokenTransfer(address from, address to, uint256 amount)
        internal
        whenNotPaused
        override
    {
        super._beforeTokenTransfer(from, to, amount);
    }''')
    
    def _add_access_control(self):
        """Add access control functionality"""
        self.add_import('import "@openzeppelin/contracts/access/AccessControl.sol";')
        self.add_inheritance("AccessControl")
        
        self.add_state_variable('bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");')
        self.add_state_variable('bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");')
        
        self.add_constructor_body('_grantRole(DEFAULT_ADMIN_ROLE, msg.sender);')
        self.add_constructor_body('_grantRole(MINTER_ROLE, msg.sender);')

class ERC721Template(ContractTemplate):
    """ERC721 NFT contract template"""
    
    def __init__(self, config: ContractConfig):
        super().__init__(config)
        self._setup_base_erc721()
        self._apply_features()
        self._apply_security_features()
    
    def _setup_base_erc721(self):
        """Setup base ERC721 functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC721/ERC721.sol";')
        self.add_inheritance("ERC721")
        
        # State variables
        self.add_state_variable('uint256 private _nextTokenId;')
        
        # Constructor
        name = self.config.constructor_params.get("name", self.config.name)
        symbol = self.config.constructor_params.get("symbol", "NFT")
        
        self.add_constructor_param('string memory name')
        self.add_constructor_param('string memory symbol')
        self.add_constructor_body('ERC721(name, symbol) {}')
    
    def _apply_features(self):
        """Apply selected features"""
        for feature in self.config.features:
            if feature == ContractFeature.MINTABLE.value:
                self._add_mintable()
            elif feature == ContractFeature.BURNABLE.value:
                self._add_burnable()
            elif feature == ContractFeature.ENUMERABLE.value:
                self._add_enumerable()
            elif feature == ContractFeature.URI_STORAGE.value:
                self._add_uri_storage()
            elif feature == ContractFeature.ROYALTY.value:
                self._add_royalty()
    
    def _apply_security_features(self):
        """Apply security features"""
        for feature in self.config.security_features:
            if feature == SecurityFeature.OWNABLE.value:
                self._add_ownable()
            elif feature == SecurityFeature.PAUSABLE.value:
                self._add_pausable()
    
    def _add_mintable(self):
        """Add mintable functionality"""
        self.add_function('''
function safeMint(address to) public onlyOwner {
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
    }

    function safeMint(address to, string memory uri) public onlyOwner {
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
    }''')
    
    def _add_burnable(self):
        """Add burnable functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";')
        self.add_inheritance("ERC721Burnable")
    
    def _add_enumerable(self):
        """Add enumerable functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";')
        self.add_inheritance("ERC721Enumerable")
        
        self.add_function('''
function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize)
        internal
        override(ERC721, ERC721Enumerable)
    {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }''')
    
    def _add_uri_storage(self):
        """Add URI storage functionality"""
        self.add_import('import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";')
        self.add_inheritance("ERC721URIStorage")
        
        self.add_function('''
function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }''')
    
    def _add_royalty(self):
        """Add royalty functionality"""
        self.add_import('import "@openzeppelin/contracts/token/common/ERC2981.sol";')
        self.add_inheritance("ERC2981")
        
        royalty_fee = self.config.constructor_params.get("royalty_fee", "250")  # 2.5%
        
        self.add_constructor_body(f'_setDefaultRoyalty(msg.sender, {royalty_fee});')
        
        self.add_function('''
function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }''')
    
    def _add_ownable(self):
        """Add ownable functionality"""
        self.add_import('import "@openzeppelin/contracts/access/Ownable.sol";')
        self.add_inheritance("Ownable")
        
        self.add_constructor_body('Ownable(msg.sender)')
    
    def _add_pausable(self):
        """Add pausable functionality"""
        self.add_import('import "@openzeppelin/contracts/security/Pausable.sol";')
        self.add_inheritance("Pausable")
        
        self.add_function('''
function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize)
        internal
        whenNotPaused
        override
    {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }''')

class ContractGenerator:
    """Main contract generator class"""
    
    def __init__(self):
        self.templates = {
            ContractType.ERC20: ERC20Template,
            ContractType.ERC721: ERC721Template,
            # Add more templates as needed
        }
    
    def generate_contract(self, config: ContractConfig) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate smart contract code and ABI"""
        try:
            if config.contract_type not in self.templates:
                raise ValueError(f"Unsupported contract type: {config.contract_type}")
            
            template_class = self.templates[config.contract_type]
            template = template_class(config)
            
            # Generate contract code
            contract_code = template.generate_contract()
            
            # Generate basic ABI (simplified for now)
            abi = self._generate_basic_abi(config)
            
            logger.info(f"Generated {config.contract_type.value} contract: {config.name}")
            
            return contract_code, abi
            
        except Exception as e:
            logger.error(f"Error generating contract: {str(e)}")
            raise
    
    def _generate_basic_abi(self, config: ContractConfig) -> List[Dict[str, Any]]:
        """Generate basic ABI for the contract"""
        abi = []
        
        if config.contract_type == ContractType.ERC20:
            abi = [
                {
                    "inputs": [
                        {"internalType": "string", "name": "name", "type": "string"},
                        {"internalType": "string", "name": "symbol", "type": "string"},
                        {"internalType": "uint256", "name": "initialSupply", "type": "uint256"}
                    ],
                    "stateMutability": "nonpayable",
                    "type": "constructor"
                },
                {
                    "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "address", "name": "to", "type": "address"},
                        {"internalType": "uint256", "name": "amount", "type": "uint256"}
                    ],
                    "name": "transfer",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]
        
        elif config.contract_type == ContractType.ERC721:
            abi = [
                {
                    "inputs": [
                        {"internalType": "string", "name": "name", "type": "string"},
                        {"internalType": "string", "name": "symbol", "type": "string"}
                    ],
                    "stateMutability": "nonpayable",
                    "type": "constructor"
                },
                {
                    "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
                    "name": "ownerOf",
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
        
        # Add custom functions from config
        for custom_func in config.custom_functions:
            abi.append(custom_func)
        
        return abi
    
    def validate_contract_config(self, config: ContractConfig) -> List[str]:
        """Validate contract configuration"""
        errors = []
        
        # Validate contract name
        if not config.name or not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', config.name):
            errors.append("Contract name must be a valid identifier")
        
        # Validate Solidity version
        if not re.match(r'^\d+\.\d+\.\d+$', config.solidity_version):
            errors.append("Invalid Solidity version format")
        
        # Validate features
        valid_features = [f.value for f in ContractFeature]
        for feature in config.features:
            if feature not in valid_features:
                errors.append(f"Unknown feature: {feature}")
        
        # Validate security features
        valid_security_features = [f.value for f in SecurityFeature]
        for feature in config.security_features:
            if feature not in valid_security_features:
                errors.append(f"Unknown security feature: {feature}")
        
        return errors
    
    def get_available_features(self, contract_type: ContractType) -> Dict[str, List[str]]:
        """Get available features for a contract type"""
        if contract_type == ContractType.ERC20:
            return {
                "features": [
                    ContractFeature.MINTABLE.value,
                    ContractFeature.BURNABLE.value,
                    ContractFeature.CAPPED.value,
                    ContractFeature.SNAPSHOT.value,
                    ContractFeature.VOTES.value,
                    ContractFeature.PERMIT.value
                ],
                "security_features": [
                    SecurityFeature.OWNABLE.value,
                    SecurityFeature.PAUSABLE.value,
                    SecurityFeature.ACCESS_CONTROL.value,
                    SecurityFeature.REENTRANCY_GUARD.value
                ]
            }
        
        elif contract_type == ContractType.ERC721:
            return {
                "features": [
                    ContractFeature.MINTABLE.value,
                    ContractFeature.BURNABLE.value,
                    ContractFeature.ENUMERABLE.value,
                    ContractFeature.URI_STORAGE.value,
                    ContractFeature.ROYALTY.value
                ],
                "security_features": [
                    SecurityFeature.OWNABLE.value,
                    SecurityFeature.PAUSABLE.value,
                    SecurityFeature.ACCESS_CONTROL.value
                ]
            }
        
        return {"features": [], "security_features": []}
    
    def get_supported_contract_types(self) -> List[str]:
        """Get list of supported contract types"""
        return [ct.value for ct in self.templates.keys()]

# Global contract generator instance
contract_generator = ContractGenerator()