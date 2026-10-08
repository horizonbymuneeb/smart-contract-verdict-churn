"""Compute A (cross-provider churn), B (run-to-run churn), C (accuracy baselines) from raw/*.jsonl."""
import json, glob, os, csv, math, collections, re
from common import load_recs, load_results, parse_verdict, CLASSES

recs = load_recs(); gold = {r['id']: r for r in recs}; N = len(recs)

def verdicts(path):
    res = load_results(path); out = {}
    for i, o in res.items():
        v, c, ok = parse_verdict(o.get('output'))
        out[i] = dict(v=v, c=c, ok=ok, rec=o)
    return out

def mcnemar_exact(b, c):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)

def run_meta(path):
    res = load_results(path)
    allrecs = [json.loads(l) for l in open(path)] if os.path.exists(path) else []
    lat = sorted(o['latency_s'] for o in res.values() if o.get('latency_s') is not None)
    pt = [o['usage']['prompt_tokens'] for o in res.values() if o.get('usage') and o['usage'].get('prompt_tokens')]
    ct = [o['usage']['completion_tokens'] for o in res.values() if o.get('usage') and o['usage'].get('completion_tokens')]
    rm = collections.Counter(o.get('returned_model') for o in res.values())
    fr = collections.Counter(o.get('finish_reason') for o in res.values())
    return dict(coverage=len(res), failed_attempt_records=sum(1 for o in allrecs if o.get('error')),
                returned_models=dict(rm), finish=dict(fr),
                median_latency_s=lat[len(lat)//2] if lat else None,
                mean_prompt_tokens=round(sum(pt)/len(pt), 1) if pt else None,
                mean_completion_tokens=round(sum(ct)/len(ct), 1) if ct else None)

def acc_metrics(V):
    ids = [i for i in gold]  # parse failures and missing count as wrong for 'strict', excluded for 'parsed'
    cov = [i for i in ids if i in V]
    parsed = [i for i in cov if V[i]['ok']]
    tp = sum(1 for i in parsed if V[i]['v'] and gold[i]['label'] == 1)
    fp = sum(1 for i in parsed if V[i]['v'] and gold[i]['label'] == 0)
    fn = sum(1 for i in parsed if not V[i]['v'] and gold[i]['label'] == 1)
    tn = sum(1 for i in parsed if not V[i]['v'] and gold[i]['label'] == 0)
    prec = tp/(tp+fp) if tp+fp else float('nan'); rec = tp/(tp+fn) if tp+fn else float('nan')
    f1 = 2*prec*rec/(prec+rec) if prec+rec else float('nan')
    # class accuracy on vulnerable contracts: predicted class == folder label (strict) or in all_classes (lenient)
    vul = [i for i in parsed if gold[i]['label'] == 1]
    cls_strict = sum(1 for i in vul if V[i]['c'] == gold[i]['label_class'])
    cls_len = sum(1 for i in vul if V[i]['c'] in set(gold[i]['all_classes']) | {gold[i]['label_class']})
    safe = [i for i in parsed if gold[i]['label'] == 0]
    refusals = sum(1 for i in cov if not V[i]['ok'] and re.match(r'\s*(sorry|i cannot|i can.t|i.m sorry)', (V[i]['rec'].get('output') or ''), re.I))
    empty = sum(1 for i in cov if not V[i]['ok'] and not (V[i]['rec'].get('output') or '').strip())
    return dict(n_covered=len(cov), n_parsed=len(parsed), n_refusal=refusals, n_empty_output=empty,
                parse_fail_rate=round(1-len(parsed)/len(cov), 4) if cov else None,
                binary_acc=round((tp+tn)/len(parsed), 4) if parsed else None,
                precision=round(prec, 4), recall=round(rec, 4), f1=round(f1, 4),
                tp=tp, fp=fp, fn=fn, tn=tn,
                safe_specificity=round(tn/len(safe), 4) if safe else None,
                class_acc_strict=round(cls_strict/len(vul), 4) if vul else None,
                class_acc_lenient=round(cls_len/len(vul), 4) if vul else None,
                n_vuln_parsed=len(vul))

def compare(Va, Vb):
    common = [i for i in gold if i in Va and i in Vb and Va[i]['ok'] and Vb[i]['ok']]
    bflip = [i for i in common if Va[i]['v'] != Vb[i]['v']]
    cflip = [i for i in common if Va[i]['c'] != Vb[i]['c']]
    # McNemar on binary correctness
    corr = lambda V, i: V[i]['v'] == bool(gold[i]['label'])
    b = sum(1 for i in common if corr(Va, i) and not corr(Vb, i))
    c = sum(1 for i in common if not corr(Va, i) and corr(Vb, i))
    raw_diff = sum(1 for i in gold if i in Va and i in Vb and (Va[i]['rec'].get('output') or '').strip() != (Vb[i]['rec'].get('output') or '').strip())
    both_cov = sum(1 for i in gold if i in Va and i in Vb)
    perclass = collections.Counter(gold[i]['label_class'] for i in bflip)
    perclass_c = collections.Counter(gold[i]['label_class'] for i in cflip)
    bc = [i for i in gold if i in Va and i in Vb]
    pstat = sum(1 for i in bc if Va[i]['ok'] != Vb[i]['ok'])
    return dict(n_common_parsed=len(common), n_both_covered=both_cov, parse_status_flips=pstat,
                binary_flips=len(bflip), binary_flip_rate=round(len(bflip)/len(common), 4) if common else None,
                binary_agreement=round(1-len(bflip)/len(common), 4) if common else None,
                class_flips=len(cflip), class_flip_rate=round(len(cflip)/len(common), 4) if common else None,
                raw_text_differs=raw_diff,
                mcnemar_b_A_right_B_wrong=b, mcnemar_c_A_wrong_B_right=c, mcnemar_exact_p=round(mcnemar_exact(b, c), 4),
                binary_flips_by_gold_class=dict(perclass), class_flips_by_gold_class=dict(perclass_c),
                binary_flip_ids=bflip)

import glob as _g
RUNS = {}
for p in sorted(_g.glob('raw/*.jsonl')):
    if not load_results(p): continue
    RUNS[os.path.basename(p)[:-6]] = p
V = {k: verdicts(p) for k, p in RUNS.items()}
meta = {k: run_meta(p) for k, p in RUNS.items()}
out = dict(n_total=N, n_vuln=sum(r['label'] for r in recs), n_safe=sum(1-r['label'] for r in recs), runs={}, A={}, B={})
rows = []
for k in RUNS:
    m = acc_metrics(V[k]) if V[k] else {}
    out['runs'][k] = dict(meta=meta[k], metrics=m)
    rows.append(dict(run=k, **{kk: vv for kk, vv in meta[k].items() if kk not in ('returned_models', 'finish')},
                     returned_models=json.dumps(meta[k]['returned_models']), finish=json.dumps(meta[k]['finish']), **m))
pairs_A = {'qwen3.8-27b: cap vs clp:free': ('cap_qwen3.8-27b__r1', 'clp_qwen3.8-27b-free__r1'),
           'deepseek-v4.1-flash: opencode-go vs clp cline-free': ('opencode-go_deepseek-v4.1-flash__r1', 'clp_cline-free_deepseek-v4.1-flash__r1'),
           'SUBSTITUTE claude-opus-4.6: cap vs agy (agy id says -thinking)': ('cap_claude-opus-4.6__r1', 'agy_claude-opus-4-6-thinking__r1')}
pairs_B = {'CACHED agy/claude-sonnet-4-6 r1 vs r2': ('agy_claude-sonnet-4-6__r1', 'agy_claude-sonnet-4-6__r2'),
           'CACHED agy/claude-opus-4-6-thinking r1 vs r2': ('agy_claude-opus-4-6-thinking__r1', 'agy_claude-opus-4-6-thinking__r2'),
           'CACHED opencode-go/deepseek-v4.1-flash r1 vs r2': ('opencode-go_deepseek-v4.1-flash__r1', 'opencode-go_deepseek-v4.1-flash__r2'),
           'cap/qwen3.8-27b r1 vs r2': ('cap_qwen3.8-27b__r1', 'cap_qwen3.8-27b__r2'),
           'cap/deepseek-v4-flash-0731 r1 vs r2': ('cap_deepseek-v4-flash-0731__r1', 'cap_deepseek-v4-flash-0731__r2')}
for m in ['agy_claude-sonnet-4-6', 'agy_claude-opus-4-6-thinking', 'opencode-go_deepseek-v4.1-flash', 'clp_laguna-s-2.1-free']:
    pairs_B[f"WS {m} ws1 vs ws2 (both uncached)"] = (f'{m}__ws1', f'{m}__ws2')
    pairs_B[f"WS {m} r1 vs ws1"] = (f'{m}__r1', f'{m}__ws1')
    pairs_B[f"WS {m} r1 vs ws2"] = (f'{m}__r1', f'{m}__ws2')
crow = []
for grp, pairs in (('A', pairs_A), ('B', pairs_B)):
    for name, (a, b) in pairs.items():
        r = compare(V.get(a, {}), V.get(b, {})); out[grp][name] = r
        crow.append(dict(experiment=grp, pair=name, **{k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items() if k != 'binary_flip_ids'}))
json.dump(out, open('results.json', 'w'), indent=1)
with open('results_runs.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}, key=lambda x: (x != 'run', x))); w.writeheader(); w.writerows(rows)
with open('results_churn.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(crow[0].keys())); w.writeheader(); w.writerows(crow)
for k, v in out['runs'].items(): print(k, v['meta']['coverage'], v['metrics'])
for g in ('A', 'B'):
    for k, v in out[g].items(): print(g, k, {kk: vv for kk, vv in v.items() if kk != 'binary_flip_ids'})
