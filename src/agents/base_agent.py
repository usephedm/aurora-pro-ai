"""
Aurora Pro AI - Base Agent
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum

from ..core.logging import get_logger

logger = get_logger("agents")


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.created_at = datetime.utcnow()
        self.last_run = None
        logger.info(f"Agent initialized: {name}")
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task
        
        Args:
            task: Task dictionary with prompt and parameters
        
        Returns:
            Dict with execution results
        """
        pass
    
    def get_status(self) -> AgentStatus:
        """Get current agent status"""
        return self.status
    
    def set_status(self, status: AgentStatus) -> None:
        """Set agent status"""
        self.status = status
        logger.debug(f"Agent {self.name} status changed to {status}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None
        }
