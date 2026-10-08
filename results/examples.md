# Example verdict flips (reference = fp16)

Total 11-way verdict flips across all quantized runs: 220

## sb/access_control/rubixi.sol (qwen3-0.6b, fp16 -> q4_k_m, neg flip)
Ground truth: `access_control`. fp16: `access_control`; q4_k_m: `none`

- fp16 raw: `'<think>\n\n</think>\n\n```json\n{\n  "vulnerable": true,\n  "class": "access_control"\n}\n```'`
- q4_k_m raw: `'<think>\n\n{"vulnerable": false, "class": "none"}'`

## sb/bad_randomness/lucky_doubler.sol (llama-3.2-1b, fp16 -> q4_k_m, neg flip)
Ground truth: `bad_randomness`. fp16: `access_control`; q4_k_m: `none`

- fp16 raw: `'{"vulnerable": true, "class": "access_control"}'`
- q4_k_m raw: `'```\n{\n  "vulnerable": true,\n  "class": "access_control"\n}\n```\n\n```\n{\n  "vulnerable": false,\n  "class": "arithmetic"\n}\n```\n\n```\n{\n  "v'`

## sb/unchecked_low_level_calls/0x19cf8481ea15427a98ba3cdd6d9e14690011ab10.sol (llama-3.2-1b, fp16 -> q4_k_m, neg flip)
Ground truth: `unchecked_low_level_calls`. fp16: `denial_of_service`; q4_k_m: `none`

- fp16 raw: `'{"vulnerable": true, "class": "denial_of_service"}'`
- q4_k_m raw: `'```\n{\n  "vulnerable": true,\n  "class": "access_control"\n}\n```\n\n```\n{\n  "vulnerable": false,\n  "class": "arithmetic"\n}\n```\n\n```\n{\n  "v'`

## sb/arithmetic/timelock.sol (qwen3-0.6b, fp16 -> q4_k_m, neg flip)
Ground truth: `arithmetic`. fp16: `access_control`; q4_k_m: `none`

- fp16 raw: `'<think>\n\n</think>\n\n```json\n{\n  "vulnerable": true,\n  "class": "access_control"\n}\n```'`
- q4_k_m raw: `'<think>\n\n</think>\n\n```json\n{\n  "vulnerable": false,\n  "class": "none"\n}\n```'`

## sb/bad_randomness/old_blockhash.sol (qwen3-0.6b, fp16 -> q4_k_m, neg flip)
Ground truth: `bad_randomness`. fp16: `access_control`; q4_k_m: `none`

- fp16 raw: `'<think>\n\n</think>\n\n```json\n{\n  "vulnerable": true,\n  "class": "access_control"\n}\n```'`
- q4_k_m raw: `"<think>\nOkay, let's look at this Solidity smart contract. The user wants me to audit it for security vulnerabilities. The categories are access_control, arithmetic, bad_randomness, denial_of_service, front_running, reentrancy, short_addresses, time_manipulation, unchecked_low_level_calls, other.\n\nFirst"`

