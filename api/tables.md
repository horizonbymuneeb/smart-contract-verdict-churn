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
