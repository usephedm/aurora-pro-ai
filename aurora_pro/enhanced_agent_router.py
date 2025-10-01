"""
Enhanced Agent Router with Confidence Scoring and Fallback Chains
Implements intelligent routing with multi-factor decision making
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json


class AgentType(Enum):
    CLAUDE = "claude"
    CODEX = "codex"
    BROWSER = "browser"
    VISION = "vision"
    INPUT = "input"
    LOCAL_LLM = "local_llm"


class TaskCategory(Enum):
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    WEB_AUTOMATION = "web_automation"
    SCREEN_ANALYSIS = "screen_analysis"
    SYSTEM_CONTROL = "system_control"
    RESEARCH = "research"
    DATA_EXTRACTION = "data_extraction"
    GENERAL = "general"


@dataclass
class AgentCapability:
    agent_type: AgentType
    categories: List[TaskCategory]
    confidence_multiplier: float = 1.0
    average_latency_ms: float = 1000.0
    success_rate: float = 1.0
    cost_per_task: float = 0.0
    availability: bool = True


@dataclass
class RoutingDecision:
    primary_agent: AgentType
    fallback_chain: List[AgentType]
    confidence_score: float
    reasoning: str
    estimated_latency_ms: float
    estimated_cost: float


@dataclass
class PerformanceMetrics:
    agent_type: AgentType
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_latency_ms: float = 0.0
    average_latency_ms: float = 0.0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    error_count_5min: int = 0

    def update_success(self, latency_ms: float):
        self.total_tasks += 1
        self.successful_tasks += 1
        self.total_latency_ms += latency_ms
        self.average_latency_ms = self.total_latency_ms / self.total_tasks
        self.last_success_time = datetime.utcnow()

    def update_failure(self):
        self.total_tasks += 1
        self.failed_tasks += 1
        self.last_failure_time = datetime.utcnow()
        self.error_count_5min += 1

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 1.0
        return self.successful_tasks / self.total_tasks

    @property
    def is_healthy(self) -> bool:
        # Agent is unhealthy if error rate is high or recent failures
        if self.error_count_5min > 5:
            return False
        if self.success_rate < 0.5:
            return False
        return True


class EnhancedAgentRouter:
    """
    Production-grade agent router with:
    - Confidence scoring based on prompt analysis
    - Multi-agent fallback chains
    - Performance tracking and adaptive routing
    - Cost optimization
    - Health monitoring
    """

    def __init__(self):
        self.logger = logging.getLogger("aurora.enhanced_router")

        # Agent capability registry
        self.capabilities: Dict[AgentType, AgentCapability] = self._init_capabilities()

        # Performance tracking
        self.metrics: Dict[AgentType, PerformanceMetrics] = {
            agent_type: PerformanceMetrics(agent_type=agent_type)
            for agent_type in AgentType
        }

        # Keyword-to-category mapping
        self.keyword_map = self._init_keyword_map()

        # Configuration
        self.confidence_threshold = 0.7
        self.prefer_fast_agents = False
        self.prefer_cheap_agents = False

    def _init_capabilities(self) -> Dict[AgentType, AgentCapability]:
        return {
            AgentType.CLAUDE: AgentCapability(
                agent_type=AgentType.CLAUDE,
                categories=[
                    TaskCategory.CODE_GENERATION,
                    TaskCategory.CODE_REVIEW,
                    TaskCategory.RESEARCH,
                    TaskCategory.GENERAL
                ],
                confidence_multiplier=1.0,
                average_latency_ms=2000.0,
                cost_per_task=0.01
            ),
            AgentType.CODEX: AgentCapability(
                agent_type=AgentType.CODEX,
                categories=[
                    TaskCategory.CODE_GENERATION,
                    TaskCategory.SYSTEM_CONTROL,
                    TaskCategory.GENERAL
                ],
                confidence_multiplier=0.9,
                average_latency_ms=1500.0,
                cost_per_task=0.008
            ),
            AgentType.BROWSER: AgentCapability(
                agent_type=AgentType.BROWSER,
                categories=[
                    TaskCategory.WEB_AUTOMATION,
                    TaskCategory.DATA_EXTRACTION,
                    TaskCategory.RESEARCH
                ],
                confidence_multiplier=1.0,
                average_latency_ms=5000.0,
                cost_per_task=0.0
            ),
            AgentType.VISION: AgentCapability(
                agent_type=AgentType.VISION,
                categories=[
                    TaskCategory.SCREEN_ANALYSIS,
                    TaskCategory.DATA_EXTRACTION
                ],
                confidence_multiplier=1.0,
                average_latency_ms=3000.0,
                cost_per_task=0.0
            ),
            AgentType.INPUT: AgentCapability(
                agent_type=AgentType.INPUT,
                categories=[
                    TaskCategory.SYSTEM_CONTROL,
                    TaskCategory.WEB_AUTOMATION
                ],
                confidence_multiplier=1.0,
                average_latency_ms=500.0,
                cost_per_task=0.0
            ),
            AgentType.LOCAL_LLM: AgentCapability(
                agent_type=AgentType.LOCAL_LLM,
                categories=[
                    TaskCategory.GENERAL,
                    TaskCategory.CODE_GENERATION
                ],
                confidence_multiplier=0.7,
                average_latency_ms=4000.0,
                cost_per_task=0.0,
                availability=False  # Disabled until Ollama configured
            )
        }

    def _init_keyword_map(self) -> Dict[str, List[TaskCategory]]:
        return {
            # Code-related
            "code": [TaskCategory.CODE_GENERATION],
            "function": [TaskCategory.CODE_GENERATION],
            "class": [TaskCategory.CODE_GENERATION],
            "implement": [TaskCategory.CODE_GENERATION],
            "refactor": [TaskCategory.CODE_REVIEW],
            "review": [TaskCategory.CODE_REVIEW],
            "debug": [TaskCategory.CODE_REVIEW],
            "fix": [TaskCategory.CODE_REVIEW],

            # Web automation
            "browser": [TaskCategory.WEB_AUTOMATION],
            "navigate": [TaskCategory.WEB_AUTOMATION],
            "click": [TaskCategory.WEB_AUTOMATION, TaskCategory.SYSTEM_CONTROL],
            "scrape": [TaskCategory.DATA_EXTRACTION],
            "extract": [TaskCategory.DATA_EXTRACTION],
            "search": [TaskCategory.RESEARCH, TaskCategory.WEB_AUTOMATION],

            # Vision
            "screen": [TaskCategory.SCREEN_ANALYSIS],
            "image": [TaskCategory.SCREEN_ANALYSIS],
            "detect": [TaskCategory.SCREEN_ANALYSIS],
            "ocr": [TaskCategory.SCREEN_ANALYSIS],
            "read": [TaskCategory.SCREEN_ANALYSIS, TaskCategory.DATA_EXTRACTION],

            # System control
            "type": [TaskCategory.SYSTEM_CONTROL],
            "move": [TaskCategory.SYSTEM_CONTROL],
            "keyboard": [TaskCategory.SYSTEM_CONTROL],
            "mouse": [TaskCategory.SYSTEM_CONTROL],
            "command": [TaskCategory.SYSTEM_CONTROL],
            "execute": [TaskCategory.SYSTEM_CONTROL],

            # Research
            "research": [TaskCategory.RESEARCH],
            "analyze": [TaskCategory.RESEARCH, TaskCategory.CODE_REVIEW],
            "investigate": [TaskCategory.RESEARCH],
            "find": [TaskCategory.RESEARCH],
        }

    async def route(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        prefer_fast: bool = False,
        prefer_cheap: bool = False
    ) -> RoutingDecision:
        """
        Route a task to the optimal agent with fallback chain

        Args:
            prompt: Task description
            context: Additional context (conversation history, etc.)
            prefer_fast: Optimize for speed
            prefer_cheap: Optimize for cost

        Returns:
            RoutingDecision with primary agent and fallbacks
        """
        start_time = time.time()

        # Analyze prompt to determine task categories
        categories = self._analyze_prompt(prompt)

        # Score all available agents
        agent_scores = await self._score_agents(
            prompt, categories, context, prefer_fast, prefer_cheap
        )

        # Sort by confidence score
        sorted_agents = sorted(
            agent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Select primary and fallback chain
        primary_agent = sorted_agents[0][0]
        primary_confidence = sorted_agents[0][1]
        fallback_chain = [agent for agent, _ in sorted_agents[1:4]]  # Top 3 fallbacks

        # Calculate estimated metrics
        primary_capability = self.capabilities[primary_agent]
        estimated_latency = primary_capability.average_latency_ms
        estimated_cost = primary_capability.cost_per_task

        reasoning = self._generate_reasoning(
            primary_agent, categories, primary_confidence, agent_scores
        )

        decision = RoutingDecision(
            primary_agent=primary_agent,
            fallback_chain=fallback_chain,
            confidence_score=primary_confidence,
            reasoning=reasoning,
            estimated_latency_ms=estimated_latency,
            estimated_cost=estimated_cost
        )

        routing_time_ms = (time.time() - start_time) * 1000
        self.logger.info(
            f"Routed to {primary_agent.value} (confidence: {primary_confidence:.2f}, "
            f"routing_time: {routing_time_ms:.1f}ms): {reasoning}"
        )

        return decision

    def _analyze_prompt(self, prompt: str) -> List[TaskCategory]:
        """Analyze prompt to determine relevant task categories"""
        prompt_lower = prompt.lower()
        categories_found = set()

        for keyword, categories in self.keyword_map.items():
            if keyword in prompt_lower:
                categories_found.update(categories)

        # Default to GENERAL if no specific categories found
        if not categories_found:
            categories_found.add(TaskCategory.GENERAL)

        return list(categories_found)

    async def _score_agents(
        self,
        prompt: str,
        categories: List[TaskCategory],
        context: Optional[Dict[str, Any]],
        prefer_fast: bool,
        prefer_cheap: bool
    ) -> Dict[AgentType, float]:
        """Score all agents for this task"""
        scores = {}

        for agent_type, capability in self.capabilities.items():
            # Skip unavailable agents
            if not capability.availability:
                continue

            # Base score: category match
            category_match = sum(
                1 for cat in categories if cat in capability.categories
            )
            base_score = category_match / max(len(categories), 1)

            # Confidence multiplier from capability
            base_score *= capability.confidence_multiplier

            # Performance-based adjustments
            metrics = self.metrics[agent_type]

            # Success rate adjustment
            base_score *= metrics.success_rate

            # Health check - penalize unhealthy agents
            if not metrics.is_healthy:
                base_score *= 0.5

            # Speed optimization
            if prefer_fast:
                # Favor faster agents
                speed_factor = 1.0 / (capability.average_latency_ms / 1000.0)
                base_score *= (1.0 + speed_factor * 0.2)

            # Cost optimization
            if prefer_cheap:
                # Favor cheaper agents
                if capability.cost_per_task == 0:
                    base_score *= 1.5
                else:
                    cost_factor = 1.0 / capability.cost_per_task
                    base_score *= (1.0 + cost_factor * 0.1)

            scores[agent_type] = min(base_score, 1.0)  # Cap at 1.0

        return scores

    def _generate_reasoning(
        self,
        primary_agent: AgentType,
        categories: List[TaskCategory],
        confidence: float,
        all_scores: Dict[AgentType, float]
    ) -> str:
        """Generate human-readable reasoning for routing decision"""
        category_names = [cat.value for cat in categories]

        reasoning_parts = [
            f"Task categories: {', '.join(category_names)}",
            f"Best match: {primary_agent.value}",
            f"Confidence: {confidence:.2%}"
        ]

        # Add performance info if relevant
        metrics = self.metrics[primary_agent]
        if metrics.total_tasks > 0:
            reasoning_parts.append(
                f"Success rate: {metrics.success_rate:.2%}"
            )

        return "; ".join(reasoning_parts)

    async def record_result(
        self,
        agent_type: AgentType,
        success: bool,
        latency_ms: float,
        error: Optional[str] = None
    ):
        """Record task result for adaptive learning"""
        metrics = self.metrics[agent_type]

        if success:
            metrics.update_success(latency_ms)
            self.logger.debug(
                f"{agent_type.value} task completed successfully "
                f"({latency_ms:.0f}ms)"
            )
        else:
            metrics.update_failure()
            self.logger.warning(
                f"{agent_type.value} task failed: {error}"
            )

        # Update capability average latency with rolling average
        capability = self.capabilities[agent_type]
        if success:
            alpha = 0.2  # Smoothing factor
            capability.average_latency_ms = (
                alpha * latency_ms + (1 - alpha) * capability.average_latency_ms
            )

    async def get_fallback_agent(
        self,
        failed_agent: AgentType,
        original_decision: RoutingDecision
    ) -> Optional[AgentType]:
        """Get next fallback agent after a failure"""
        fallback_chain = original_decision.fallback_chain

        for fallback in fallback_chain:
            if fallback == failed_agent:
                continue

            # Check if fallback is available and healthy
            if not self.capabilities[fallback].availability:
                continue

            if not self.metrics[fallback].is_healthy:
                continue

            self.logger.info(
                f"Falling back from {failed_agent.value} to {fallback.value}"
            )
            return fallback

        self.logger.error(
            f"No healthy fallback available for {failed_agent.value}"
        )
        return None

    def get_status(self) -> Dict[str, Any]:
        """Get router status for monitoring"""
        return {
            "confidence_threshold": self.confidence_threshold,
            "agents": {
                agent_type.value: {
                    "available": cap.availability,
                    "categories": [cat.value for cat in cap.categories],
                    "avg_latency_ms": cap.average_latency_ms,
                    "cost_per_task": cap.cost_per_task,
                    "total_tasks": self.metrics[agent_type].total_tasks,
                    "success_rate": self.metrics[agent_type].success_rate,
                    "is_healthy": self.metrics[agent_type].is_healthy
                }
                for agent_type, cap in self.capabilities.items()
            }
        }

    def enable_agent(self, agent_type: AgentType):
        """Enable an agent at runtime"""
        self.capabilities[agent_type].availability = True
        self.logger.info(f"Enabled agent: {agent_type.value}")

    def disable_agent(self, agent_type: AgentType):
        """Disable an agent at runtime"""
        self.capabilities[agent_type].availability = False
        self.logger.info(f"Disabled agent: {agent_type.value}")


# Singleton instance
_router_instance: Optional[EnhancedAgentRouter] = None


def get_enhanced_router() -> EnhancedAgentRouter:
    """Get or create singleton router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = EnhancedAgentRouter()
    return _router_instance
