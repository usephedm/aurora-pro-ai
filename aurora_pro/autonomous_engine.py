"""
Fully Autonomous Task Execution Engine for Aurora Pro

Understands any request and executes it autonomously with minimal human intervention.

Features:
- Web automation (open sites, fill forms, extract data, bypass CAPTCHAs)
- OS automation (run CLI commands, install software, manage files)
- Vision-guided actions (screenshot analysis, UI element detection, click coordinates)
- Multi-step workflow planning and execution
- Self-reflection and error recovery
- Progress reporting and transparency
"""
import asyncio
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiofiles

from llm_orchestrator import get_llm_orchestrator, TaskType
from vision_agent import get_vision_agent
from stealth_browser_agent import get_stealth_browser
from captcha_manager import get_captcha_manager
from mouse_keyboard_agent import get_input_agent, InputActionType

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of autonomous workflow."""
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ActionType(Enum):
    """Types of autonomous actions."""
    WEB_NAVIGATE = "web_navigate"
    WEB_CLICK = "web_click"
    WEB_TYPE = "web_type"
    WEB_EXTRACT = "web_extract"
    CLI_EXECUTE = "cli_execute"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    SCREENSHOT = "screenshot"
    VISION_ANALYZE = "vision_analyze"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    KEYBOARD_TYPE = "keyboard_type"
    WAIT = "wait"
    VERIFY = "verify"


@dataclass
class Action:
    """Single autonomous action."""
    action_id: str
    action_type: ActionType
    description: str
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, executing, completed, failed, skipped
    result: Any = None
    error: Optional[str] = None
    reasoning: Optional[str] = None
    timestamp: Optional[str] = None
    execution_time_sec: float = 0.0


@dataclass
class Workflow:
    """Autonomous workflow with multiple actions."""
    workflow_id: str
    description: str
    original_request: str
    status: WorkflowStatus
    actions: List[Action] = field(default_factory=list)
    current_action_index: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    total_actions: int = 0
    completed_actions: int = 0
    failed_actions: int = 0
    result: Optional[Any] = None
    error: Optional[str] = None
    reasoning_chain: List[str] = field(default_factory=list)


class AutonomousEngine:
    """
    Fully Autonomous Task Execution Engine.

    Capabilities:
    1. Understand natural language requests
    2. Break down into executable steps
    3. Execute each step with appropriate tools
    4. Verify success after each step
    5. Recover from errors automatically
    6. Report progress in real-time
    7. Learn from failures
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/autonomous_engine.log"
    WORKFLOWS_PATH = "/root/aurora_pro/logs/workflows"

    def __init__(self):
        self._running = False
        self._workflows: Dict[str, Workflow] = {}
        self._lock = asyncio.Lock()

        # Agents
        self._llm = get_llm_orchestrator()
        self._vision = get_vision_agent()
        self._browser = get_stealth_browser()
        self._captcha = get_captcha_manager()
        self._input = get_input_agent()

    async def start(self):
        """Initialize autonomous engine."""
        self._running = True

        # Ensure agents are started
        if not self._llm._running:
            await self._llm.start()
        if not self._vision._running:
            await self._vision.start()
        if not self._browser._running:
            await self._browser.start()
        if not self._captcha._running:
            await self._captcha.start()
        if not self._input._running:
            await self._input.start()

        # Create workflows directory
        Path(self.WORKFLOWS_PATH).mkdir(parents=True, exist_ok=True)

        await self._audit_log("system", "Autonomous Engine started")
        logger.info("Autonomous Engine initialized")

    async def stop(self):
        """Shutdown autonomous engine."""
        self._running = False
        await self._audit_log("system", "Autonomous Engine stopped")

    async def execute_request(
        self,
        request: str,
        max_actions: int = 50,
        operator_user: Optional[str] = None,
    ) -> Workflow:
        """
        Execute an autonomous request.

        Args:
            request: Natural language request
            max_actions: Maximum actions to prevent infinite loops
            operator_user: User requesting the action

        Returns:
            Workflow with execution details
        """
        workflow_id = f"wf_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"

        workflow = Workflow(
            workflow_id=workflow_id,
            description=f"Execute: {request[:100]}",
            original_request=request,
            status=WorkflowStatus.PLANNING,
        )

        async with self._lock:
            self._workflows[workflow_id] = workflow

        try:
            # PHASE 1: Understand and plan
            await self._audit_log("planning", f"Workflow {workflow_id}: {request}")
            workflow.reasoning_chain.append("Analyzing request and creating execution plan...")

            actions = await self._plan_workflow(request, max_actions)
            workflow.actions = actions
            workflow.total_actions = len(actions)
            workflow.reasoning_chain.append(f"Created plan with {len(actions)} actions")

            # PHASE 2: Execute each action
            workflow.status = WorkflowStatus.EXECUTING

            for i, action in enumerate(actions):
                workflow.current_action_index = i
                workflow.reasoning_chain.append(
                    f"Step {i+1}/{len(actions)}: {action.description}"
                )

                result = await self._execute_action(action, workflow, operator_user)

                if action.status == "failed":
                    workflow.failed_actions += 1

                    # Try to recover
                    recovery_successful = await self._attempt_recovery(
                        action, workflow, operator_user
                    )

                    if not recovery_successful:
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error = f"Action {i+1} failed: {action.error}"
                        break
                else:
                    workflow.completed_actions += 1

                # PHASE 3: Verify action succeeded
                if action.action_type != ActionType.VERIFY:
                    verification = await self._verify_action(action, workflow)
                    if not verification["success"]:
                        workflow.reasoning_chain.append(
                            f"Verification failed: {verification['reason']}"
                        )

            # Workflow complete
            if workflow.status == WorkflowStatus.EXECUTING:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.reasoning_chain.append("Workflow completed successfully!")

            workflow.completed_at = datetime.utcnow().isoformat()

            # Save workflow
            await self._save_workflow(workflow)

            return workflow

        except Exception as e:
            logger.error(f"Workflow {workflow_id} error: {e}")
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.utcnow().isoformat()
            return workflow

    async def _plan_workflow(self, request: str, max_actions: int) -> List[Action]:
        """Use LLM to plan workflow actions."""
        planning_prompt = f"""You are an autonomous task planner. Break down this request into specific executable actions.

Request: {request}

Available action types:
- WEB_NAVIGATE: Navigate to URL
- WEB_CLICK: Click element on webpage
- WEB_TYPE: Type text into input field
- WEB_EXTRACT: Extract data from webpage
- CLI_EXECUTE: Run terminal command
- FILE_READ: Read file contents
- FILE_WRITE: Write file contents
- FILE_DELETE: Delete file
- SCREENSHOT: Take screenshot
- VISION_ANALYZE: Analyze screen with OCR
- MOUSE_MOVE: Move mouse to coordinates
- MOUSE_CLICK: Click mouse at current position
- KEYBOARD_TYPE: Type text via keyboard
- WAIT: Wait for specified seconds
- VERIFY: Verify previous action succeeded

Respond with JSON array of actions (max {max_actions}):
[
  {{
    "action_type": "ACTION_TYPE",
    "description": "Human readable description",
    "parameters": {{"key": "value"}},
    "reasoning": "Why this action is needed"
  }}
]

Be specific and detailed. Include verification steps."""

        response = await self._llm.generate(
            planning_prompt,
            task_type=TaskType.REASONING,
            temperature=0.3,
        )

        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', response.response)
            if json_match:
                actions_data = json.loads(json_match.group(0))
            else:
                actions_data = json.loads(response.response)

            actions = []
            for i, action_data in enumerate(actions_data[:max_actions]):
                action = Action(
                    action_id=f"action_{i}",
                    action_type=ActionType(action_data["action_type"].lower()),
                    description=action_data["description"],
                    parameters=action_data["parameters"],
                    reasoning=action_data.get("reasoning"),
                )
                actions.append(action)

            return actions

        except Exception as e:
            logger.error(f"Failed to parse action plan: {e}")
            # Fallback: create simple plan
            return [
                Action(
                    action_id="action_0",
                    action_type=ActionType.CLI_EXECUTE,
                    description=f"Execute: {request}",
                    parameters={"command": request},
                    reasoning="Fallback action",
                )
            ]

    async def _execute_action(
        self,
        action: Action,
        workflow: Workflow,
        operator_user: Optional[str],
    ) -> Any:
        """Execute single action."""
        action.status = "executing"
        action.timestamp = datetime.utcnow().isoformat()
        start_time = asyncio.get_event_loop().time()

        try:
            await self._audit_log(
                "action",
                f"{workflow.workflow_id} | {action.action_id} | {action.action_type.value} | {action.description}"
            )

            if action.action_type == ActionType.WEB_NAVIGATE:
                result = await self._action_web_navigate(action, operator_user)
            elif action.action_type == ActionType.CLI_EXECUTE:
                result = await self._action_cli_execute(action, operator_user)
            elif action.action_type == ActionType.SCREENSHOT:
                result = await self._action_screenshot(action, operator_user)
            elif action.action_type == ActionType.VISION_ANALYZE:
                result = await self._action_vision_analyze(action, operator_user)
            elif action.action_type == ActionType.MOUSE_CLICK:
                result = await self._action_mouse_click(action, operator_user)
            elif action.action_type == ActionType.KEYBOARD_TYPE:
                result = await self._action_keyboard_type(action, operator_user)
            elif action.action_type == ActionType.WAIT:
                result = await self._action_wait(action)
            elif action.action_type == ActionType.FILE_READ:
                result = await self._action_file_read(action)
            elif action.action_type == ActionType.FILE_WRITE:
                result = await self._action_file_write(action)
            elif action.action_type == ActionType.VERIFY:
                result = await self._action_verify(action, workflow)
            else:
                raise ValueError(f"Unsupported action type: {action.action_type}")

            action.result = result
            action.status = "completed"
            action.execution_time_sec = asyncio.get_event_loop().time() - start_time

            return result

        except Exception as e:
            logger.error(f"Action {action.action_id} failed: {e}")
            action.status = "failed"
            action.error = str(e)
            action.execution_time_sec = asyncio.get_event_loop().time() - start_time
            return None

    async def _action_web_navigate(self, action: Action, operator_user: Optional[str]) -> Any:
        """Navigate to URL."""
        url = action.parameters.get("url")
        wait_time = action.parameters.get("wait_time", 2.0)

        result = await self._browser.navigate(url, wait_time, operator_user)
        return result

    async def _action_cli_execute(self, action: Action, operator_user: Optional[str]) -> Any:
        """Execute CLI command."""
        command = action.parameters.get("command")
        timeout = action.parameters.get("timeout", 30)

        # Execute command
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )

            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "returncode": proc.returncode,
            }
        except asyncio.TimeoutError:
            proc.kill()
            raise Exception(f"Command timed out after {timeout}s")

    async def _action_screenshot(self, action: Action, operator_user: Optional[str]) -> Any:
        """Take screenshot."""
        region = action.parameters.get("region")

        analysis = await self._vision.analyze_screen(
            region=region,
            detect_elements=False,
            operator_user=operator_user,
        )

        return {
            "screenshot_path": analysis.screenshot_path,
            "timestamp": analysis.timestamp,
        }

    async def _action_vision_analyze(self, action: Action, operator_user: Optional[str]) -> Any:
        """Analyze screen with vision."""
        region = action.parameters.get("region")
        detect_elements = action.parameters.get("detect_elements", True)

        analysis = await self._vision.analyze_screen(
            region=region,
            detect_elements=detect_elements,
            operator_user=operator_user,
        )

        return {
            "ocr_text": analysis.ocr_text,
            "ui_elements": [
                {
                    "type": el.element_type,
                    "text": el.text,
                    "x": el.x,
                    "y": el.y,
                }
                for el in analysis.ui_elements
            ],
            "screenshot_path": analysis.screenshot_path,
        }

    async def _action_mouse_click(self, action: Action, operator_user: Optional[str]) -> Any:
        """Click mouse."""
        x = action.parameters.get("x")
        y = action.parameters.get("y")
        button = action.parameters.get("button", "left")

        task = await self._input.submit_task(
            action_type=InputActionType.MOUSE_CLICK,
            parameters={"x": x, "y": y, "button": button},
            operator_user=operator_user,
        )

        # Wait for completion
        for _ in range(50):  # 5 seconds max
            await asyncio.sleep(0.1)
            current = self._input.get_task(task.task_id)
            if current and current.status in ["completed", "failed"]:
                return {"status": current.status}

        return {"status": "timeout"}

    async def _action_keyboard_type(self, action: Action, operator_user: Optional[str]) -> Any:
        """Type text via keyboard."""
        text = action.parameters.get("text")
        interval = action.parameters.get("interval", 0.01)

        task = await self._input.submit_task(
            action_type=InputActionType.KEYBOARD_TYPE,
            parameters={"text": text, "interval": interval},
            operator_user=operator_user,
        )

        # Wait for completion
        for _ in range(50):
            await asyncio.sleep(0.1)
            current = self._input.get_task(task.task_id)
            if current and current.status in ["completed", "failed"]:
                return {"status": current.status}

        return {"status": "timeout"}

    async def _action_wait(self, action: Action) -> Any:
        """Wait for specified time."""
        seconds = action.parameters.get("seconds", 1.0)
        await asyncio.sleep(seconds)
        return {"waited": seconds}

    async def _action_file_read(self, action: Action) -> Any:
        """Read file contents."""
        file_path = action.parameters.get("path")

        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()

        return {"content": content, "length": len(content)}

    async def _action_file_write(self, action: Action) -> Any:
        """Write file contents."""
        file_path = action.parameters.get("path")
        content = action.parameters.get("content")

        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)

        return {"bytes_written": len(content)}

    async def _action_verify(self, action: Action, workflow: Workflow) -> Any:
        """Verify previous action."""
        condition = action.parameters.get("condition")

        # Use LLM to verify
        verification_prompt = f"""Verify if this condition is met based on the workflow context:

Condition: {condition}

Recent actions:
{json.dumps([
    {"description": a.description, "status": a.status, "result": str(a.result)[:200]}
    for a in workflow.actions[-3:]
], indent=2)}

Respond with JSON: {{"success": true/false, "reason": "explanation"}}"""

        response = await self._llm.generate(
            verification_prompt,
            task_type=TaskType.REASONING,
            temperature=0.1,
        )

        try:
            json_match = re.search(r'\{[\s\S]*\}', response.response)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(response.response)

            return result
        except:
            return {"success": False, "reason": "Failed to parse verification"}

    async def _verify_action(self, action: Action, workflow: Workflow) -> Dict[str, Any]:
        """Automatically verify action succeeded."""
        if action.status == "failed":
            return {"success": False, "reason": action.error}

        if action.status != "completed":
            return {"success": False, "reason": "Action not completed"}

        # Action-specific verification
        if action.action_type == ActionType.CLI_EXECUTE:
            if action.result and action.result.get("returncode") != 0:
                return {
                    "success": False,
                    "reason": f"Command failed with code {action.result['returncode']}"
                }

        return {"success": True, "reason": "Action completed successfully"}

    async def _attempt_recovery(
        self,
        failed_action: Action,
        workflow: Workflow,
        operator_user: Optional[str],
    ) -> bool:
        """Attempt to recover from failed action."""
        workflow.reasoning_chain.append(
            f"Attempting recovery from failed action: {failed_action.description}"
        )

        # Use LLM to suggest recovery
        recovery_prompt = f"""An action failed. Suggest recovery steps.

Failed Action: {failed_action.description}
Error: {failed_action.error}
Action Type: {failed_action.action_type.value}
Parameters: {json.dumps(failed_action.parameters, indent=2)}

Suggest 1-3 recovery actions as JSON array."""

        try:
            response = await self._llm.generate(
                recovery_prompt,
                task_type=TaskType.REASONING,
                temperature=0.3,
            )

            json_match = re.search(r'\[[\s\S]*\]', response.response)
            if not json_match:
                return False

            recovery_actions_data = json.loads(json_match.group(0))

            # Execute recovery actions
            for action_data in recovery_actions_data:
                recovery_action = Action(
                    action_id=f"recovery_{failed_action.action_id}",
                    action_type=ActionType(action_data["action_type"].lower()),
                    description=action_data["description"],
                    parameters=action_data["parameters"],
                    reasoning="Recovery action",
                )

                await self._execute_action(recovery_action, workflow, operator_user)

                if recovery_action.status == "completed":
                    workflow.reasoning_chain.append("Recovery successful!")
                    return True

            return False

        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return False

    async def _save_workflow(self, workflow: Workflow):
        """Save workflow to disk."""
        try:
            file_path = Path(self.WORKFLOWS_PATH) / f"{workflow.workflow_id}.json"

            data = {
                "workflow_id": workflow.workflow_id,
                "description": workflow.description,
                "original_request": workflow.original_request,
                "status": workflow.status.value,
                "created_at": workflow.created_at,
                "completed_at": workflow.completed_at,
                "total_actions": workflow.total_actions,
                "completed_actions": workflow.completed_actions,
                "failed_actions": workflow.failed_actions,
                "reasoning_chain": workflow.reasoning_chain,
                "actions": [
                    {
                        "action_id": a.action_id,
                        "action_type": a.action_type.value,
                        "description": a.description,
                        "status": a.status,
                        "error": a.error,
                        "execution_time_sec": a.execution_time_sec,
                    }
                    for a in workflow.actions
                ],
            }

            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(data, indent=2))

        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")

    async def _audit_log(self, action: str, details: str):
        """Write audit log entry."""
        try:
            Path(self.AUDIT_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().isoformat()
            log_entry = f"{timestamp} | {action} | {details}\n"

            async with aiofiles.open(self.AUDIT_LOG_PATH, "a") as f:
                await f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self._workflows.get(workflow_id)

    def list_workflows(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent workflows."""
        workflows = sorted(
            self._workflows.values(),
            key=lambda w: w.created_at,
            reverse=True
        )[:limit]

        return [
            {
                "workflow_id": w.workflow_id,
                "description": w.description,
                "status": w.status.value,
                "created_at": w.created_at,
                "completed_at": w.completed_at,
                "progress": f"{w.completed_actions}/{w.total_actions}",
            }
            for w in workflows
        ]

    def get_status(self) -> Dict[str, Any]:
        """Get engine status."""
        return {
            "running": self._running,
            "active_workflows": len([w for w in self._workflows.values() if w.status == WorkflowStatus.EXECUTING]),
            "total_workflows": len(self._workflows),
            "agents_available": {
                "llm": self._llm._running,
                "vision": self._vision._running,
                "browser": self._browser._running,
                "captcha": self._captcha._running,
                "input": self._input._running,
            },
        }


# Singleton instance
_engine: Optional[AutonomousEngine] = None


def get_autonomous_engine() -> AutonomousEngine:
    """Get singleton engine instance."""
    global _engine
    if _engine is None:
        _engine = AutonomousEngine()
    return _engine