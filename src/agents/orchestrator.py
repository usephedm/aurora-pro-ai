"""
Aurora Pro AI - Multi-Agent Orchestrator
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from enum import Enum

from .base_agent import BaseAgent, AgentStatus
from ..core.logging import get_logger
from ..core.config import get_settings

logger = get_logger("orchestrator")
settings = get_settings()


class OrchestrationMode(str, Enum):
    """Orchestration execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"


class MultiAgentOrchestrator:
    """Orchestrates multiple AI agents"""
    
    def __init__(self, mode: OrchestrationMode = OrchestrationMode.SEQUENTIAL):
        self.agents: Dict[str, BaseAgent] = {}
        self.mode = mode
        self.max_agents = settings.max_agents
        logger.info(f"Orchestrator initialized with mode: {mode}")
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """
        Register an agent with the orchestrator
        
        Args:
            agent: Agent instance to register
        
        Returns:
            bool: True if registration successful
        """
        try:
            if len(self.agents) >= self.max_agents:
                logger.warning(f"Max agents ({self.max_agents}) reached")
                return False
            
            if agent.name in self.agents:
                logger.warning(f"Agent {agent.name} already registered")
                return False
            
            self.agents[agent.name] = agent
            logger.info(f"Agent registered: {agent.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False
    
    def unregister_agent(self, agent_name: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_name in self.agents:
                del self.agents[agent_name]
                logger.info(f"Agent unregistered: {agent_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister agent: {e}")
            return False
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [agent.get_info() for agent in self.agents.values()]
    
    async def execute_sequential(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tasks sequentially"""
        results = []
        
        for task in tasks:
            agent_name = task.get("agent")
            if not agent_name or agent_name not in self.agents:
                logger.warning(f"Invalid agent: {agent_name}")
                results.append({
                    "status": "failed",
                    "error": f"Agent {agent_name} not found"
                })
                continue
            
            agent = self.agents[agent_name]
            result = await agent.execute(task)
            results.append(result)
        
        return results
    
    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tasks in parallel"""
        task_coroutines = []
        
        for task in tasks:
            agent_name = task.get("agent")
            if agent_name and agent_name in self.agents:
                agent = self.agents[agent_name]
                task_coroutines.append(agent.execute(task))
            else:
                logger.warning(f"Invalid agent: {agent_name}")
        
        if not task_coroutines:
            return []
        
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_pipeline(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute tasks in pipeline mode (output of one feeds into next)"""
        if not tasks:
            return {"status": "failed", "error": "No tasks provided"}
        
        current_output = None
        
        for i, task in enumerate(tasks):
            agent_name = task.get("agent")
            if not agent_name or agent_name not in self.agents:
                return {
                    "status": "failed",
                    "error": f"Agent {agent_name} not found",
                    "step": i
                }
            
            # Use output from previous step as input
            if current_output and i > 0:
                task["prompt"] = f"{task.get('prompt', '')} Context: {current_output.get('result', '')}"
            
            agent = self.agents[agent_name]
            current_output = await agent.execute(task)
            
            if current_output.get("status") == "failed":
                return current_output
        
        return current_output
    
    async def execute(self, tasks: List[Dict[str, Any]]) -> Any:
        """
        Execute tasks based on orchestration mode
        
        Args:
            tasks: List of task dictionaries with 'agent' and 'prompt'
        
        Returns:
            Results based on orchestration mode
        """
        start_time = datetime.utcnow()
        
        logger.info(
            f"Executing {len(tasks)} tasks in {self.mode} mode",
            extra={"task_count": len(tasks), "mode": self.mode}
        )
        
        try:
            if self.mode == OrchestrationMode.SEQUENTIAL:
                results = await self.execute_sequential(tasks)
            elif self.mode == OrchestrationMode.PARALLEL:
                results = await self.execute_parallel(tasks)
            elif self.mode == OrchestrationMode.PIPELINE:
                results = await self.execute_pipeline(tasks)
            else:
                results = {"status": "failed", "error": f"Invalid mode: {self.mode}"}
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Orchestration completed in {duration:.2f}s",
                extra={"duration": duration, "mode": self.mode}
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return {"status": "failed", "error": str(e)}


# Global orchestrator instance
_orchestrator: Optional[MultiAgentOrchestrator] = None


def get_orchestrator() -> MultiAgentOrchestrator:
    """Get global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        mode = OrchestrationMode(settings.orchestration_mode)
        _orchestrator = MultiAgentOrchestrator(mode=mode)
    return _orchestrator
