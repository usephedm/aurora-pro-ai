"""
Real-Time Reasoning Display System for Aurora Pro

Shows what the AI is thinking in real-time, providing complete transparency.

Features:
- Live reasoning chain display
- Confidence scores for each decision
- Alternative approaches considered
- Decision rationale
- Data sources and influences
- Next planned steps
- WebSocket streaming
- Multiple output formats (terminal, web, logs)
"""
import asyncio
import json
import logging
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set

import aiofiles

logger = logging.getLogger(__name__)


class ReasoningLevel(Enum):
    """Level of reasoning detail."""
    DEBUG = "debug"  # Very detailed, internal thoughts
    INFO = "info"  # Normal reasoning steps
    WARNING = "warning"  # Concerns or uncertainties
    ERROR = "error"  # Errors or failures
    CRITICAL = "critical"  # Major decisions or risks


@dataclass
class ReasoningStep:
    """Single step in reasoning chain."""
    step_id: str
    timestamp: str
    level: ReasoningLevel
    component: str  # Which component is reasoning (LLM, Vision, Browser, etc)
    thought: str  # The actual thought/reasoning
    confidence: float  # 0.0 to 1.0
    alternatives_considered: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    decision_rationale: Optional[str] = None
    next_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningContext:
    """Context for a reasoning session."""
    context_id: str
    task_description: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "active"  # active, completed, failed
    total_steps: int = 0
    steps: List[ReasoningStep] = field(default_factory=list)


