"""Agent router coordinating conversational prompts and tool dispatch."""
from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ConversationMessage:
    role: str
    content: str
    timestamp: float = dataclasses.field(default_factory=time.time)
    metadata: Dict[str, str] = dataclasses.field(default_factory=dict)

    def serialize(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class ConversationState:
    """Maintains rolling conversation history for agent orchestration."""

    def __init__(self, max_messages: int = 200) -> None:
        self.max_messages = max_messages
        self.messages: Deque[ConversationMessage] = deque(maxlen=max_messages)
        self.last_summary: Optional[str] = None

    def add_message(self, message: ConversationMessage) -> None:
        self.messages.append(message)

    def history(self) -> List[dict]:
        return [message.serialize() for message in self.messages]

    def summarize(self) -> str:
        if not self.messages:
            return ""
        summary = {
            "count": len(self.messages),
            "latest": self.messages[-1].content,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.last_summary = json.dumps(summary)
        return self.last_summary


class AgentRouter:
    """High-level orchestrator providing conversational interface over Aurora tools."""

    def __init__(self, coordinator) -> None:
        self.coordinator = coordinator
        self.state = ConversationState()
        self._lock = asyncio.Lock()

    async def handle_message(
        self,
        prompt: str,
        *,
        channel: str = "user",
        agent_preference: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, object]:
        metadata = metadata or {}
        async with self._lock:
            self.state.add_message(
                ConversationMessage(role=channel, content=prompt, metadata=metadata)
            )

            # Simple heuristic: if prompt requests browser/system use coordinator command path
            lower_prompt = prompt.lower()
            if lower_prompt.startswith("run ") or "open " in lower_prompt or "navigate" in lower_prompt:
                response = await self.coordinator.process_command(prompt)
                self.state.add_message(ConversationMessage(role="system", content=response))
                return {
                    "route": "system",
                    "response": response,
                    "history": self.state.history(),
                }

            # Otherwise route via CLI task
            cli_result = await self.coordinator.submit_cli_task(
                prompt,
                agent=agent_preference,
                metadata=metadata,
            )
            task_info = cli_result.get("task", {})
            message = f"Dispatched task {task_info.get('id')} to agent {cli_result.get('agent')}"
            self.state.add_message(ConversationMessage(role="system", content=message))
            return {
                "route": "cli",
                "response": message,
                "task": task_info,
                "history": self.state.history(),
            }

    def snapshot(self) -> Dict[str, object]:
        return {
            "history": self.state.history(),
            "summary": self.state.last_summary or self.state.summarize(),
        }


__all__ = ["AgentRouter", "ConversationMessage", "ConversationState"]
