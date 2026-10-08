# Phase 1 — Quantization-induced verdict churn in small smart-contract auditor LLMs

Muneeb Anjum (independent researcher). Run on a 2-vCPU Linux CPU machine, 2026-10-08. All numbers below come from `results/results.csv` and `results/per_class_flips.csv`, which `analyze.py` computes from the raw outputs in `raw/*.jsonl`. Nothing here was submitted anywhere.

## Setup
- **Data (175 contracts).**
  - **Vulnerable (143):** SmartBugs-curated, https://github.com/smartbugs/smartbugs-curated, commit `230e649123477eff332742a59a1c7cc6dc286cab` (2024-06-16). Each contract is labelled with its DASP folder, and every contract carries a single DASP category in `vulnerabilities.json`. Class counts: unchecked_low_level_calls 52, reentrancy 31, access_control 18, arithmetic 15, bad_randomness 8, denial_of_service 6, time_manipulation 5, front_running 4, other 3, short_addresses 1.
  - **Safe (32):** every `*_fixed.sol` sample in the SWC Registry docs, https://github.com/SmartContractSecurity/SWC-registry, commit `1b6227074ecd180b374e4844153afdda0332f979` (2024-08-06), parsed from `entries/docs/SWC-*.md`. These are the registry's own patched versions; many pair with SmartBugs originals, e.g. integer_overflow_*, incorrect_constructor_name*, guess_the_random_number. They are labelled `none`.
  - **Caveat on the safe set:** "fixed for its SWC" does not certify the contract free of every DASP issue. A few target non-DASP SWCs, such as floating pragma and unused variables. No larger credible public set of verified-safe contracts was used.
- **Preprocessing** (`build_dataset.py`):
  - All comments are stripped. SmartBugs files carry `// <yes> <report> CLASS` and `@vulnerable_at_lines` annotations that would leak the label; a check confirmed 0 leaks remain.
  - Runs of 8 or more interior spaces are collapsed, because honeypot contracts hide code far to the right.
  - Code is cut at 4,000 characters, at a line boundary, with a `// ... [truncated]` marker. 15 of 175 contracts are truncated; this is logged per record.
  - Contract and file names are not shown to the model, but contract identifiers inside the code remain.
- **Prompt** (`run_audit.py`):
  - The system prompt is "You are a smart contract security auditor."
  - The user message gives the instructions, lists the 10 DASP categories plus `none`, and asks for JSON only: `{"vulnerable": true/false, "class": "..."}`. The contract follows.
  - Qwen3 gets `/no_think` appended (run in the phase-1b continuation, see below).
- **Inference:** llama-cpp-python 0.3.36 (CPU wheel), n_threads=2, n_ctx=4096, temperature 0, top_k=1, seed 1234, max_tokens 48 (64 for Qwen3).
- **Models (public GGUF, no HF token):**

| Model | Source | Files | Status |
|---|---|---|---|
| Qwen2.5-Coder-0.5B-Instruct | `Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF` (official) | fp16, q8_0, q4_k_m | **done** |
| Qwen2.5-Coder-0.5B-Instruct | same | fp16 repeat, reversed order (noise floor) | **done** |
| Llama-3.2-1B-Instruct | `bartowski/Llama-3.2-1B-Instruct-GGUF` (imatrix quants) | f16, Q4_K_M | **done** |
| Llama-3.2-1B-Instruct | same | Q8_0 | **done** (phase 1b, 2026-10-08 13:49–14:30 UTC) |
| Qwen3-0.6B | `ggml-org/Qwen3-0.6B-GGUF` f16, with Q8_0 and Q4_K_M quantized locally (`quantize.py`, no imatrix) | f16, q8_0, q4_k_m | **done** (phase 1b, 12:32–13:49 UTC) |

  SHA-256 hashes are in `model_sha256.txt` (phase-1b files re-verified with sha256sum before deletion; all GGUF files are now deleted). The hash of the Qwen2.5-0.5B q8_0 file was not recorded because the file was deleted before hashing.
- **Shared parser:** `api/common.py:parse_verdict` is imported read-only, so the local and API arms parse identically. It:
  - strips `<think>` blocks;
  - takes the **last** JSON object that contains `"vulnerable"`;
  - maps vulnerable=false to `none`;
  - maps vulnerable=true with class `none`, or with an invalid class, to `other`.

  An unparsed output counts as "no detection". A separate strict/first-object parser is kept only for the diagnostic columns (strict-JSON failure, inconsistent true+none).
- **Differences from the API arm:**
  - max_tokens is 48 locally versus 4096 for the API (`api/driver.py`).
  - Locally, Qwen3 uses `/no_think`.
  - Locally, greedy decoding runs on llama.cpp CPU with a fixed seed and no cache nonce.
- **Runtime:** about 2.4 h of CPU, including two machine restarts. The runs resumed through the resume-safe jsonl. Mean time per contract: Qwen-0.5B 4.3 s (fp16), 6.6 s (q8_0), 6.5 s (q4_k_m); Llama-1B 10.0 s (f16), 13.7 s (Q4_K_M).

## Main results

### Aggregate metrics (positive class = vulnerable)

| model | quant | parse fail | strict-JSON fail | true+`none` inconsistency | acc | F1 | recall | specificity | class acc (vuln only) | 11-way acc |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5-coder-0.5b | fp16 | 0 | 0 | 0.200 | 0.8171 | 0.8994 | 1.000 | 0.000 | 0.1329 | 0.1086 |
| qwen2.5-coder-0.5b | q8_0 | 0 | 0 | 0.274 | 0.8171 | 0.8994 | 1.000 | 0.000 | 0.1049 | 0.0857 |
| qwen2.5-coder-0.5b | q4_k_m | 0 | 0 | 0.571 | 0.8171 | 0.8994 | 1.000 | 0.000 | 0.0420 | 0.0343 |
| qwen2.5-coder-0.5b | fp16 (repeat) | 0 | 0 | 0.200 | 0.8171 | 0.8994 | 1.000 | 0.000 | 0.1329 | 0.1086 |
| llama-3.2-1b | f16 | 0 | 0 | 0 | 0.8171 | 0.8994 | 1.000 | 0.000 | 0.2098 | 0.1714 |
| llama-3.2-1b | Q4_K_M | 0 | 0 | 0 | 0.8000 | 0.8889 | 0.979 | 0.000 | 0.2657 | 0.2171 |

**Both models say "vulnerable" for every contract at full precision**, including all 32 fixed contracts (specificity 0). Binary accuracy is therefore just the 143/175 base rate. The binary task is degenerate for these sub-1B/1B models with this prompt, and the real signal is in the class verdict.

### Churn against the full-precision reference (n = 175 paired)

| model | quant | binary flips (rate, 95% Wilson CI) | neg / pos flips | McNemar binary (b/c, p) | 11-way verdict flips (rate, CI) | McNemar class (b/c, p) | Δ11-way acc | raw text changed |
|---|---|---|---|---|---|---|---|---|
| qwen2.5-coder-0.5b | q8_0 | 0 (0.000, [0.000,0.021]) | 0 / 0 | 0/0, 1.0 | 32 (0.183, [0.133,0.247]) | 4/0, 0.125 | −0.023 | 48 |
| qwen2.5-coder-0.5b | q4_k_m | 0 (0.000, [0.000,0.021]) | 0 / 0 | 0/0, 1.0 | 80 (0.457, [0.385,0.531]) | 14/1, 0.001 | −0.074 | 137 |
| qwen2.5-coder-0.5b | fp16 repeat (noise floor) | 0 | 0 / 0 | — | **0** ([0.000,0.021]) | — | 0 | **0** |
| llama-3.2-1b | Q4_K_M | 3 (0.017, [0.006,0.049]) | **3 / 0** (all 3 are truly vulnerable contracts) | 3/0, 0.25 | 65 (0.371, [0.303,0.445]) | 3/11, 0.057 | +0.046 | 92 |

- **Noise floor is zero.** The fp16 re-run, in reversed order so KV-prefix reuse differed, reproduced all 175 outputs byte for byte. Every flip above can therefore be attributed to quantization, not to run-to-run nondeterminism.
- **The headline effect matches paper #1, in a different form.** Binary accuracy and F1 do not move at all for Qwen-0.5B (0 binary flips), yet the stated vulnerability class changes on 18.3% of contracts at Q8_0 and 45.7% at Q4_K_M. For Llama-1B, Q4_K_M changes accuracy by −1.7 points, while the class verdict changes on 37.1% of contracts.
  - Q4 net-hurts Qwen class accuracy: 14 correct→wrong versus 1 wrong→correct, McNemar p = 0.001.
  - For Llama the class changes are net-neutral to slightly positive: 3 versus 11, p = 0.057. **Churn and accuracy change are decoupled.**
- **The Qwen Q4 failure mode is a self-contradicting verdict.** The share of outputs saying `vulnerable: true, class: "none"` rises from 20.0% (fp16) to 27.4% (q8_0) to 57.1% (q4_k_m).
- **Llama Q4 negative flips come with format degradation.** 10 of 175 Q4 outputs are rambling multi-object answers versus 0 at f16, and all 3 negative flips are among them.
  - The shared last-object parser counts 3 flips. A first-object parser counts 0 (`results/parser_sensitivity.txt`).
  - The truncation at max_tokens = 48 also shapes which object comes last. This should be reported as a parser-policy-sensitive result, not a clean semantic miss.

### Per-class 11-way verdict flips (flipped / n)
From `results/per_class_flips.csv`:

| true class | n | Qwen q8_0 | Qwen q4_k_m | Llama Q4_K_M |
|---|---|---|---|---|
| unchecked_low_level_calls | 52 | 13 | 30 | 25 |
| none (fixed) | 32 | 2 | 15 | 10 |
| reentrancy | 31 | 4 | 7 | 7 |
| access_control | 18 | 4 | 11 | 2 |
| arithmetic | 15 | 3 | 5 | 8 |
| bad_randomness | 8 | 1 | 5 | 5 (1 negative) |
| denial_of_service | 6 | 2 | 1 | 1 |
| time_manipulation | 5 | 1 | 2 | 3 |
| front_running | 4 | 1 | 2 | 2 |
| other | 3 | 0 | 1 | 2 |
| short_addresses | 1 | 1 | 1 | 0 |

The 2 other Llama negative flips are both unchecked_low_level_calls.

### Example flips
`results/examples.md` holds 5 examples, each with the raw outputs. Among them:
- `lucky_doubler.sol` (bad_randomness): Llama f16 says `access_control`; Q4 says not vulnerable.
- `0x19cf…ab10.sol` (unchecked calls): Llama f16 says `denial_of_service`; Q4 says not vulnerable.
- `parity_wallet_bug_1.sol`: Llama goes from a correct `access_control` to `arithmetic`.
- `auction.sol`: Llama goes from a correct `denial_of_service` to `other`.
- `incorrect_constructor_name1.sol`: Qwen-0.5B goes from a correct `access_control` to `true` + `none`.

## Phase 1b (2026-10-08, 12:32–14:30 UTC): remaining local runs
Llama-3.2-1B Q8_0 and Qwen3-0.6B f16/q8_0/q4_k_m, same settings (temp 0, top_k 1, seed 1234, n_ctx 4096; max_tokens 48 for Llama, 64 for Qwen3 as implemented in `run_audit.py`; Qwen3 `/no_think`). All 175/175 per run, no duplicate or corrupt lines; one machine restart (13:18 UTC) was resumed. Mean s/contract: Qwen3 6.9 (f16), 8.7 (q8_0), 8.7 (q4_k_m); Llama Q8_0 14.0. Numbers from `results/results.csv`, `results/per_class_flips.csv`, `results/parser_sensitivity.txt`.

| model | quant | acc | F1 | recall | spec | binary flips (CI) | neg/pos | McNemar bin b/c, p | 11-way flips (rate, CI) | McNemar class b/c, p | Δ11-way acc | raw text changed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| llama-3.2-1b | Q8_0 | 0.8171 | 0.8994 | 1.000 | 0.000 | 0 [0.000,0.021] | 0/0 | 0/0, 1.0 | 13 (0.074, [0.044,0.123]) | 3/0, 0.25 | −0.017 | 31 |
| qwen3-0.6b | f16 | 0.8114 | 0.8959 | 0.993 | 0.000 | — | — | — | — | — | — | — |
| qwen3-0.6b | q8_0 | 0.8114 | 0.8959 | 0.993 | 0.000 | 0 [0.000,0.021] | 0/0 | 0/0, 1.0 | 2 (0.011, [0.003,0.041]) | 0/0, 1.0 | 0 | 24 |
| qwen3-0.6b | q4_k_m | 0.7314 | 0.8439 | 0.888 | 0.031 | 16 (0.091, [0.057,0.143]) | 16/0 (15 truly vulnerable, 1 fixed) | 15/1, 0.0005 | 28 (0.160, [0.113,0.222]) | 1/1, 1.0 | 0 | 65 |