class ReasoningDisplay:
    """
    Real-Time Reasoning Display System.

    Captures and displays AI reasoning in real-time for full transparency.
    Supports multiple output formats and live streaming.
    """

    LOG_PATH = "/root/aurora_pro/logs/reasoning.log"
    CONTEXTS_PATH = "/root/aurora_pro/logs/reasoning_contexts"
    MAX_MEMORY_STEPS = 1000  # Keep last 1000 steps in memory

    def __init__(self):
        self._running = False
        self._contexts: Dict[str, ReasoningContext] = {}
        self._active_context: Optional[str] = None
        self._recent_steps: Deque[ReasoningStep] = deque(maxlen=self.MAX_MEMORY_STEPS)
        self._lock = asyncio.Lock()
        self._subscribers: Set[asyncio.Queue] = set()

        # Console output settings
        self._console_enabled = True
        self._console_min_level = ReasoningLevel.INFO

    async def start(self):
        """Initialize reasoning display."""
        self._running = True
        Path(self.CONTEXTS_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        logger.info("Reasoning Display initialized")

    async def stop(self):
        """Shutdown reasoning display."""
        self._running = False

        # Close all active contexts
        for context_id in list(self._contexts.keys()):
            await self.end_context(context_id)

    async def begin_context(
        self,
        task_description: str,
        context_id: Optional[str] = None,
    ) -> str:
        """
        Begin a new reasoning context.

        Args:
            task_description: Description of the task
            context_id: Optional custom context ID

        Returns:
            Context ID
        """
        if context_id is None:
            context_id = f"ctx_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        context = ReasoningContext(
            context_id=context_id,
            task_description=task_description,
            start_time=datetime.utcnow().isoformat(),
        )

        async with self._lock:
            self._contexts[context_id] = context
            self._active_context = context_id

        await self._log_to_file(
            f"===== BEGIN CONTEXT: {context_id} =====\n"
            f"Task: {task_description}\n"
            f"Start: {context.start_time}\n"
        )

        await self._broadcast({
            "type": "context_begin",
            "context_id": context_id,
            "task_description": task_description,
        })

        return context_id

    async def end_context(
        self,
        context_id: str,
        status: str = "completed",
    ):
        """
        End a reasoning context.

        Args:
            context_id: Context to end
            status: Final status (completed, failed, cancelled)
        """
        async with self._lock:
            if context_id not in self._contexts:
                return

            context = self._contexts[context_id]
            context.end_time = datetime.utcnow().isoformat()
            context.status = status

            if self._active_context == context_id:
                self._active_context = None

        await self._log_to_file(
            f"===== END CONTEXT: {context_id} =====\n"
            f"Status: {status}\n"
            f"End: {context.end_time}\n"
            f"Total Steps: {context.total_steps}\n\n"
        )

        await self._broadcast({
            "type": "context_end",
            "context_id": context_id,
            "status": status,
        })

        # Save context to disk
        await self._save_context(context)

    async def add_thought(
        self,
        thought: str,
        component: str,
        level: ReasoningLevel = ReasoningLevel.INFO,
        confidence: float = 1.0,
        alternatives: Optional[List[str]] = None,
        data_sources: Optional[List[str]] = None,
        rationale: Optional[str] = None,
        next_steps: Optional[List[str]] = None,
        context_id: Optional[str] = None,
        **metadata
    ) -> ReasoningStep:
        """
        Add a reasoning step/thought.

        Args:
            thought: The actual thought/reasoning
            component: Which component is reasoning
            level: Reasoning level (debug, info, warning, error, critical)
            confidence: Confidence in this reasoning (0.0 to 1.0)
            alternatives: Alternative approaches considered
            data_sources: What data influenced this thought
            rationale: Why this decision was made
            next_steps: What will happen next
            context_id: Context to add to (uses active if None)
            **metadata: Additional metadata

        Returns:
            Created ReasoningStep
        """
        if context_id is None:
            context_id = self._active_context

        step = ReasoningStep(
            step_id=f"step_{datetime.utcnow().strftime('%H%M%S_%f')}",
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            component=component,
            thought=thought,
            confidence=confidence,
            alternatives_considered=alternatives or [],
            data_sources=data_sources or [],
            decision_rationale=rationale,
            next_steps=next_steps or [],
            metadata=metadata,
        )

        async with self._lock:
            self._recent_steps.append(step)

            if context_id and context_id in self._contexts:
                context = self._contexts[context_id]
                context.steps.append(step)
                context.total_steps += 1

        # Output to console if enabled
        if self._console_enabled and level.value >= self._console_min_level.value:
            await self._print_to_console(step)

        # Log to file
        await self._log_step(step)

        # Broadcast to subscribers
        await self._broadcast({
            "type": "reasoning_step",
            "step": self._step_to_dict(step),
            "context_id": context_id,
        })

        return step

    async def add_decision(
        self,
        decision: str,
        component: str,
        confidence: float,
        alternatives: List[str],
        rationale: str,
        context_id: Optional[str] = None,
    ):
        """
        Add a major decision point.

        This is a convenience method for important decisions.
        """
        return await self.add_thought(
            thought=f"DECISION: {decision}",
            component=component,
            level=ReasoningLevel.CRITICAL if confidence < 0.7 else ReasoningLevel.INFO,
            confidence=confidence,
            alternatives=alternatives,
            rationale=rationale,
            context_id=context_id,
        )

    async def add_error(
        self,
        error: str,
        component: str,
        recovery_plan: Optional[List[str]] = None,
        context_id: Optional[str] = None,
    ):
        """Add an error with recovery plan."""
        return await self.add_thought(
            thought=f"ERROR: {error}",
            component=component,
            level=ReasoningLevel.ERROR,
            confidence=0.0,
            next_steps=recovery_plan or ["Attempting recovery..."],
            context_id=context_id,
        )

    async def _print_to_console(self, step: ReasoningStep):
        """Print reasoning step to console with formatting."""
        colors = {
            ReasoningLevel.DEBUG: "\033[90m",  # Gray
            ReasoningLevel.INFO: "\033[94m",  # Blue
            ReasoningLevel.WARNING: "\033[93m",  # Yellow
            ReasoningLevel.ERROR: "\033[91m",  # Red
            ReasoningLevel.CRITICAL: "\033[95m",  # Magenta
        }
        reset = "\033[0m"

        color = colors.get(step.level, "")
        confidence_bar = "█" * int(step.confidence * 10)

        output = f"{color}[{step.component}] {step.thought}{reset}"
        output += f"\n  Confidence: {confidence_bar} {step.confidence:.1%}"

        if step.alternatives_considered:
            output += f"\n  Alternatives: {', '.join(step.alternatives_considered)}"

        if step.decision_rationale:
            output += f"\n  Rationale: {step.decision_rationale}"

        if step.next_steps:
            output += f"\n  Next: {' → '.join(step.next_steps)}"

        print(output)
        sys.stdout.flush()

    async def _log_step(self, step: ReasoningStep):
        """Log reasoning step to file."""
        try:
            log_entry = (
                f"{step.timestamp} | {step.level.value.upper()} | {step.component} | "
                f"{step.thought}\n"
            )

            if step.confidence < 1.0:
                log_entry += f"  Confidence: {step.confidence:.1%}\n"

            if step.alternatives_considered:
                log_entry += f"  Alternatives: {', '.join(step.alternatives_considered)}\n"

            if step.decision_rationale:
                log_entry += f"  Rationale: {step.decision_rationale}\n"

            if step.next_steps:
                log_entry += f"  Next: {' → '.join(step.next_steps)}\n"

            await self._log_to_file(log_entry)

        except Exception as e:
            logger.error(f"Failed to log reasoning step: {e}")

    async def _log_to_file(self, content: str):
        """Write to log file."""
        try:
            async with aiofiles.open(self.LOG_PATH, "a") as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")

    async def _broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all subscribers."""
        dead_subscribers = set()

        for queue in self._subscribers:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # Subscriber is not keeping up, remove them
                dead_subscribers.add(queue)

        # Remove dead subscribers
        for queue in dead_subscribers:
            self._subscribers.discard(queue)

    async def subscribe(self) -> asyncio.Queue:
        """
        Subscribe to reasoning updates.

        Returns:
            Queue that will receive reasoning updates
        """
        queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from reasoning updates."""
        self._subscribers.discard(queue)

    def _step_to_dict(self, step: ReasoningStep) -> Dict[str, Any]:
        """Convert reasoning step to dictionary."""
        return {
            "step_id": step.step_id,
            "timestamp": step.timestamp,
            "level": step.level.value,
            "component": step.component,
            "thought": step.thought,
            "confidence": step.confidence,
            "alternatives_considered": step.alternatives_considered,
            "data_sources": step.data_sources,
            "decision_rationale": step.decision_rationale,
            "next_steps": step.next_steps,
            "metadata": step.metadata,
        }

    async def _save_context(self, context: ReasoningContext):
        """Save context to disk."""
        try:
            file_path = Path(self.CONTEXTS_PATH) / f"{context.context_id}.json"

            data = {
                "context_id": context.context_id,
                "task_description": context.task_description,
                "start_time": context.start_time,
                "end_time": context.end_time,
                "status": context.status,
                "total_steps": context.total_steps,
                "steps": [self._step_to_dict(step) for step in context.steps],
            }

            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(data, indent=2))

        except Exception as e:
            logger.error(f"Failed to save context: {e}")

    def get_context(self, context_id: str) -> Optional[ReasoningContext]:
        """Get reasoning context by ID."""
        return self._contexts.get(context_id)

    def get_recent_steps(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent reasoning steps."""
        steps = list(self._recent_steps)[-limit:]
        return [self._step_to_dict(step) for step in steps]

    def get_active_context(self) -> Optional[ReasoningContext]:
        """Get currently active context."""
        if self._active_context:
            return self._contexts.get(self._active_context)
        return None

    def list_contexts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent contexts."""
        contexts = sorted(
            self._contexts.values(),
            key=lambda c: c.start_time,
            reverse=True
        )[:limit]

        return [
            {
                "context_id": c.context_id,
                "task_description": c.task_description,
                "start_time": c.start_time,
                "end_time": c.end_time,
                "status": c.status,
                "total_steps": c.total_steps,
            }
            for c in contexts
        ]

    def get_status(self) -> Dict[str, Any]:
        """Get reasoning display status."""
        return {
            "running": self._running,
            "active_contexts": len([c for c in self._contexts.values() if c.status == "active"]),
            "total_contexts": len(self._contexts),
            "recent_steps": len(self._recent_steps),
            "subscribers": len(self._subscribers),
            "console_enabled": self._console_enabled,
        }

    def enable_console(self, min_level: ReasoningLevel = ReasoningLevel.INFO):
        """Enable console output."""
        self._console_enabled = True
        self._console_min_level = min_level

    def disable_console(self):
        """Disable console output."""
        self._console_enabled = False


# Singleton instance
_display: Optional[ReasoningDisplay] = None


def get_reasoning_display() -> ReasoningDisplay:
    """Get singleton display instance."""
    global _display
    if _display is None:
        _display = ReasoningDisplay()
    return _display