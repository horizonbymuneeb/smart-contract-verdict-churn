# Same Accuracy, Different Verdicts

Code, data and raw model outputs for the preprint

> Muneeb Anjum. **Same Accuracy, Different Verdicts: Quantization-Induced Verdict Churn in Small LLM Smart-Contract Auditors.** Preprint, 2026. Zenodo, DOI [10.5281/zenodo.23241640](https://doi.org/10.5281/zenodo.23241640).

The study measures **verdict churn**, the share of contracts whose audit verdict changes, when small open LLM auditors are quantized (F16 → Q8_0 → Q4_K_M, GGUF via llama.cpp), and when large models are reached through a third-party OpenAI-compatible routing service. Aggregate accuracy hides most of these changes.

## Summary of results

175 Solidity contracts (143 vulnerable from SmartBugs-curated, 32 patched SWC Registry samples), one fixed JSON-verdict prompt, greedy decoding, one shared parser (`api/common.py:parse_verdict`).

| Model | Format | Binary acc | Class acc (vulnerable) | Binary flips vs F16 | Class (11-way) flips vs F16 | McNemar p (binary) |
|---|---|---|---|---|---|---|
| Qwen2.5-Coder-0.5B-Instruct | F16 | 0.817 | 0.133 | – | – | – |
| | F16 repeat | 0.817 | 0.133 | 0 | 0 (0.0%) | 1.0 |
| | Q8_0 | 0.817 | 0.105 | 0 | 18.3% | 1.0 |
| | Q4_K_M | 0.817 | 0.042 | 0 | 45.7% | 1.0 |
| Llama-3.2-1B-Instruct | F16 | 0.817 | 0.210 | – | – | – |
| | Q8_0 | 0.817 | 0.189 | 0 | 7.4% | 1.0 |
| | Q4_K_M | 0.800 | 0.266 | 3 (3 neg.) | 37.1% | 0.25 |
| Qwen3-0.6B | F16 | 0.811 | 0.126 | – | – | – |
| | Q8_0 | 0.811 | 0.126 | 0 | 1.1% | 1.0 |
| | Q4_K_M | 0.731 | 0.119 | 16 (16 neg.) | 16.0% | 0.0005 |

- At full precision all three small models flag (nearly) every contract as vulnerable, so the vulnerability class carries the signal, and it churns heavily under quantization while binary accuracy barely moves.
- An F16 repeat run (reversed order) reproduced all outputs byte for byte: the churn is not run-to-run noise.
- Qwen3-0.6B at Q4_K_M loses 15 vulnerable-contract detections, partly by ignoring its `/no_think` instruction.
- API arm: across 21 endpoints with at least 65 parsed verdicts, recall is 0.951–1.000 but specificity only 0.400–0.813. The router caches responses, so identical temperature-0 repeats show zero churn by construction; whitespace-perturbed (uncached) repeats show 1.2–1.8% binary churn. One model name served by two providers disagrees on 14 of 172 binary verdicts (p = 0.013).

Full tables: `results/tables.md` (local arm), `api/tables.md` and `api/summary.md` (API arm), and the paper.

## Repository layout

| Path | Contents |
|---|---|
| `build_dataset.py` | Builds `data/contracts.json` from the two upstream repositories (comment stripping, whitespace normalisation, labels) |
| `data/contracts.json` | The 175-contract evaluation set (see `data/NOTICE.md` for provenance and licences) |
| `dl.py`, `quantize.py` | Download public GGUF files; quantize Qwen3-0.6B F16 to Q8_0 / Q4_K_M with llama.cpp (no imatrix) |
| `run_audit.py` | Resume-safe local runner (llama-cpp-python, CPU, greedy) |
| `analyze.py`, `parser_sensitivity.py`, `make_summary_tables.py` | Local-arm metrics, parser-sensitivity check, tables |
| `raw/*.jsonl` | Every local model output, one JSON line per contract and run, including the raw text |
| `results/` | Local-arm metrics (`results.csv`, `per_class_flips.csv`, `metrics.json`, `parser_sensitivity.txt`, `examples.md`, `tables.md`) |
| `api/` | API-arm client and shared parser (`common.py`), runners (`driver.py`, `clp_slow.py`), probe, analysis, raw outputs (`api/raw/*.jsonl`) and results (`results_runs.csv`, `results_churn.csv`, `results.json`, `tables.md`, `summary.md`) |
| `paper/` | LaTeX source (elsarticle), table generator `make_paper_tables.py`, `numbers.json`, and the preprint PDF |
| `docs/local_arm_notes.md` | Detailed notes on the local runs |
| `model_sha256.txt`, `versions.txt` | Model file hashes and software/data versions |
| `run_all.sh` | End-to-end reproduction of the local arm |

## Data sources

| Part | Repository | Commit | Licence |
|---|---|---|---|
| 143 vulnerable contracts | [SmartBugs-curated](https://github.com/smartbugs/smartbugs-curated) | `230e649123477eff332742a59a1c7cc6dc286cab` (2024-06-16) | Apache-2.0 |
| 32 patched contracts (`*_fixed.sol`) | [SWC Registry](https://github.com/SmartContractSecurity/SWC-registry) | `1b6227074ecd180b374e4844153afdda0332f979` (2024-08-06) | MIT |

Both licences permit redistribution; copies are in `third_party_licenses/`. Comments are stripped because SmartBugs files carry `<yes> <report> CLASS` annotations that would leak the label. Contracts longer than 4,000 characters (15 of 175) are truncated at a line boundary.

## Models

All local models are public GGUF files (no access token needed). SHA-256 hashes are in `model_sha256.txt`.

| Model | GGUF source | Formats |
|---|---|---|
| Qwen2.5-Coder-0.5B-Instruct | `Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF` (official) | fp16, q8_0, q4_k_m |
| Llama-3.2-1B-Instruct | `bartowski/Llama-3.2-1B-Instruct-GGUF` (imatrix quants) | f16, Q8_0, Q4_K_M |
| Qwen3-0.6B | `ggml-org/Qwen3-0.6B-GGUF` (f16); Q8_0 and Q4_K_M quantized locally with `quantize.py` | f16, Q8_0, Q4_K_M |

| File | SHA-256 |
|---|---|
| qwen2.5-coder-0.5b-instruct-fp16.gguf | `bb69b303c65113199b19c72f9c75bca449200b6cdf807e0f7d8822f669c02e64` |
| qwen2.5-coder-0.5b-instruct-q4_k_m.gguf | `1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32` |
| qwen2.5-coder-0.5b-instruct-q8_0.gguf | not recorded (file deleted before hashing) |
| Llama-3.2-1B-Instruct-f16.gguf | `1f33ad43d2b85b908ff06fe7002b69806a57359b9b2617ca27d7bdea428ae146` |
| Llama-3.2-1B-Instruct-Q8_0.gguf | `432f310a77f4650a88d0fd59ecdd7cebed8d684bafea53cbff0473542964f0c3` |
| Llama-3.2-1B-Instruct-Q4_K_M.gguf | `6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83` |
| Qwen3-0.6B-f16.gguf | `ab9004daf660cd6a6ba1c07556e74fcceb2b756063ccce3f9c69d3a637b361cc` |
| Qwen3-0.6B-Q8_0.gguf (local) | `84c0dbe606526d5907251d88ea88b41457f46ce456e9a333d5d2b6245a95cafe` |
| Qwen3-0.6B-Q4_K_M.gguf (local) | `ebfd42b196c529c3b692c549585e62cc6e817b5a5aff8375b3724cdfbafa651a` |

Inference settings: llama-cpp-python 0.3.36 (CPU), n_threads=2, n_ctx=4096, temperature 0, top_k=1, seed 1234, max_tokens 48 (64 for Qwen3, which also gets `/no_think`).

## How to reproduce

```bash
python -m venv venv && . venv/bin/activate
pip install -r requirements.txt

# Recompute every metric and table from the released raw outputs (seconds):
python analyze.py
python parser_sensitivity.py
(cd api && python analyze.py && python make_summary_tables.py)
python paper/make_paper_tables.py

# Re-run the local models from scratch (about 2-3 h on a 2-vCPU CPU):
mv raw raw_released           # the runner is resume-safe and skips contracts already in raw/
./run_all.sh                  # REBUILD_DATA=1 ./run_all.sh also rebuilds data/contracts.json
```

Recomputing from the released raw outputs reproduces `results/results.csv`, `results/per_class_flips.csv`, `results/parser_sensitivity.txt`, `api/results_runs.csv`, `api/results_churn.csv` and the paper tables exactly.

**API arm.** The large models were queried through a third-party OpenAI-compatible routing service (a closed commercial aggregator). Its URL is not published, and its back-ends, model versions and serving precision cannot be pinned, so these calls cannot be guaranteed to be reproducible. The raw responses (returned model names, outputs, finish reasons, latencies and token counts) are released in `api/raw/`. To run the same protocol against any OpenAI-compatible endpoint:

```bash
export SCAUDIT_API_BASE=https://<your-endpoint>/v1
export SCAUDIT_API_KEY=...          # if the endpoint needs one
cd api && python driver.py $(( $(date +%s) + 3600 )) 4 <model-id>:<outfile>.jsonl
```

## Citation

```bibtex
@misc{anjum2026verdicts,
  author    = {Anjum, Muneeb},
  title     = {Same Accuracy, Different Verdicts: Quantization-Induced Verdict Churn in Small {LLM} Smart-Contract Auditors},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23241640},
  url       = {https://doi.org/10.5281/zenodo.23241640}
}
```

Related earlier work by the same author: *Quantized Guardians* (decision churn in quantized prompt-injection detectors), DOI [10.5281/zenodo.23233203](https://doi.org/10.5281/zenodo.23233203).

## Licence

Code: MIT (see `LICENSE`). The contract data keeps its upstream licences (Apache-2.0 and MIT; see `data/NOTICE.md`). The preprint PDF and the Zenodo archive are released under CC BY 4.0.
