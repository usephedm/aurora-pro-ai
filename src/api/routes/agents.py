"""
Aurora Pro AI - Agent API Routes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ...agents.orchestrator import get_orchestrator
from ...agents.llm_agent import LLMAgent
from ...utils.model_loader import ModelProvider
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger("api.agents")


class AgentCreate(BaseModel):
    """Schema for creating a new agent"""
    name: str
    agent_type: str = "llm"
    model_name: str = "llama2"
    provider: str = "ollama"
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class TaskExecute(BaseModel):
    """Schema for executing a task"""
    agent: str
    prompt: str
    parameters: Optional[Dict[str, Any]] = None


@router.get("/")
async def list_agents() -> List[Dict[str, Any]]:
    """List all registered agents"""
    try:
        orchestrator = get_orchestrator()
        agents = orchestrator.list_agents()
        return agents
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate) -> Dict[str, Any]:
    """Create and register a new agent"""
    try:
        orchestrator = get_orchestrator()
        
        # Create agent based on type
        if agent_data.agent_type == "llm":
            agent = LLMAgent(
                name=agent_data.name,
                model_name=agent_data.model_name,
                provider=ModelProvider(agent_data.provider),
                description=agent_data.description or "LLM Agent",
                config=agent_data.config or {}
            )
        else:
            raise ValueError(f"Unsupported agent type: {agent_data.agent_type}")
        
        # Register with orchestrator
        success = orchestrator.register_agent(agent)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register agent"
            )
        
        return agent.get_info()
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{agent_name}")
async def get_agent(agent_name: str) -> Dict[str, Any]:
    """Get agent information"""
    try:
        orchestrator = get_orchestrator()
        agent = orchestrator.get_agent(agent_name)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_name} not found"
            )
        
        return agent.get_info()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{agent_name}")
async def delete_agent(agent_name: str) -> Dict[str, str]:
    """Unregister an agent"""
    try:
        orchestrator = get_orchestrator()
        success = orchestrator.unregister_agent(agent_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_name} not found"
            )
        
        return {"message": f"Agent {agent_name} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
