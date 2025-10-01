"""
Multi-LLM Orchestration Engine for Aurora Pro

Intelligently routes tasks to the best LLM based on task type, cost, speed, and quality.
Supports Claude (Sonnet/Opus), GPT-4, Gemini Pro, and local Ollama models.

Features:
- Automatic LLM selection based on task analysis
- Cost tracking per LLM
- Speed benchmarking
- Quality scoring
- Fallback chains
- Parallel queries with voting
- Token usage monitoring
- Rate limiting and error recovery
"""
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
import httpx

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    CLAUDE_SONNET = "claude-sonnet-4-5"
    CLAUDE_OPUS = "claude-opus-4"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4 = "gpt-4"
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"
    OLLAMA_QWEN = "ollama-qwen2.5"
    OLLAMA_LLAMA = "ollama-llama3.2"
    OLLAMA_CODELLAMA = "ollama-codellama"
    CODEX = "codex"


class TaskType(Enum):
    """Types of tasks for intelligent routing."""
    REASONING = "reasoning"  # Complex logical reasoning
    CODE_GENERATION = "code_generation"  # Writing code
    CODE_REVIEW = "code_review"  # Reviewing code
    ANALYSIS = "analysis"  # Data/content analysis
    CONVERSATION = "conversation"  # Natural conversation
    SUMMARIZATION = "summarization"  # Summarizing content
    TRANSLATION = "translation"  # Language translation
    CLI_COMMAND = "cli_command"  # CLI/terminal commands
    WEB_SCRAPING = "web_scraping"  # Web extraction
    CREATIVE_WRITING = "creative_writing"  # Creative content
    MATH = "math"  # Mathematical problems
    LONG_CONTEXT = "long_context"  # Long document processing


@dataclass
class LLMResponse:
    """Response from an LLM."""
    provider: LLMProvider
    response: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    cost_usd: float
    timestamp: str
    model_version: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMStats:
    """Statistics for an LLM provider."""
    provider: LLMProvider
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    success_count: int = 0
    error_count: int = 0
    average_latency_ms: float = 0.0
    average_cost_per_request: float = 0.0
    quality_score: float = 0.0  # User feedback based
    last_used: Optional[str] = None


