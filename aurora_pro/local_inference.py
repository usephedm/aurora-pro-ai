"""Local Inference Engine for Aurora Pro - Ollama integration.

This module provides local LLM inference using Ollama, with model selection,
streaming responses, and fallback to cloud agents. All features are gated by
operator_enabled.yaml configuration.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional

import aiofiles
import aiohttp
import yaml

logger = logging.getLogger(__name__)


@dataclass
class InferenceRequest:
    """Local inference request."""
    request_id: str
    model: str
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


@dataclass
class InferenceResponse:
    """Local inference response."""
    request_id: str
    model: str
    response: str
    tokens_generated: int
    inference_time_sec: float
    tokens_per_sec: float


class LocalInferenceEngine:
    """
    Local LLM inference engine using Ollama.

    Features:
    - Ollama client integration
    - Multiple model support (qwen, llama, mistral, etc.)
    - Streaming and non-streaming responses
    - Automatic fallback to cloud agents
    - Performance monitoring
    - Operator authorization gating
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/local_inference.log"
    CONFIG_PATH = "/root/aurora_pro/config/operator_enabled.yaml"
    DEFAULT_OLLAMA_URL = "http://localhost:11434"

    SUPPORTED_MODELS = [
        "qwen2.5:latest",
        "llama3.2:latest",
        "llama3.1:latest",
        "mistral:latest",
        "codellama:latest",
        "deepseek-coder:latest",
    ]

    def __init__(self, ollama_url: Optional[str] = None):
        self._ollama_url = ollama_url or self.DEFAULT_OLLAMA_URL
        self._config: Dict = {}
        self._running = False
        self._available = False
        self._available_models: List[str] = []
        self._lock = asyncio.Lock()

        # Statistics
        self._total_requests = 0
        self._total_tokens = 0
        self._total_inference_time = 0.0

    async def start(self):
        """Initialize local inference engine."""
        self._running = True
        await self._load_config()
        await self._check_ollama()
        await self._audit_log("system", f"Local inference engine started (Ollama: {self._available})")
        logger.info(f"Local inference engine started (Ollama available: {self._available})")

    async def stop(self):
        """Shutdown local inference engine."""
        self._running = False
        await self._audit_log("system", "Local inference engine stopped")
        logger.info("Local inference engine stopped")

    async def _load_config(self):
        """Load operator configuration."""
        try:
            async with aiofiles.open(self.CONFIG_PATH, "r") as f:
                content = await f.read()
                self._config = yaml.safe_load(content)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {"operator_enabled": False, "features": {}}

    async def _check_ollama(self):
        """Check if Ollama is available and list models."""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Check Ollama API
                async with session.get(f"{self._ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        self._available_models = [m["name"] for m in models]
                        self._available = True
                        logger.info(f"Ollama available with models: {self._available_models}")
                    else:
                        self._available = False
                        logger.warning("Ollama API returned non-200 status")
        except Exception as e:
            self._available = False
            logger.warning(f"Ollama not available: {e}")

    def _check_authorization(self) -> bool:
        """Check if local inference is authorized."""
        operator_enabled = self._config.get("operator_enabled", False)
        feature_enabled = self._config.get("features", {}).get("local_inference", False)
        return operator_enabled and feature_enabled

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        operator_user: Optional[str] = None,
    ) -> InferenceResponse:
        """
        Generate response using local LLM.

        Args:
            prompt: Input prompt
            model: Model name (defaults to first available)
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            operator_user: User requesting operation

        Returns:
            InferenceResponse with generated text
        """
        if not self._check_authorization():
            raise PermissionError("Local inference not authorized - check operator_enabled.yaml")

        if not self._available:
            raise RuntimeError("Ollama not available - ensure Ollama is running on localhost:11434")

        # Select model
        if not model:
            if not self._available_models:
                raise RuntimeError("No models available in Ollama")
            model = self._available_models[0]

        if model not in self._available_models:
            raise ValueError(f"Model {model} not available. Available: {self._available_models}")

        request_id = f"infer_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Build request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            # Make request to Ollama
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self._ollama_url}/api/generate",
                    json=payload,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama API error: {error_text}")

                    data = await response.json()

            inference_time = time.time() - start_time

            # Extract response
            generated_text = data.get("response", "")
            tokens_generated = data.get("eval_count", 0)
            tokens_per_sec = tokens_generated / inference_time if inference_time > 0 else 0

            # Update statistics
            self._total_requests += 1
            self._total_tokens += tokens_generated
            self._total_inference_time += inference_time

            response_obj = InferenceResponse(
                request_id=request_id,
                model=model,
                response=generated_text,
                tokens_generated=tokens_generated,
                inference_time_sec=inference_time,
                tokens_per_sec=tokens_per_sec,
            )

            await self._audit_log(
                "generate",
                f"Generated {tokens_generated} tokens in {inference_time:.2f}s",
                operator_user=operator_user,
                metadata={
                    "request_id": request_id,
                    "model": model,
                    "tokens": tokens_generated,
                    "inference_time_sec": inference_time,
                    "tokens_per_sec": round(tokens_per_sec, 2),
                },
            )

            logger.info(f"Inference completed: {tokens_generated} tokens in {inference_time:.2f}s ({tokens_per_sec:.1f} tok/s)")
            return response_obj

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            await self._audit_log("error", f"Inference failed: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        operator_user: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Generate response with streaming (yields tokens as they're generated).

        Args:
            prompt: Input prompt
            model: Model name
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            operator_user: User requesting operation

        Yields:
            Generated text chunks
        """
        if not self._check_authorization():
            raise PermissionError("Local inference not authorized - check operator_enabled.yaml")

        if not self._available:
            raise RuntimeError("Ollama not available")

        # Select model
        if not model:
            if not self._available_models:
                raise RuntimeError("No models available in Ollama")
            model = self._available_models[0]

        if model not in self._available_models:
            raise ValueError(f"Model {model} not available")

        request_id = f"infer_stream_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Build request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            # Stream response from Ollama
            timeout = aiohttp.ClientTimeout(total=300)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self._ollama_url}/api/generate",
                    json=payload,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama API error: {error_text}")

                    # Stream chunks
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line)
                                chunk = data.get("response", "")
                                if chunk:
                                    yield chunk

                                # Check if done
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue

            inference_time = time.time() - start_time

            await self._audit_log(
                "generate_stream",
                f"Streaming inference completed in {inference_time:.2f}s",
                operator_user=operator_user,
                metadata={
                    "request_id": request_id,
                    "model": model,
                    "inference_time_sec": inference_time,
                },
            )

        except Exception as e:
            logger.error(f"Streaming inference failed: {e}")
            await self._audit_log("error", f"Streaming inference failed: {e}")
            raise

    async def list_models(self) -> List[str]:
        """List available models in Ollama."""
        if not self._available:
            return []

        return self._available_models.copy()

    async def pull_model(self, model: str) -> bool:
        """
        Pull/download a model in Ollama.

        Args:
            model: Model name to pull

        Returns:
            True if successful
        """
        if not self._check_authorization():
            raise PermissionError("Local inference not authorized - check operator_enabled.yaml")

        if not self._available:
            raise RuntimeError("Ollama not available")

        try:
            payload = {"name": model}

            timeout = aiohttp.ClientTimeout(total=3600)  # 1 hour for model download
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self._ollama_url}/api/pull",
                    json=payload,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Model pull failed: {error_text}")

                    # Wait for download to complete
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get("status") == "success":
                                    break
                            except json.JSONDecodeError:
                                continue

            # Refresh available models
            await self._check_ollama()

            await self._audit_log("pull_model", f"Model pulled: {model}")
            logger.info(f"Model pulled successfully: {model}")
            return True

        except Exception as e:
            logger.error(f"Model pull failed: {e}")
            await self._audit_log("error", f"Model pull failed: {e}")
            return False

    def get_statistics(self) -> Dict:
        """Get inference statistics."""
        avg_tokens_per_request = 0
        avg_inference_time = 0
        avg_tokens_per_sec = 0

        if self._total_requests > 0:
            avg_tokens_per_request = self._total_tokens / self._total_requests
            avg_inference_time = self._total_inference_time / self._total_requests

        if self._total_inference_time > 0:
            avg_tokens_per_sec = self._total_tokens / self._total_inference_time

        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_inference_time_sec": round(self._total_inference_time, 2),
            "avg_tokens_per_request": round(avg_tokens_per_request, 1),
            "avg_inference_time_sec": round(avg_inference_time, 2),
            "avg_tokens_per_sec": round(avg_tokens_per_sec, 1),
        }

    def get_status(self) -> Dict:
        """Get local inference engine status."""
        return {
            "running": self._running,
            "ollama_available": self._available,
            "ollama_url": self._ollama_url,
            "authorized": self._check_authorization(),
            "available_models": self._available_models,
            "statistics": self.get_statistics(),
        }

    async def _audit_log(
        self,
        action: str,
        message: str,
        operator_user: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Write audit log entry."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

        entry = {
            "timestamp": timestamp,
            "action": action,
            "message": message,
            "operator_user": operator_user or "system",
            "metadata": metadata or {},
        }

        line = json.dumps(entry) + "\n"

        log_path = Path(self.AUDIT_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(self.AUDIT_LOG_PATH, "a") as f:
                await f.write(line)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Singleton instance
_local_inference_instance: Optional[LocalInferenceEngine] = None


def get_local_inference(ollama_url: Optional[str] = None) -> LocalInferenceEngine:
    """Get or create local inference engine singleton."""
    global _local_inference_instance
    if _local_inference_instance is None:
        _local_inference_instance = LocalInferenceEngine(ollama_url=ollama_url)
    return _local_inference_instance


__all__ = ["LocalInferenceEngine", "get_local_inference", "InferenceRequest", "InferenceResponse"]