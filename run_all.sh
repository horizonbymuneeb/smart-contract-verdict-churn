#!/usr/bin/env bash
# Reproduce the local arm end to end (CPU). Run from the repository root.
set -euo pipefail
# 1. Dataset (optional: data/contracts.json is already included)
if [ "${REBUILD_DATA:-0}" = "1" ]; then
  git clone https://github.com/smartbugs/smartbugs-curated && git -C smartbugs-curated checkout 230e649123477eff332742a59a1c7cc6dc286cab
  git clone https://github.com/SmartContractSecurity/SWC-registry && git -C SWC-registry checkout 1b6227074ecd180b374e4844153afdda0332f979
  python build_dataset.py
fi
M=${MODELS_DIR:-/tmp/models}
# 2. Models (public GGUF files, no token needed); verify against model_sha256.txt afterwards
python dl.py Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF qwen2.5-coder-0.5b-instruct-fp16.gguf qwen2.5-coder-0.5b-instruct-q8_0.gguf qwen2.5-coder-0.5b-instruct-q4_k_m.gguf
python dl.py bartowski/Llama-3.2-1B-Instruct-GGUF Llama-3.2-1B-Instruct-f16.gguf Llama-3.2-1B-Instruct-Q8_0.gguf Llama-3.2-1B-Instruct-Q4_K_M.gguf
python dl.py ggml-org/Qwen3-0.6B-GGUF Qwen3-0.6B-f16.gguf
python quantize.py $M/Qwen3-0.6B-f16.gguf $M/Qwen3-0.6B-Q8_0.gguf q8_0
python quantize.py $M/Qwen3-0.6B-f16.gguf $M/Qwen3-0.6B-Q4_K_M.gguf q4_k_m
# 3. Runs (resume-safe; outputs go to raw/<tag>__<quant>.jsonl)
python run_audit.py qwen2.5-coder-0.5b fp16   $M/qwen2.5-coder-0.5b-instruct-fp16.gguf
python run_audit.py qwen2.5-coder-0.5b q8_0   $M/qwen2.5-coder-0.5b-instruct-q8_0.gguf
python run_audit.py qwen2.5-coder-0.5b q4_k_m $M/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf
REVERSE=1 python run_audit.py qwen2.5-coder-0.5b fp16_rep $M/qwen2.5-coder-0.5b-instruct-fp16.gguf
python run_audit.py llama-3.2-1b fp16   $M/Llama-3.2-1B-Instruct-f16.gguf
python run_audit.py llama-3.2-1b q8_0   $M/Llama-3.2-1B-Instruct-Q8_0.gguf
python run_audit.py llama-3.2-1b q4_k_m $M/Llama-3.2-1B-Instruct-Q4_K_M.gguf
python run_audit.py qwen3-0.6b fp16   $M/Qwen3-0.6B-f16.gguf
python run_audit.py qwen3-0.6b q8_0   $M/Qwen3-0.6B-Q8_0.gguf
python run_audit.py qwen3-0.6b q4_k_m $M/Qwen3-0.6B-Q4_K_M.gguf
# 4. Analysis and paper tables
python analyze.py
python parser_sensitivity.py
(cd api && python analyze.py && python make_summary_tables.py)
python paper/make_paper_tables.py
