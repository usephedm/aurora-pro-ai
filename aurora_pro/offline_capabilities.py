from __future__ import annotations

from typing import Any


class OfflineAISystem:
    """Local fallback using Ollama and/or vLLM.

    Notes:
      - vLLM does not serve EXL2 quantized models. Use FP16 with vLLM.
      - EXL2 4-bit is supported by ExLlamaV2 runtimes, not vLLM.
    """

    def __init__(self) -> None:
        self.is_online = self._check_connectivity()

    def _check_connectivity(self) -> bool:
        try:
            import requests  # type: ignore

            requests.get("https://api.anthropic.com", timeout=2)
            return True
        except Exception:
            return False

    async def generate_with_fallback(self, prompt: str) -> str:
        if self.is_online:
            try:
                return await self._cloud_generation(prompt)
            except Exception as exc:  # pragma: no cover
                print(f"[FALLBACK] Cloud failed: {exc}. Using local models.")
                return await self._local_generation(prompt)
        else:
            print("[OFFLINE] Using local inference only")
            return await self._local_generation(prompt)

    async def _cloud_generation(self, prompt: str) -> str:
        # Placeholder: integrate cloud provider
        return f"[Cloud] {prompt[:64]}..."

    async def _local_generation(self, prompt: str) -> str:
        # Prefer Ollama if available
        try:
            import ollama  # type: ignore

            client = ollama.Client()
            out = client.generate(model="qwen2.5:7b", prompt=prompt)
            return out.get("response", "")
        except Exception:
            pass

        # Fallback to vLLM Python API (must target FP16 model)
        try:
            from vllm import LLM, SamplingParams  # type: ignore

            engine = LLM(
                model="/models/fp16/Qwen2.5-7B-Instruct",
                gpu_memory_utilization=0.9,
                tensor_parallel_size=1,
                trust_remote_code=True,
            )
            sampling = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=1024)
            outputs = engine.generate([prompt], sampling)
            return outputs[0].outputs[0].text
        except Exception as exc:
            return f"[Local inference unavailable] {exc}"

