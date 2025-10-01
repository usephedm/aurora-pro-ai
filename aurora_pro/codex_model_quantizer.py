from __future__ import annotations

from pathlib import Path
from typing import Dict

from .codex_orchestrator import CodexCLIOrchestrator


class CodexModelQuantizer:
    def __init__(self, codex_orchestrator: CodexCLIOrchestrator):
        self.codex = codex_orchestrator
        self.models_dir = Path("/models/fp16")
        self.output_dir = Path("/models/exl2-4bit")

    async def quantize_all_models(self) -> Dict:
        """Automated model quantization prompts via Codex CLI."""
        tasks = [
            # Tooling
            """
            Install ExLlamaV2 quantization toolkit:
            pip install --upgrade exllamav2 torch
            """,
            # Hermes
            """
            Quantize Hermes-3-Llama-3.1-8B to EXL2 4-bit:
            python -m exllamav2.convert \
              --input /models/fp16/Hermes-3-Llama-3.1-8B \
              --output /models/exl2-4bit/Hermes-3-8B-4bit \
              --bits 4 \
              --head_bits 6 \
              --calibration_length 2048
            """,
            # Qwen
            """
            Quantize Qwen2.5-7B-Instruct:
            python -m exllamav2.convert \
              --input /models/fp16/Qwen2.5-7B-Instruct \
              --output /models/exl2-4bit/Qwen2.5-7B-4bit \
              --bits 4
            """,
            # vLLM tuning (note: vLLM serves FP16, EXL2 runs via ExLlamaV2)
            """
            Configure vLLM server for FP16 models:
            echo 'VLLM_GPU_MEMORY_UTILIZATION=0.9' | sudo tee -a /etc/environment
            echo 'VLLM_TENSOR_PARALLEL_SIZE=1' | sudo tee -a /etc/environment
            """,
        ]

        return await self.codex.infrastructure_deployment(tasks)

