"""
Aurora Pro AI - Task API Routes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ...agents.orchestrator import get_orchestrator
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger("api.tasks")


class TaskRequest(BaseModel):
    """Schema for a single task"""
    agent: str
    prompt: str
    parameters: Optional[Dict[str, Any]] = None


class TaskBatchRequest(BaseModel):
    """Schema for batch task execution"""
    tasks: List[TaskRequest]


@router.post("/execute")
async def execute_task(task: TaskRequest) -> Dict[str, Any]:
    """Execute a single task"""
    try:
        orchestrator = get_orchestrator()
        
        # Convert to dict format expected by orchestrator
        task_dict = {
            "agent": task.agent,
            "prompt": task.prompt,
            "parameters": task.parameters or {}
        }
        
        results = await orchestrator.execute([task_dict])
        
        if not results or len(results) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Task execution failed"
            )
        
        return results[0]
        
    except Exception as e:
        logger.error(f"Failed to execute task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/execute/batch")
async def execute_batch(batch: TaskBatchRequest) -> List[Dict[str, Any]]:
    """Execute multiple tasks"""
    try:
        orchestrator = get_orchestrator()
        
        # Convert tasks to dict format
        tasks = [
            {
                "agent": task.agent,
                "prompt": task.prompt,
                "parameters": task.parameters or {}
            }
            for task in batch.tasks
        ]
        
        results = await orchestrator.execute(tasks)
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to execute batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
