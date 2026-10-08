"""Render markdown tables from results.json into tables.md (included by summary.md)."""
import json
d = json.load(open('results.json'))
L = []
L.append(f"Dataset: {d['n_total']} contracts ({d['n_vuln']} vulnerable SmartBugs-curated, {d['n_safe']} SWC *_fixed safe).\n")
def f(x): return '' if x is None else (f'{x:.3f}' if isinstance(x, float) else str(x))
for g, title in (('A', 'A. Cross-provider churn'), ('B', 'B. Run-to-run churn (temperature 0)')):
    L.append(f'### {title}\n')
    L.append('| pair | both covered | both parsed | parse-status flips | binary flips (rate) | class flips (rate) | raw text differs | McNemar b/c | exact p | binary flips by gold class |')
    L.append('|---|---|---|---|---|---|---|---|---|---|')
    for k, r in d[g].items():
        L.append(f"| {k} | {r['n_both_covered']} | {r['n_common_parsed']} | {r.get('parse_status_flips','')} | {r['binary_flips']} ({f(r['binary_flip_rate'])}) | {r['class_flips']} ({f(r['class_flip_rate'])}) | {r['raw_text_differs']} | {r['mcnemar_b_A_right_B_wrong']}/{r['mcnemar_c_A_wrong_B_right']} | {f(r['mcnemar_exact_p'])} | {json.dumps(r['binary_flips_by_gold_class'])} |")
    L.append('')
L.append('### C. Per-run accuracy (parsed items only; parse failures excluded from acc/F1 and reported separately)\n')
L.append('| run | coverage /175 | parsed | parse-fail rate | refusals | empty outputs | binary acc | precision | recall | F1 | safe specificity (TN/safe parsed) | class acc (vuln, strict) | median latency s | mean prompt tok | mean completion tok | returned model |')
L.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for k, v in d['runs'].items():
    m, me = v['metrics'], v['meta']
    L.append(f"| {k} | {me['coverage']} | {m.get('n_parsed')} | {f(m.get('parse_fail_rate'))} | {m.get('n_refusal')} | {m.get('n_empty_output')} | {f(m.get('binary_acc'))} | {f(m.get('precision'))} | {f(m.get('recall'))} | {f(m.get('f1'))} | {f(m.get('safe_specificity'))} | {f(m.get('class_acc_strict'))} | {f(me.get('median_latency_s'))} | {f(me.get('mean_prompt_tokens'))} | {f(me.get('mean_completion_tokens'))} | {', '.join(x for x in me['returned_models'] if x)} |")
open('tables.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
