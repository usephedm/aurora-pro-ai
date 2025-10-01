"""
Aurora Pro AI - LLM Agent
"""
from typing import Any, Dict
from datetime import datetime

from .base_agent import BaseAgent, AgentStatus
from ..core.logging import get_logger
from ..utils.model_loader import get_model_loader, ModelProvider

logger = get_logger("agents.llm")


class LLMAgent(BaseAgent):
    """Agent for Large Language Model interactions"""
    
    def __init__(
        self,
        name: str,
        model_name: str = "llama2",
        provider: ModelProvider = ModelProvider.OLLAMA,
        description: str = "LLM Agent for text generation",
        config: Dict[str, Any] = None
    ):
        super().__init__(name, description, config)
        self.model_name = model_name
        self.provider = provider
        self.model_loader = get_model_loader()
        
        # Ensure model is loaded
        self.model_loader.load_model(model_name, provider, config)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LLM task
        
        Args:
            task: Task with 'prompt' and optional 'parameters'
        
        Returns:
            Dict with 'result', 'status', and metadata
        """
        self.set_status(AgentStatus.RUNNING)
        self.last_run = datetime.utcnow()
        
        try:
            prompt = task.get("prompt", "")
            parameters = task.get("parameters", {})
            
            if not prompt:
                raise ValueError("Prompt is required")
            
            logger.info(
                f"Executing LLM task",
                extra={
                    "agent": self.name,
                    "model": self.model_name,
                    "prompt_length": len(prompt)
                }
            )
            
            # Simulate LLM response (in production, call actual LLM API)
            result = {
                "result": f"Processed by {self.model_name}: {prompt[:50]}...",
                "status": "completed",
                "model": self.model_name,
                "provider": self.provider,
                "tokens_used": len(prompt.split()),
                "completed_at": datetime.utcnow().isoformat()
            }
            
            self.set_status(AgentStatus.COMPLETED)
            logger.info(f"LLM task completed", extra={"agent": self.name})
            
            return result
            
        except Exception as e:
            self.set_status(AgentStatus.FAILED)
            logger.error(f"LLM task failed: {e}", extra={"agent": self.name})
            return {
                "result": None,
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }
