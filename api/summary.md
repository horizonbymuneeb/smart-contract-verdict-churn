# API arm — verdict churn in LLM smart-contract auditors (paper #2, Muneeb Anjum)

Run: 2026-10-08, 09:53–11:22 UTC. Router: a third-party OpenAI-compatible routing service (closed commercial aggregator; `/v1/chat/completions` endpoint). Its URL is not published; set `SCAUDIT_API_BASE` to re-run.
Data: `data/contracts.json` (sha1 f6f25163…, v1 = the 10:02 UTC rebuild with interior-whitespace collapse; 175 = 143 vulnerable SmartBugs-curated + 32 SWC *_fixed safe).
Prompt + truncation: exactly the SYS/INSTR/`truncate()` in `../run_audit.py`, checked programmatically against the final revision (sha1 5cada6d…): identical for all 175 items. The local script's Qwen3-only `/no_think` suffix is **not** applied here (API models).
Decoding: temperature 0, max_tokens 4096 (reasoning models need the room; run_audit.py uses 48 locally), up to 4 parallel requests per run, up to 8 retries with exponential backoff, resume-safe jsonl.
Parser: `../run_audit.py` contains **no** JSON-verdict parser (it only logs raw text), so one is defined in `api/common.py:parse_verdict` (drop `<think>`, take the last `{...}` containing "vulnerable", json-load, regex fallback; class normalized to the 11 labels, unknown → `other`; vulnerable=false → `none`). The local arm should import it so both arms use the same parser.

## Key findings (computed values only)
1. **The router caches responses.** A repeated identical request (same model + messages) returns the **same response id** in ~0.75–1.0 s, even for reasoning models that took 15–35 s the first time. `user`, `seed`, `top_p`, `n`, `stream` and `max_tokens` do not change the cache key. As a result every "identical call" re-run gave 0 changed verdicts and byte-identical text: agy/claude-sonnet-4-6, agy/claude-opus-4-6-thinking, opencode-go/deepseek-v4.1-flash and cap/qwen3.8-27b, each 175/175. **This 0% says nothing about model determinism.**
2. **Uncached repeats (B′).** To get past the cache, a whitespace-only suffix was appended to the user message (`"\n"` = ws1, `" \n"` = ws2). Between the two uncached runs ws1 and ws2 there were binary flips of 3/175 (1.7%) for sonnet-4-6, 3/175 (1.7%) for opus-4-6-thinking, 2/109 both-parsed (1.8%) for deepseek-v4.1-flash, with another 22 items flipping between parsed and not parsed, and 1/84 (1.2%) for laguna-s-2.1. Class flips were 2.9–5.1% for the large models and 13.1% for laguna. None of the McNemar tests is significant (p ≥ 0.25). Caveat: these runs differ by one trailing whitespace character, so the numbers measure nondeterminism plus sensitivity to a trivial prompt change. Treat them as an upper bound.
3. **Cross-provider (A).** Neither planned pair could be measured. clp/qwen/qwen3.8-27b:free and clp/cline-free/deepseek-v4.1-flash returned **0 successful responses** in 49 and 48 attempt records over 10:00–11:20 UTC (429 `model_cooldown` with one cooling credential, plus some 504s). That was with a single worker that waited out every `reset_seconds`. A **substitute pair** was run instead: claude-opus-4.6, cap vs agy (the agy id is `claude-opus-4-6-thinking`). Over 172 contracts both parsed: **14 binary flips (8.1%)**, 31 class flips (18.0%), McNemar b/c = 12/2 (cap right & agy wrong / the reverse), **exact p = 0.013**. 10 of the 14 flips are safe contracts, where agy says vulnerable. The two endpoints are clearly configured differently: mean completion tokens were 1483 on cap vs 17 on agy, so this is the "same model name, different serving stack" case, not a clean same-weights comparison.
4. **Baselines (C).** 22 model endpoints (r1 runs) returned usable responses. 21 of them have at least 65 parsed verdicts and give the accuracy ranges below; clp/lfm-2.5-2.6b-free (20 covered) is excluded from summary ranges. 19 have full 175/175 coverage. Partial r1 runs: cap/claude-opus-4.6 172, clp dots-3-note 145, lfm-2.5-2.6b 20 (the uncached laguna repeats are also partial: ws1 103 / ws2 84). Every model flags almost everything as vulnerable: recall 0.95–1.00, but specificity on the 32 safe contracts only 0.40–0.81. Parse failures are almost all refusals or empty outputs, not bad JSON:
   - Refusals: agy gemini-3.1-pro-high 110/175 ("Sorry, I cannot…"), gemini-3.6-flash-tiered 90, gemini-3-flash 44, gemini-3.8-flash-tiered 22 (blocked by Gemini's safety filter).
   - Empty outputs: opencode-go deepseek-v4.1-flash 58/175. Its hidden reasoning used up all 4096 tokens (finish_reason=length, empty content).
   - Every other model parsed 100%, except nemotron-3-nano-omni (8 failures).
Dataset: 175 contracts (143 vulnerable SmartBugs-curated, 32 SWC *_fixed safe).

### A. Cross-provider churn

| pair | both covered | both parsed | parse-status flips | binary flips (rate) | class flips (rate) | raw text differs | McNemar b/c | exact p | binary flips by gold class |
|---|---|---|---|---|---|---|---|---|---|
| qwen3.8-27b: cap vs clp:free | 0 | 0 | 0 | 0 () | 0 () | 0 | 0/0 | 1.000 | {} |
| deepseek-v4.1-flash: opencode-go vs clp cline-free | 0 | 0 | 0 | 0 () | 0 () | 0 | 0/0 | 1.000 | {} |
| SUBSTITUTE claude-opus-4.6: cap vs agy (agy id says -thinking) | 172 | 172 | 0 | 14 (0.081) | 31 (0.180) | 31 | 12/2 | 0.013 | {"arithmetic": 2, "front_running": 1, "time_manipulation": 1, "none": 10} |

### B. Run-to-run churn (temperature 0)

| pair | both covered | both parsed | parse-status flips | binary flips (rate) | class flips (rate) | raw text differs | McNemar b/c | exact p | binary flips by gold class |
|---|---|---|---|---|---|---|---|---|---|
| CACHED agy/claude-sonnet-4-6 r1 vs r2 | 175 | 175 | 0 | 0 (0.000) | 0 (0.000) | 0 | 0/0 | 1.000 | {} |
| CACHED agy/claude-opus-4-6-thinking r1 vs r2 | 175 | 175 | 0 | 0 (0.000) | 0 (0.000) | 0 | 0/0 | 1.000 | {} |
| CACHED opencode-go/deepseek-v4.1-flash r1 vs r2 | 175 | 117 | 0 | 0 (0.000) | 0 (0.000) | 0 | 0/0 | 1.000 | {} |
| cap/qwen3.8-27b r1 vs r2 | 175 | 175 | 0 | 0 (0.000) | 0 (0.000) | 0 | 0/0 | 1.000 | {} |
| cap/deepseek-v4-flash-0731 r1 vs r2 | 0 | 0 | 0 | 0 () | 0 () | 0 | 0/0 | 1.000 | {} |
| WS agy_claude-sonnet-4-6 ws1 vs ws2 (both uncached) | 175 | 175 | 0 | 3 (0.017) | 9 (0.051) | 11 | 2/1 | 1.000 | {"none": 3} |
| WS agy_claude-sonnet-4-6 r1 vs ws1 | 175 | 175 | 0 | 1 (0.006) | 6 (0.034) | 7 | 1/0 | 1.000 | {"none": 1} |
| WS agy_claude-sonnet-4-6 r1 vs ws2 | 175 | 175 | 0 | 2 (0.011) | 6 (0.034) | 9 | 2/0 | 0.500 | {"none": 2} |
| WS agy_claude-opus-4-6-thinking ws1 vs ws2 (both uncached) | 175 | 175 | 0 | 3 (0.017) | 5 (0.029) | 5 | 1/2 | 1.000 | {"arithmetic": 1, "time_manipulation": 1, "none": 1} |
| WS agy_claude-opus-4-6-thinking r1 vs ws1 | 175 | 175 | 0 | 2 (0.011) | 3 (0.017) | 3 | 0/2 | 0.500 | {"none": 2} |
| WS agy_claude-opus-4-6-thinking r1 vs ws2 | 175 | 175 | 0 | 3 (0.017) | 4 (0.023) | 4 | 0/3 | 0.250 | {"arithmetic": 1, "time_manipulation": 1, "none": 1} |
| WS opencode-go_deepseek-v4.1-flash ws1 vs ws2 (both uncached) | 175 | 109 | 22 | 2 (0.018) | 3 (0.028) | 25 | 2/0 | 0.500 | {"time_manipulation": 1, "none": 1} |
| WS opencode-go_deepseek-v4.1-flash r1 vs ws1 | 175 | 102 | 28 | 0 (0.000) | 3 (0.029) | 31 | 0/0 | 1.000 | {} |
| WS opencode-go_deepseek-v4.1-flash r1 vs ws2 | 175 | 107 | 28 | 1 (0.009) | 2 (0.019) | 30 | 1/0 | 1.000 | {"time_manipulation": 1} |
| WS clp_laguna-s-2.1-free ws1 vs ws2 (both uncached) | 84 | 84 | 0 | 1 (0.012) | 11 (0.131) | 11 | 0/1 | 1.000 | {"access_control": 1} |
| WS clp_laguna-s-2.1-free r1 vs ws1 | 103 | 103 | 0 | 4 (0.039) | 17 (0.165) | 17 | 3/1 | 0.625 | {"access_control": 1, "front_running": 2, "time_manipulation": 1} |
| WS clp_laguna-s-2.1-free r1 vs ws2 | 84 | 84 | 0 | 2 (0.024) | 16 (0.191) | 16 | 2/0 | 0.500 | {"front_running": 2} |

### C. Per-run accuracy (parsed items only; parse failures excluded from acc/F1 and reported separately)

| run | coverage /175 | parsed | parse-fail rate | refusals | empty outputs | binary acc | precision | recall | F1 | safe specificity (TN/safe parsed) | class acc (vuln, strict) | median latency s | mean prompt tok | mean completion tok | returned model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agy_claude-opus-4-6-thinking__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.874 | 0.880 | 0.979 | 0.927 | 0.406 | 0.748 | 3.100 | 594.000 | 17.100 | claude-opus-4-6-thinking |
| agy_claude-opus-4-6-thinking__r2 | 175 | 175 | 0.000 | 0 | 0 | 0.874 | 0.880 | 0.979 | 0.927 | 0.406 | 0.748 | 0.750 | 594.000 | 17.100 | claude-opus-4-6-thinking |
| agy_claude-opus-4-6-thinking__ws1 | 175 | 175 | 0.000 | 0 | 0 | 0.886 | 0.892 | 0.979 | 0.933 | 0.469 | 0.755 | 3.190 | 594.000 | 17.000 | claude-opus-4-6-thinking |
| agy_claude-opus-4-6-thinking__ws2 | 175 | 175 | 0.000 | 0 | 0 | 0.891 | 0.887 | 0.993 | 0.937 | 0.438 | 0.755 | 3.250 | 595.000 | 17.100 | claude-opus-4-6-thinking |
| agy_claude-sonnet-4-6__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.903 | 0.899 | 0.993 | 0.944 | 0.500 | 0.818 | 2.290 | 594.000 | 21.500 | claude-sonnet-4-6 |
| agy_claude-sonnet-4-6__r2 | 175 | 175 | 0.000 | 0 | 0 | 0.903 | 0.899 | 0.993 | 0.944 | 0.500 | 0.818 | 0.770 | 594.000 | 21.500 | claude-sonnet-4-6 |
| agy_claude-sonnet-4-6__ws1 | 175 | 175 | 0.000 | 0 | 0 | 0.897 | 0.893 | 0.993 | 0.940 | 0.469 | 0.825 | 2.330 | 594.000 | 23.800 | claude-sonnet-4-6 |
| agy_claude-sonnet-4-6__ws2 | 175 | 175 | 0.000 | 0 | 0 | 0.891 | 0.887 | 0.993 | 0.937 | 0.438 | 0.797 | 2.460 | 595.000 | 22.100 | claude-sonnet-4-6 |
| agy_gemini-3-flash__r1 | 175 | 131 | 0.251 | 44 | 0 | 0.924 | 0.913 | 1.000 | 0.955 | 0.615 | 0.781 | 9.680 | 544.900 | 24.500 | gemini-3-flash |
| agy_gemini-3.1-flash-lite__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.891 | 0.903 | 0.972 | 0.936 | 0.531 | 0.636 | 5.800 | 544.900 | 14.600 | gemini-3.1-flash-lite |
| agy_gemini-3.1-pro-high__r1 | 175 | 65 | 0.629 | 110 | 0 | 0.923 | 0.940 | 0.959 | 0.950 | 0.812 | 0.837 | 12.370 | 544.900 | 35.300 | gemini-3.1-pro-high |
| agy_gemini-3.5-flash-lite__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.914 | 0.916 | 0.986 | 0.950 | 0.594 | 0.755 | 4.690 | 544.900 | 15.100 | gemini-3.5-flash-lite |
| agy_gemini-3.6-flash-tiered__r1 | 175 | 85 | 0.514 | 90 | 0 | 0.953 | 0.947 | 1.000 | 0.973 | 0.714 | 0.859 | 17.050 | 544.900 | 31.800 | gemini-3.6-flash-tiered |
| agy_gemini-3.7-flash-tiered__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.903 | 0.909 | 0.979 | 0.943 | 0.562 | 0.755 | 8.880 | 544.900 | 17.600 | gemini-3.7-flash-tiered |
| agy_gemini-3.8-flash-tiered__r1 | 175 | 153 | 0.126 | 0 | 0 | 0.941 | 0.941 | 0.992 | 0.966 | 0.680 | 0.844 | 16.640 | 544.900 | 14.700 | gemini-3.8-flash-tiered |
| agy_gpt-oss-120b-medium__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.863 | 0.889 | 0.951 | 0.919 | 0.469 | 0.685 | 4.200 | 536.600 | 395.300 | gpt-oss-120b-medium |
| cap_claude-opus-4.6__r1 | 172 | 172 | 0.000 | 0 | 0 | 0.936 | 0.933 | 0.993 | 0.962 | 0.677 | 0.716 | 31.680 | 682.900 | 1483.100 | claude-opus-4.6 |
| cap_deepseek-v4-flash-0731__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.926 | 0.922 | 0.993 | 0.956 | 0.625 | 0.706 | 34.960 | 692.100 | 1330.600 | deepseek-v4-flash-0731 |
| cap_glm-5.2__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.926 | 0.922 | 0.993 | 0.956 | 0.625 | 0.713 | 33.370 | 696.100 | 1308.000 | glm-5.2 |
| cap_qwen3.8-27b__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.926 | 0.928 | 0.986 | 0.956 | 0.656 | 0.692 | 27.810 | 682.100 | 1255.700 | qwen3.8-27b |
| cap_qwen3.8-27b__r2 | 175 | 175 | 0.000 | 0 | 0 | 0.926 | 0.928 | 0.986 | 0.956 | 0.656 | 0.692 | 0.960 | 682.100 | 1255.700 | qwen3.8-27b |
| clp_cline-free_mimo-v2.6-flash__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.891 | 0.908 | 0.965 | 0.936 | 0.562 | 0.664 | 19.640 | 412.500 | 697.300 | xiaomi/mimo-v2.6-flash, cline-free/mimo-v2.6-flash |
| clp_cline-free_muse-spark-1.3__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.920 | 0.927 | 0.979 | 0.952 | 0.656 | 0.678 | 18.040 | 414.100 | 1607.000 | meta/muse-spark-1.3-contributor, cline-free/muse-spark-1.3-contributor |
| clp_dots-3-note-preview-free__r1 | 145 | 145 | 0.000 | 0 | 0 | 0.952 | 0.993 | 0.958 | 0.975 | 0.667 | 0.662 | 42.780 | 430.700 | 2443.000 | dots-studio/dots-3-note-preview:free |
| clp_laguna-s-2.1-free__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.886 | 0.887 | 0.986 | 0.934 | 0.438 | 0.608 | 4.160 | 464.900 | 26.900 | poolside/laguna-s-2.1:free |
| clp_laguna-s-2.1-free__ws1 | 103 | 103 | 0.000 | 0 | 0 | 0.961 | 1.000 | 0.961 | 0.980 |  | 0.699 | 30.430 | 481.100 | 991.100 | poolside/laguna-s-2.1:free |
| clp_laguna-s-2.1-free__ws2 | 84 | 84 | 0.000 | 0 | 0 | 0.964 | 1.000 | 0.964 | 0.982 |  | 0.798 | 28.330 | 475.900 | 1010.300 | poolside/laguna-s-2.1:free |
| clp_lfm-2.5-2.6b-free__r1 | 20 | 20 | 0.000 | 0 | 0 | 0.650 | 1.000 | 0.650 | 0.788 |  | 0.500 | 48.860 | 454.800 | 2342.800 | liquid/lfm-2.5-2.6b:free |
| clp_nemotron-3-nano-omni-30b-free__r1 | 175 | 167 | 0.046 | 0 | 0 | 0.856 | 0.879 | 0.956 | 0.916 | 0.400 | 0.540 | 34.490 | 437.800 | 1121.600 | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free |
| clp_nemotron-3-super-120b-free__r1 | 175 | 175 | 0.000 | 0 | 0 | 0.880 | 0.886 | 0.979 | 0.930 | 0.438 | 0.615 | 16.290 | 437.800 | 1199.200 | nvidia/nemotron-3-super-120b-a12b:free |
| opencode-go_deepseek-v4.1-flash__r1 | 175 | 117 | 0.331 | 0 | 58 | 0.949 | 0.952 | 0.990 | 0.971 | 0.706 | 0.780 | 15.350 | 444.400 | 2026.500 | deepseek-v4.1-flash |
| opencode-go_deepseek-v4.1-flash__r2 | 175 | 117 | 0.331 | 0 | 58 | 0.949 | 0.952 | 0.990 | 0.971 | 0.706 | 0.780 | 0.850 | 444.400 | 2026.500 | deepseek-v4.1-flash |
| opencode-go_deepseek-v4.1-flash__ws1 | 175 | 115 | 0.343 | 0 | 60 | 0.922 | 0.922 | 0.990 | 0.955 | 0.579 | 0.792 | 22.770 | 444.400 | 2082.800 | deepseek-v4.1-flash |
| opencode-go_deepseek-v4.1-flash__ws2 | 175 | 125 | 0.286 | 0 | 50 | 0.920 | 0.929 | 0.981 | 0.954 | 0.579 | 0.792 | 20.500 | 445.400 | 1905.300 | deepseek-v4.1-flash |

## Coverage, failures and what was not run
- **Down or unusable during the run:** cap/kimi-k3 (502 empty upstream at the probe; never reached in the queue). The clp :free qwen3.8-27b and cline-free deepseek-v4.1-flash pair had 0 successes (above). cap/* "other" models in the 15:05 probe (gpt-5.5/5.6, claude-opus-4.7/4.8/5, sonnet-5, fable, mythos, glm-5.3, qwen3.8-max, deepseek-v4-pro, grok-4.5/4.6, gemini-3.7-flash, muse-spark-1.1) all returned 504 "upstream request deadline exceeded" at about 120 s. cap was saturated (about 1 response/min/model at the time). clp nemotron-3.5-lightning, cohere north-mini-code and ling-3.0-flash returned 504; stealth/space-bunny-alpha returned 429.
- **Answered the probe but not run** (not enough time or capacity on cap): cap/gemma-2-2b, cap/seed-2.1-pro. Effort variants (-low/-medium/-high/-xhigh) and `no-think/` aliases were not run; they share base weights with the models above.
- **Run-to-run on cap models:** cap/qwen3.8-27b r2 was served entirely from cache (median latency 0.96 s vs 27.8 s; identical text). cap/deepseek-v4-flash-0731 r2 was dropped to free cap capacity.
- **Dataset change during the run:** the local agent rebuilt contracts.json at 10:02 UTC (whitespace collapse) and changed `truncate()`. Prompts changed for 11 contracts (`api/v0_changed_ids.json`). Responses for those 11 obtained before the rebuild were moved to `raw/v0_purged/` and re-queried, so every reported number uses the v1 prompts.
- **Sandbox restart at about 10:44 UTC** killed all runners. They were relaunched resume-safe, and no data was lost.
- **laguna-s-2.1:free changed behaviour mid-session:** mean completion tokens were 27 in r1 (14:55–15:20) vs about 1000 in ws1/ws2 (16:00–16:20), suggesting the free backend switched to a reasoning configuration. Read its r1-vs-ws comparisons with care. ws1 vs ws2 were run at the same time.

## Limitations
- The router is closed and proprietary. Backends, versions, quantization and serving precision are **unknown**, and the "same model" across providers may not be the same weights or config (see the opus substitute pair).
- The router adds hidden prompt tokens: reported prompt tokens are about 590–700 on cap/agy against about 410–470 on clp/opencode for the same text, so a hidden system prompt may be shaping answers.
- The router's response cache means identical re-runs cannot measure nondeterminism. B′ uses a whitespace nonce, which mixes nondeterminism with prompt sensitivity.
- Safe contracts are only 32 (SWC *_fixed samples), so specificity estimates are coarse. Class accuracy uses the SmartBugs folder label (strict). The `all_classes` metadata never gave a different answer.
- Accuracy and F1 are computed on parsed items only. Parse failures (refusal or empty) are reported separately and are not counted as wrong.
- Some vulnerable SmartBugs contracts are well known and may be in the training data.

## Files (all in `api/`)
- `common.py`: prompt/truncation (identical to ../run_audit.py), `parse_verdict`, API client, resume-safe runner. `driver.py`: sequential multi-run driver. `clp_slow.py`: cooldown-aware single-worker runner. `probe.py`: endpoint probe. `analyze.py`: computes A/B/C. `make_summary_tables.py`: builds tables.md.
- `raw/*.jsonl`: one line per attempt: id, requested_model, returned_model, output, reasoning (if exposed), finish_reason, usage, latency_s, attempts, error, ts. Failed attempts are kept (error≠null); analysis uses the latest successful line per id. Naming: `<provider>_<model>__r1|r2|ws1|ws2.jsonl`. Superseded responses from before the dataset rebuild are not included; `v0_changed_ids.json` lists the contracts that changed in that rebuild.
- `results.json` (everything, including flip ids), `results_runs.csv` (per-run C metrics plus metadata), `results_churn.csv` (A/B pairs), `tables.md`.
- Runner logs are not included in the public release.
