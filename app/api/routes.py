"""Main API routes for the multi-agent Web3 application builder."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..agents import AgentManager, AgentTask, AgentConfig, AgentType, agent_manager

from ..llm.manager import LLMManager
from ..web3 import Web3ProviderManager, ContractGenerator, NetworkType, ContractType
from ..core.config import get_settings

router = APIRouter()
settings = get_settings()

# Initialize managers
llm_manager = LLMManager()
web3_manager = Web3ProviderManager()
contract_generator = ContractGenerator()

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    tokens_used: Optional[int] = None

class SupervisorWorkflowRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    priority: int = 1
    requirements: Optional[Dict[str, Any]] = None

class SupervisorWorkflowResponse(BaseModel):
    workflow_id: str
    session_id: str
    status: str
    supervisor_analysis: Dict[str, Any]
    task_assignments: List[Dict[str, Any]]
    execution_results: Optional[Dict[str, Any]] = None
    final_output: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class AgentTaskRequest(BaseModel):
    task_type: str
    description: str
    parameters: Dict[str, Any] = {}
    agent_type: AgentType = AgentType.WEB3_BUILDER

class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ContractGenerationRequest(BaseModel):
    contract_type: ContractType
    name: str
    symbol: Optional[str] = None
    features: List[str] = []
    security_features: List[str] = []
    custom_parameters: Dict[str, Any] = {}

class ContractGenerationResponse(BaseModel):
    contract_code: str
    abi: List[Dict[str, Any]]
    deployment_bytecode: Optional[str] = None
    metadata: Dict[str, Any]

class DeploymentRequest(BaseModel):
    contract_code: str
    constructor_args: List[Any] = []
    network: NetworkType
    gas_limit: Optional[int] = None

class DeploymentResponse(BaseModel):
    transaction_hash: str
    contract_address: Optional[str] = None
    status: str
    gas_used: Optional[int] = None

# LLM Endpoints
@router.post("/llm/chat", response_model=ChatResponse)
async def chat_with_llm(request: ChatRequest):
    """Chat with LLM using specified or default provider."""
    try:
        if request.provider:
            await llm_manager.switch_provider(request.provider)
        
        if request.stream:
            # For streaming, we'll return a simple response for now
            # In a real implementation, you'd use Server-Sent Events
            response = await llm_manager.chat_completion(
                messages=[{"role": "user", "content": request.message}],
                model=request.model
            )
        else:
            response = await llm_manager.chat_completion(
                messages=[{"role": "user", "content": request.message}],
                model=request.model
            )
        
        return ChatResponse(
            response=response.content,
            provider=llm_manager.current_provider,
            model=response.model or "default",
            tokens_used=response.tokens_used
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/llm/providers")
async def get_llm_providers():
    """Get available LLM providers."""
    return {"providers": llm_manager.get_available_providers()}

@router.get("/llm/models")
async def get_llm_models(provider: Optional[str] = None):
    """Get available models for a provider."""
    try:
        models = await llm_manager.get_available_models(provider)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Supervisor Workflow Endpoint


@router.post("/llm/switch-provider")
async def switch_llm_provider(provider: str):
    """Switch to a different LLM provider."""
    try:
        await llm_manager.switch_provider(provider)
        return {"message": f"Switched to provider: {provider}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Agent Endpoints
@router.post("/agents/task", response_model=AgentTaskResponse)
async def execute_agent_task(request: AgentTaskRequest, background_tasks: BackgroundTasks):
    """Execute a task using the specified agent."""
    try:
        task = AgentTask(
            task_type=request.task_type,
            description=request.description,
            parameters=request.parameters
        )
        
        # Execute task in background
        task_id = await agent_manager.execute_task_async(request.agent_type, task)
        
        return AgentTaskResponse(
            task_id=task_id,
            status="running"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/task/{task_id}", response_model=AgentTaskResponse)
async def get_task_status(task_id: str):
    """Get the status of a running task."""
    try:
        status = await agent_manager.get_task_status(task_id)
        return AgentTaskResponse(
            task_id=task_id,
            status=status.get("status", "unknown"),
            result=status.get("result"),
            error=status.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/agents/types")
async def get_agent_types():
    """Get available agent types."""
    return {"agent_types": [agent_type.value for agent_type in AgentType]}

@router.get("/agents/status")
async def get_agents_status():
    """Get status of all agents."""
    return await agent_manager.get_system_status()

# Web3 Endpoints
@router.post("/web3/generate-contract", response_model=ContractGenerationResponse)
async def generate_contract(request: ContractGenerationRequest):
    """Generate a smart contract based on specifications."""
    try:
        contract_code = contract_generator.generate_contract(
            contract_type=request.contract_type,
            name=request.name,
            symbol=request.symbol,
            features=request.features,
            security_features=request.security_features,
            **request.custom_parameters
        )
        
        abi = contract_generator.generate_abi(
            contract_type=request.contract_type,
            features=request.features
        )
        
        return ContractGenerationResponse(
            contract_code=contract_code,
            abi=abi,
            metadata={
                "contract_type": request.contract_type.value,
                "features": request.features,
                "security_features": request.security_features
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/web3/deploy-contract", response_model=DeploymentResponse)
async def deploy_contract(request: DeploymentRequest):
    """Deploy a smart contract to the blockchain."""
    try:
        provider = web3_manager.get_provider(request.network)
        
        deployment_result = await provider.deploy_contract(
            contract_code=request.contract_code,
            constructor_args=request.constructor_args,
            gas_limit=request.gas_limit
        )
        
        return DeploymentResponse(
            transaction_hash=deployment_result["transaction_hash"],
            contract_address=deployment_result.get("contract_address"),
            status=deployment_result["status"],
            gas_used=deployment_result.get("gas_used")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/web3/networks")
async def get_supported_networks():
    """Get supported blockchain networks."""
    return {"networks": [network.value for network in NetworkType]}

@router.get("/web3/contract-types")
async def get_contract_types():
    """Get supported contract types."""
    return {"contract_types": contract_generator.get_supported_types()}

@router.get("/web3/contract-features")
async def get_contract_features(contract_type: ContractType):
    """Get available features for a contract type."""
    return {"features": contract_generator.get_available_features(contract_type)}

@router.get("/web3/transaction/{tx_hash}")
async def get_transaction_status(tx_hash: str, network: NetworkType):
    """Get transaction status."""
    try:
        provider = web3_manager.get_provider(network)
        status = await provider.get_transaction_status(tx_hash)
        return {"transaction_hash": tx_hash, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# System Endpoints
@router.get("/system/health")
async def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "llm_providers": llm_manager.get_available_providers(),
        "agents_status": "active",
        "web3_networks": [network.value for network in NetworkType]
    }

@router.get("/system/info")
async def system_info():
    """Get system information."""
    return {
        "version": "1.0.0",
        "components": {
            "llm_integration": True,
            "agent_framework": True,
            "web3_functionality": True
        },
        "supported_features": {
            "multi_llm_providers": True,
            "agent_workflows": True,
            "contract_generation": True,
            "blockchain_deployment": True,

        }
    }