#!/usr/bin/env bash
set -euo pipefail

MODELS_DIR="${MODELS_DIR:-./models}"
HF_CACHE_DIR="${HF_CACHE_DIR:-$HOME/.cache/huggingface}"

declare -A MODELS=(
  ["Hermes-3-8B"]="NousResearch/Hermes-3-Llama-3.1-8B"
  ["Qwen2.5-7B"]="Qwen/Qwen2.5-7B-Instruct"
  ["DeepSeek-R1-7B"]="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
)

echo "🚀 Starting Aurora Pro model setup..."
mkdir -p "$MODELS_DIR"/{fp16,exl2-4bit,ollama}

for model_name in "${!MODELS[@]}"; do
  model_id="${MODELS[$model_name]}"
  output_dir="$MODELS_DIR/fp16/$model_name"
  if [[ ! -d "$output_dir" ]]; then
    echo "📥 Downloading $model_name ($model_id)..."
    huggingface-cli download \
      --local-dir-use-symlinks False \
      --local-dir "$output_dir" \
      "$model_id"
  else
    echo "✅ $model_name already downloaded"
  fi
done

echo "⚙️ Starting quantization process..."
for model_name in "${!MODELS[@]}"; do
  input_dir="$MODELS_DIR/fp16/$model_name"
  output_dir="$MODELS_DIR/exl2-4bit/${model_name}-4bit"
  if [[ -d "$input_dir" && ! -d "$output_dir" ]]; then
    echo "🔧 Quantizing $model_name to EXL2 4-bit..."
    python -m exllamav2.convert \
      --input "$input_dir" \
      --output "$output_dir" \
      --bits 4 \
      --head_bits 6 \
      --calibration_length 2048 || true
  fi
done

echo "🦙 Setting up Ollama models..."
if command -v ollama >/dev/null 2>&1; then
  ollama pull qwen2.5:7b || true
  ollama pull llama3.1:8b || true
else
  echo "⚠️ Ollama not installed, skipping Ollama model setup"
fi

echo "✅ Model setup complete!"
du -sh "$MODELS_DIR"/* || true