class LLMOrchestrator:
    """
    Intelligent Multi-LLM Orchestration Engine.

    Routes tasks to optimal LLM based on:
    - Task type and complexity
    - Cost constraints
    - Speed requirements
    - Quality requirements
    - Availability and rate limits
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/llm_orchestrator.log"
    STATS_PATH = "/root/aurora_pro/logs/llm_stats.json"

    # Cost per 1K tokens (estimated, adjust as needed)
    COSTS = {
        LLMProvider.CLAUDE_SONNET: {"input": 0.003, "output": 0.015},
        LLMProvider.CLAUDE_OPUS: {"input": 0.015, "output": 0.075},
        LLMProvider.GPT4_TURBO: {"input": 0.01, "output": 0.03},
        LLMProvider.GPT4: {"input": 0.03, "output": 0.06},
        LLMProvider.GEMINI_PRO: {"input": 0.0005, "output": 0.0015},
        LLMProvider.GEMINI_FLASH: {"input": 0.0001, "output": 0.0004},
        LLMProvider.OLLAMA_QWEN: {"input": 0.0, "output": 0.0},
        LLMProvider.OLLAMA_LLAMA: {"input": 0.0, "output": 0.0},
        LLMProvider.OLLAMA_CODELLAMA: {"input": 0.0, "output": 0.0},
        LLMProvider.CODEX: {"input": 0.0, "output": 0.0},
    }

    # Task type to LLM preference mapping
    TASK_PREFERENCES = {
        TaskType.REASONING: [
            LLMProvider.CLAUDE_OPUS,
            LLMProvider.CLAUDE_SONNET,
            LLMProvider.GPT4,
        ],
        TaskType.CODE_GENERATION: [
            LLMProvider.GPT4_TURBO,
            LLMProvider.CLAUDE_SONNET,
            LLMProvider.OLLAMA_CODELLAMA,
        ],
        TaskType.CODE_REVIEW: [
            LLMProvider.CLAUDE_SONNET,
            LLMProvider.GPT4_TURBO,
        ],
        TaskType.ANALYSIS: [
            LLMProvider.CLAUDE_SONNET,
            LLMProvider.GPT4_TURBO,
            LLMProvider.GEMINI_PRO,
        ],
        TaskType.CONVERSATION: [
            LLMProvider.CLAUDE_SONNET,
            LLMProvider.GPT4_TURBO,
            LLMProvider.OLLAMA_LLAMA,
        ],
        TaskType.SUMMARIZATION: [
            LLMProvider.GEMINI_FLASH,
            LLMProvider.CLAUDE_SONNET,
        ],
        TaskType.CLI_COMMAND: [
            LLMProvider.CODEX,
            LLMProvider.GPT4_TURBO,
            LLMProvider.OLLAMA_CODELLAMA,
        ],
        TaskType.LONG_CONTEXT: [
            LLMProvider.GEMINI_PRO,
            LLMProvider.CLAUDE_OPUS,
        ],
        TaskType.MATH: [
            LLMProvider.GPT4,
            LLMProvider.CLAUDE_OPUS,
        ],
    }

    def __init__(self):
        self._running = False
        self._stats: Dict[LLMProvider, LLMStats] = {}
        self._lock = asyncio.Lock()

        # API keys from environment
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._google_key = os.getenv("GOOGLE_API_KEY")

        # Initialize stats for all providers
        for provider in LLMProvider:
            self._stats[provider] = LLMStats(provider=provider)

    async def start(self):
        """Initialize orchestrator."""
        self._running = True
        await self._load_stats()
        await self._audit_log("system", "LLM Orchestrator started")
        logger.info("LLM Orchestrator initialized")

    async def stop(self):
        """Shutdown orchestrator."""
        self._running = False
        await self._save_stats()
        await self._audit_log("system", "LLM Orchestrator stopped")

    async def generate(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None,
        preferred_provider: Optional[LLMProvider] = None,
        max_cost_usd: Optional[float] = None,
        max_latency_ms: Optional[float] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate response using optimal LLM.

        Args:
            prompt: The prompt to send
            task_type: Type of task for intelligent routing
            preferred_provider: Force specific provider
            max_cost_usd: Maximum acceptable cost
            max_latency_ms: Maximum acceptable latency
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with the result
        """
        # Select LLM
        if preferred_provider:
            provider = preferred_provider
        elif task_type:
            provider = await self._select_llm_for_task(
                task_type, max_cost_usd, max_latency_ms
            )
        else:
            # Default to Claude Sonnet
            provider = LLMProvider.CLAUDE_SONNET

        # Generate response
        start_time = time.time()
        try:
            response = await self._call_llm(
                provider,
                prompt,
                system_prompt,
                temperature,
                max_tokens,
            )
            latency_ms = (time.time() - start_time) * 1000

            # Update stats
            async with self._lock:
                stats = self._stats[provider]
                stats.total_requests += 1
                stats.success_count += 1
                stats.total_tokens += response.tokens_input + response.tokens_output
                stats.total_cost_usd += response.cost_usd
                stats.total_latency_ms += latency_ms
                stats.average_latency_ms = stats.total_latency_ms / stats.total_requests
                stats.average_cost_per_request = stats.total_cost_usd / stats.total_requests
                stats.last_used = datetime.utcnow().isoformat()

            await self._audit_log(
                "generate",
                f"Provider: {provider.value}, tokens: {response.tokens_input + response.tokens_output}, "
                f"cost: ${response.cost_usd:.4f}, latency: {latency_ms:.0f}ms"
            )

            return response

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            async with self._lock:
                stats = self._stats[provider]
                stats.total_requests += 1
                stats.error_count += 1

            await self._audit_log("error", f"Provider: {provider.value}, error: {str(e)}")

            # Try fallback
            return await self._try_fallback(
                provider, prompt, system_prompt, temperature, max_tokens, str(e)
            )

    async def generate_with_voting(
        self,
        prompt: str,
        providers: List[LLMProvider],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Query multiple LLMs in parallel and aggregate results.

        Useful for high-stakes decisions where you want consensus.
        """
        tasks = [
            self._call_llm(provider, prompt, system_prompt, temperature, None)
            for provider in providers
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        valid_responses = []
        for resp in responses:
            if isinstance(resp, LLMResponse) and not resp.error:
                valid_responses.append(resp)

        await self._audit_log(
            "voting",
            f"Queried {len(providers)} providers, got {len(valid_responses)} valid responses"
        )

        return {
            "responses": valid_responses,
            "providers_queried": len(providers),
            "successful_responses": len(valid_responses),
            "consensus": self._calculate_consensus(valid_responses),
        }

    async def _select_llm_for_task(
        self,
        task_type: TaskType,
        max_cost_usd: Optional[float],
        max_latency_ms: Optional[float],
    ) -> LLMProvider:
        """Select optimal LLM based on task requirements."""
        preferences = self.TASK_PREFERENCES.get(
            task_type,
            [LLMProvider.CLAUDE_SONNET]
        )

        async with self._lock:
            for provider in preferences:
                stats = self._stats[provider]

                # Check cost constraint
                if max_cost_usd and stats.average_cost_per_request > max_cost_usd:
                    continue

                # Check latency constraint
                if max_latency_ms and stats.average_latency_ms > max_latency_ms:
                    continue

                # Check availability (not too many errors recently)
                if stats.total_requests > 10:
                    error_rate = stats.error_count / stats.total_requests
                    if error_rate > 0.5:  # More than 50% errors
                        continue

                return provider

        # Fallback to cheapest option
        return LLMProvider.OLLAMA_LLAMA

    async def _call_llm(
        self,
        provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """Call specific LLM provider."""
        if provider.value.startswith("claude"):
            return await self._call_claude(provider, prompt, system_prompt, temperature, max_tokens)
        elif provider.value.startswith("gpt"):
            return await self._call_openai(provider, prompt, system_prompt, temperature, max_tokens)
        elif provider.value.startswith("gemini"):
            return await self._call_gemini(provider, prompt, system_prompt, temperature, max_tokens)
        elif provider.value.startswith("ollama"):
            return await self._call_ollama(provider, prompt, system_prompt, temperature, max_tokens)
        elif provider == LLMProvider.CODEX:
            return await self._call_codex(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _call_claude(
        self,
        provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """Call Claude API."""
        if not self._anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self._anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        data = {
            "model": provider.value,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            data["system"] = system_prompt

        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

        latency_ms = (time.time() - start_time) * 1000

        tokens_input = result["usage"]["input_tokens"]
        tokens_output = result["usage"]["output_tokens"]
        cost = self._calculate_cost(provider, tokens_input, tokens_output)

        return LLMResponse(
            provider=provider,
            response=result["content"][0]["text"],
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            cost_usd=cost,
            timestamp=datetime.utcnow().isoformat(),
            model_version=result["model"],
        )

    async def _call_openai(
        self,
        provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """Call OpenAI API."""
        if not self._openai_key:
            raise ValueError("OPENAI_API_KEY not set")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openai_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": provider.value,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            data["max_tokens"] = max_tokens

        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

        latency_ms = (time.time() - start_time) * 1000

        tokens_input = result["usage"]["prompt_tokens"]
        tokens_output = result["usage"]["completion_tokens"]
        cost = self._calculate_cost(provider, tokens_input, tokens_output)

        return LLMResponse(
            provider=provider,
            response=result["choices"][0]["message"]["content"],
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            cost_usd=cost,
            timestamp=datetime.utcnow().isoformat(),
            model_version=result["model"],
        )

    async def _call_gemini(
        self,
        provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """Call Google Gemini API."""
        if not self._google_key:
            raise ValueError("GOOGLE_API_KEY not set")

        model_name = "gemini-1.5-pro" if provider == LLMProvider.GEMINI_PRO else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self._google_key}"

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            data["generationConfig"]["maxOutputTokens"] = max_tokens

        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

        latency_ms = (time.time() - start_time) * 1000

        # Estimate tokens (Gemini doesn't always return token counts)
        tokens_input = len(full_prompt.split()) * 1.3  # Rough estimate
        response_text = result["candidates"][0]["content"]["parts"][0]["text"]
        tokens_output = len(response_text.split()) * 1.3

        cost = self._calculate_cost(provider, int(tokens_input), int(tokens_output))

        return LLMResponse(
            provider=provider,
            response=response_text,
            tokens_input=int(tokens_input),
            tokens_output=int(tokens_output),
            latency_ms=latency_ms,
            cost_usd=cost,
            timestamp=datetime.utcnow().isoformat(),
            model_version=model_name,
        )

    async def _call_ollama(
        self,
        provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """Call local Ollama API."""
        model_name = provider.value.replace("ollama-", "")
        url = "http://localhost:11434/api/generate"

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        data = {
            "model": model_name,
            "prompt": full_prompt,
            "temperature": temperature,
            "stream": False,
        }

        start_time = time.time()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

        latency_ms = (time.time() - start_time) * 1000

        # Ollama provides token counts
        tokens_input = result.get("prompt_eval_count", 0)
        tokens_output = result.get("eval_count", 0)

        return LLMResponse(
            provider=provider,
            response=result["response"],
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            cost_usd=0.0,  # Local is free
            timestamp=datetime.utcnow().isoformat(),
            model_version=model_name,
        )

    async def _call_codex(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """Call Codex (treated as local for now)."""
        # For now, treat Codex as OpenAI GPT-4 with code optimization
        return await self._call_openai(
            LLMProvider.GPT4_TURBO,
            prompt,
            system_prompt or "You are an expert programmer and CLI assistant.",
            temperature,
            max_tokens,
        )

    def _calculate_cost(
        self, provider: LLMProvider, tokens_input: int, tokens_output: int
    ) -> float:
        """Calculate cost for LLM call."""
        costs = self.COSTS.get(provider, {"input": 0, "output": 0})
        cost_input = (tokens_input / 1000) * costs["input"]
        cost_output = (tokens_output / 1000) * costs["output"]
        return cost_input + cost_output

    def _calculate_consensus(self, responses: List[LLMResponse]) -> Optional[str]:
        """Calculate consensus from multiple responses."""
        if not responses:
            return None

        # Simple majority voting on similar responses
        # For now, just return the most common response
        from collections import Counter
        response_texts = [r.response[:100] for r in responses]  # Compare first 100 chars
        most_common = Counter(response_texts).most_common(1)

        if most_common:
            # Find full response
            prefix = most_common[0][0]
            for resp in responses:
                if resp.response.startswith(prefix):
                    return resp.response

        return responses[0].response

    async def _try_fallback(
        self,
        failed_provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        error_msg: str,
    ) -> LLMResponse:
        """Try fallback LLMs if primary fails."""
        fallback_order = [
            LLMProvider.CLAUDE_SONNET,
            LLMProvider.GPT4_TURBO,
            LLMProvider.OLLAMA_LLAMA,
        ]

        for provider in fallback_order:
            if provider == failed_provider:
                continue

            try:
                response = await self._call_llm(
                    provider, prompt, system_prompt, temperature, max_tokens
                )
                response.metadata["fallback_from"] = failed_provider.value
                response.metadata["original_error"] = error_msg
                return response
            except Exception as e:
                logger.warning(f"Fallback to {provider.value} also failed: {e}")
                continue

        # All failed, return error response
        return LLMResponse(
            provider=failed_provider,
            response="",
            tokens_input=0,
            tokens_output=0,
            latency_ms=0,
            cost_usd=0,
            timestamp=datetime.utcnow().isoformat(),
            model_version="unknown",
            error=f"All LLMs failed. Last error: {error_msg}",
        )

    async def _load_stats(self):
        """Load statistics from disk."""
        try:
            if Path(self.STATS_PATH).exists():
                async with aiofiles.open(self.STATS_PATH, "r") as f:
                    content = await f.read()
                    data = json.loads(content)

                    for provider_str, stats_dict in data.items():
                        try:
                            provider = LLMProvider(provider_str)
                            self._stats[provider] = LLMStats(
                                provider=provider,
                                **{k: v for k, v in stats_dict.items() if k != "provider"}
                            )
                        except ValueError:
                            continue
        except Exception as e:
            logger.warning(f"Failed to load LLM stats: {e}")

    async def _save_stats(self):
        """Save statistics to disk."""
        try:
            data = {
                stats.provider.value: {
                    "total_requests": stats.total_requests,
                    "total_tokens": stats.total_tokens,
                    "total_cost_usd": stats.total_cost_usd,
                    "total_latency_ms": stats.total_latency_ms,
                    "success_count": stats.success_count,
                    "error_count": stats.error_count,
                    "average_latency_ms": stats.average_latency_ms,
                    "average_cost_per_request": stats.average_cost_per_request,
                    "quality_score": stats.quality_score,
                    "last_used": stats.last_used,
                }
                for stats in self._stats.values()
            }

            async with aiofiles.open(self.STATS_PATH, "w") as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save LLM stats: {e}")

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

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return {
            "providers": {
                stats.provider.value: {
                    "total_requests": stats.total_requests,
                    "success_count": stats.success_count,
                    "error_count": stats.error_count,
                    "success_rate_percent": (
                        (stats.success_count / stats.total_requests * 100)
                        if stats.total_requests > 0 else 0.0
                    ),
                    "total_tokens": stats.total_tokens,
                    "total_cost_usd": stats.total_cost_usd,
                    "average_latency_ms": stats.average_latency_ms,
                    "average_cost_per_request": stats.average_cost_per_request,
                    "quality_score": stats.quality_score,
                    "last_used": stats.last_used,
                }
                for stats in self._stats.values()
            },
            "total_cost_all_providers": sum(s.total_cost_usd for s in self._stats.values()),
            "total_requests_all_providers": sum(s.total_requests for s in self._stats.values()),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "running": self._running,
            "providers_configured": {
                "anthropic": self._anthropic_key is not None,
                "openai": self._openai_key is not None,
                "google": self._google_key is not None,
                "ollama": True,  # Local, always available
            },
            "total_providers": len(LLMProvider),
        }


# Singleton instance
_orchestrator: Optional[LLMOrchestrator] = None


def get_llm_orchestrator() -> LLMOrchestrator:
    """Get singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LLMOrchestrator()
    return _orchestrator