- **Qwen3 F16** says vulnerable for 174/175 (answers `access_control` for 160); class acc on vulnerable 0.126.
- **Qwen3 Q8_0 is nearly churn-free** (2 class flips, 0 binary). **Llama Q8_0**: 0 binary, 7.4% class churn, 1/175 multi-object output (vs 10 at Q4, 0 at F16).
- **Qwen3 Q4_K_M is the first local configuration with significant binary degradation:** 16 negative flips, McNemar p = 0.0005, accuracy 0.811 → 0.731. Causes: 7 outputs ignore `/no_think` and start a free-text reasoning trace that the 64-token budget cuts before any verdict (unparsed → counted as no detection; parse-fail rate 0.04); 9 are well-formed `{"vulnerable": false, "class": "none"}` (8 vulnerable contracts + the 1 fixed contract, one of them inside an unclosed think block). 0 F16/Q8_0 Qwen3 outputs deviate from the empty-think format vs 8 at Q4_K_M. First-object parser gives the same 16 flips (not parser-sensitive); excluding unparsed outputs instead would leave 9.
- **What changed in the conclusions:** churn is strongly model-dependent. Q8_0 class churn spans 1.1% (Qwen3), 7.4% (Llama), 18.3% (Qwen2.5) with zero binary flips in every model; Q4_K_M class churn spans 16.0–45.7%. "Accuracy-neutral" holds for Qwen2.5 (and roughly Llama) but **not** for Qwen3 at Q4_K_M, where quantization causes real, accuracy-visible recall loss plus loss of control-token compliance (a new failure mode alongside self-contradiction and multi-object format degradation).

## Limitations
- **Only 3 small models from 2 families** (Qwen, Llama), all ≤1B. All planned local runs are now complete (phase 1b).
- **The models are too weak to give a usable binary verdict** (always or almost always "vulnerable" at F16), so binary churn is near zero by construction for Qwen2.5/Llama; Qwen3 Q4_K_M is the exception (real negative flips). Phase 2 needs a model that discriminates, e.g. Qwen2.5-Coder-1.5B/3B or Qwen3-1.7B/4B on a GPU or Colab, and possibly a few-shot prompt.
- **The safe set is small** (32) and only "fixed for one SWC". Some SmartBugs contracts are old Solidity (0.4.x).
- **Truncation:** 15/175 contracts are cut at 4,000 characters.
- **Tight token budget:** max_tokens 48 cuts off verbose answers.
- **Quantization sources are mixed:** official Qwen, bartowski imatrix for Llama, and local non-imatrix for Qwen3 (may contribute to the Qwen3 Q4_K_M degradation).
- **Single prompt, single seed.** Greedy decoding was shown deterministic on one model only (Qwen fp16 repeat).
- Model identifiers in the code (e.g. contract names like `Reentrancy`-style names) can hint the class.
- The parser maps invalid or `none`-with-true classes to `other`, which merges with the real `other` class (3 contracts).

## Files (paths relative to the repository root)
- **Scripts:**
  - `build_dataset.py` builds `data/contracts.json`.
  - `run_audit.py` is the resume-safe runner.
  - `analyze.py` computes the metrics, using `api/common.py:parse_verdict`.
  - `make_summary_tables.py` writes the tables.
  - `quantize.py`, `dl.py` and `bench.py` handle quantizing, downloads and speed benchmarks.
  - `parser_sensitivity.py` regenerates `results/parser_sensitivity.txt`. (The machine-specific shell queues used to schedule the runs are not included; `run_all.sh` reproduces the same sequence.)
  - `paper/`: LaTeX manuscript (elsarticle) `main.tex` + `body.tex` + `abstract.tex` + `refs.bib`, tables generated by `paper/make_paper_tables.py` from the CSVs, compiled `paper/Same_Accuracy_Different_Verdicts_preprint.pdf`.
- **Raw outputs:** `raw/*.jsonl`, one line per contract with the raw model text, prompt tokens, truncation flag and seconds.
- **Results:** `results/results.csv`, `results/per_class_flips.csv`, `results/metrics.json`, `results/tables.md`, `results/examples.md`, `results/parser_sensitivity.txt`.
- **Provenance:** `versions.txt`, `model_sha256.txt`, `logs/`.
- **Earlier runs, excluded from results:** `pilot/` holds the timing pilot and an aborted v0 run that used pre-whitespace-fix data.
