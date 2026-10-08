"""Generate LaTeX tables for the manuscript directly from the computed result files.
Run from the repository root:  python paper/make_paper_tables.py
Inputs : data/contracts.json, results/results.csv, results/per_class_flips.csv,
         api/results_runs.csv, api/results_churn.csv
Outputs: paper/tab_*.tex, paper/numbers.json (every number quoted in the text)"""
import json, collections, math
import pandas as pd

OUT = 'paper/'
MODEL = {'qwen2.5-coder-0.5b': 'Qwen2.5-Coder-0.5B', 'llama-3.2-1b': 'Llama-3.2-1B', 'qwen3-0.6b': 'Qwen3-0.6B'}
QUANT = {'fp16': 'F16', 'fp16_rep': 'F16 (repeat)', 'q8_0': 'Q8\\_0', 'q4_k_m': 'Q4\\_K\\_M'}
MORDER = ['qwen2.5-coder-0.5b', 'llama-3.2-1b', 'qwen3-0.6b']
QORDER = ['fp16', 'fp16_rep', 'q8_0', 'q4_k_m']
CLS = ['unchecked_low_level_calls', 'none', 'reentrancy', 'access_control', 'arithmetic', 'bad_randomness',
       'denial_of_service', 'time_manipulation', 'front_running', 'other', 'short_addresses']
def tt(s): return s.replace('_', '\\_')
def f3(x): return '--' if pd.isna(x) or x == '' else f'{float(x):.3f}'
def pct(k, n): return f'{100*k/n:.1f}'
def pfmt(p):
    p = float(p)
    return '$<$0.001' if p < 0.001 else f'{p:.3f}'

N = {}
# ---------- dataset ----------
recs = json.load(open('data/contracts.json'))
cnt = collections.Counter(r['label_class'] for r in recs)
N['n_total'] = len(recs); N['n_vuln'] = sum(r['label'] for r in recs); N['n_safe'] = N['n_total'] - N['n_vuln']
N['class_counts'] = dict(cnt)
L = ['\\begin{table}[t]\\centering\\small', '\\caption{Evaluation set (175 contracts). Vulnerable contracts carry their SmartBugs-curated DASP folder label; safe contracts are the SWC Registry \\texttt{*\\_fixed} samples, labelled \\texttt{none}.}\\label{tab:data}',
     '\\begin{tabular}{lrl}\\toprule', 'Label & $n$ & Source\\\\\\midrule']
for c in CLS:
    L.append(f'\\texttt{{{tt(c)}}} & {cnt[c]} & {"SWC Registry (fixed)" if c=="none" else "SmartBugs-curated"}\\\\')
L += ['\\midrule', f'Total & {len(recs)} & {N["n_vuln"]} vulnerable, {N["n_safe"]} safe\\\\', '\\bottomrule\\end{tabular}\\end{table}']
open(OUT + 'tab_data.tex', 'w').write('\n'.join(L) + '\n')
def fit(L):
    t='\n'.join(L)
    return t.replace('\\begin{tabular}','\\resizebox{\\textwidth}{!}{\\begin{tabular}').replace('\\end{tabular}','\\end{tabular}}')+'\n'

# ---------- local aggregate ----------
r = pd.read_csv('results/results.csv')
r['mo'] = r.model.map(MORDER.index); r['qo'] = r.quant.map(QORDER.index)
r = r.sort_values(['mo', 'qo'])
N['local'] = r.drop(columns=['mo', 'qo']).to_dict(orient='records')
L = ['\\begin{table*}[t]\\centering\\small',
     '\\caption{Local models: aggregate metrics on the 175 contracts (positive class = vulnerable). ``Self-contr.\'\' is the share of outputs whose first JSON object states \\texttt{vulnerable: true} with class \\texttt{none}; ``Multi-obj.\'\' counts outputs containing more than one verdict object. Class accuracy is exact-match on the 11-way label (10 DASP classes + \\texttt{none}).}\\label{tab:local_agg}',
     '\\begin{tabular}{llrrrrrrrrr}\\toprule',
     'Model & Quant. & Parse fail & Self-contr. & Multi-obj. & Acc. & F1 & Recall & Spec. & Class acc. (vuln.) & 11-way acc.\\\\\\midrule']
ps = {}
for line in open('results/parser_sensitivity.txt'):
    if '>1 verdict object' in line:
        k, v = line.split(': outputs with >1 verdict object: '); ps[k] = v.strip().split('/')[0]
for _, x in r.iterrows():
    L.append(f'{MODEL[x.model]} & {QUANT[x.quant]} & {f3(x.parse_fail_rate)} & {f3(x.inconsistent_rate)} & {ps.get(x.model+"__"+x.quant,"--")} & {f3(x.acc)} & {f3(x.f1)} & {f3(x.recall)} & {f3(x.specificity)} & {f3(x.class_acc_on_vuln)} & {f3(x.class_acc_all_11way)}\\\\')
L += ['\\bottomrule\\end{tabular}\\end{table*}']
open(OUT + 'tab_local_agg.tex', 'w').write(fit(L))

# ---------- local churn ----------
q = r[r.binary_flips.notna()]
L = ['\\begin{table*}[t]\\centering\\small',
     '\\caption{Local models: churn against the same model at F16 ($n=175$ paired contracts). Binary flips change the vulnerable/safe verdict; 11-way flips change the stated label. Neg./pos.\\ = vulnerable$\\to$safe / safe$\\to$vulnerable. McNemar $b/c$ = reference correct \\& quantized wrong / the reverse; exact two-sided binomial $p$. Intervals are 95\\% Wilson. ``Text changed\'\' counts byte-level differences in the raw output.}\\label{tab:local_churn}',
     '\\begin{tabular}{llrrrrrrrrrr}\\toprule',
     ' & & \\multicolumn{4}{c}{Binary verdict} & \\multicolumn{4}{c}{11-way verdict} & & \\\\\\cmidrule(lr){3-6}\\cmidrule(lr){7-10}',
     'Model & Quant. & Flips (95\\% CI) & Neg./pos. & $b/c$, $p$ & $\\Delta$Acc. & Flips & Rate (95\\% CI) & McNemar $b/c$ & $p$ & $\\Delta$11-way acc. & Text changed\\\\\\midrule']
for _, x in q.iterrows():
    L.append(f'{MODEL[x.model]} & {QUANT[x.quant]} & {int(x.binary_flips)} {x.binary_flip_ci95} & {int(x.neg_flips)}/{int(x.pos_flips)} & {x.mcnemar_binary_b_c}, {pfmt(x.mcnemar_binary_p)} & {x.delta_acc:+.3f} & {int(x.verdict_flips_11way)} & {x.verdict_flip_rate_11way:.3f} {x.verdict_flip_ci95} & {x.mcnemar_class_b_c} & {pfmt(x.mcnemar_class_p)} & {x.delta_class_acc_11way:+.3f} & {int(x.raw_output_changed)}\\\\')
L += ['\\bottomrule\\end{tabular}\\end{table*}']
open(OUT + 'tab_local_churn.tex', 'w').write(fit(L).replace('+0.000', '0.000').replace('-0.000', '0.000'))

# ---------- per-class flips ----------
p = pd.read_csv('results/per_class_flips.csv')
p = p[p.quant != 'fp16_rep']
cols = [(m, qq) for m in MORDER for qq in QORDER if ((p.model == m) & (p.quant == qq)).any()]
N['per_class'] = p.to_dict(orient='records')
hdr = ' & '.join(f'{MODEL[m].split("-")[0] if False else MODEL[m]} {QUANT[qq]}' for m, qq in cols)
L = ['\\begin{table*}[t]\\centering\\small',
     '\\caption{11-way verdict flips by ground-truth label (flipped / $n$), each quantized model against its own F16 reference.}\\label{tab:perclass}',
     '\\begin{tabular}{lr' + 'r' * len(cols) + '}\\toprule',
     'True label & $n$ & ' + ' & '.join(f'\\shortstack{{{MODEL[m]}\\\\{QUANT[qq]}}}' for m, qq in cols) + '\\\\\\midrule']
for c in CLS:
    row = [f'\\texttt{{{tt(c)}}}', str(cnt[c])]
    for m, qq in cols:
        s = p[(p.model == m) & (p.quant == qq) & (p.label_class == c)]
        if len(s): v = int(s.verdict_flips_11way.iloc[0]); ng = int(s.neg_flips.iloc[0]); row.append(f'{v}' + (f' ({ng} neg.)' if ng else ''))
        else: row.append('--')
    L.append(' & '.join(row) + '\\\\')
L += ['\\bottomrule\\end{tabular}\\end{table*}']
open(OUT + 'tab_perclass.tex', 'w').write(fit(L))

# ---------- API baselines ----------
a = pd.read_csv('api/results_runs.csv')
a1 = a[a.run.str.endswith('__r1')].copy()
a1['ep'] = a1.run.str[:-4]
N['api_endpoints_r1'] = len(a1)
N['api_endpoints_ge65_parsed'] = int((a1.n_parsed >= 65).sum())
N['api_full_coverage_r1'] = int((a1.coverage == 175).sum())
main = a1[a1.n_parsed >= 65]
N['api_recall_range'] = [float(main.recall.min()), float(main.recall.max())]
N['api_spec_range'] = [float(main.safe_specificity.min()), float(main.safe_specificity.max())]
N['api_runs'] = a1.to_dict(orient='records')
L = ['\\begin{table*}[t]\\centering\\scriptsize',
     '\\caption{External API arm: first run (\\texttt{r1}) of each endpoint, temperature 0. Metrics are computed on parsed responses only; refusals and empty outputs are counted as parse failures and reported separately. Specificity is over the parsed safe contracts. Endpoint names are the router\'s provider prefix and model identifier, as returned; backends, weights and serving precision are not disclosed by the router. $^\\dagger$Only 20 responses, excluded from summary ranges.}\\label{tab:api}',
     '\\begin{tabular}{lrrrrrrrrr}\\toprule',
     'Endpoint & Covered & Parsed & Refusals & Empty & Acc. & F1 & Recall & Spec. & Class acc. (vuln.)\\\\\\midrule']
for _, x in a1.sort_values('ep').iterrows():
    nm = '\\texttt{' + tt(x.ep.replace('_', '/', 1)) + '}' + ('$^\\dagger$' if x.n_parsed < 65 else '')
    L.append(f'{nm} & {int(x.coverage)} & {int(x.n_parsed)} & {int(x.n_refusal)} & {int(x.n_empty_output)} & {f3(x.binary_acc)} & {f3(x.f1)} & {f3(x.recall)} & {f3(x.safe_specificity)} & {f3(x.class_acc_strict)}\\\\')
L += ['\\bottomrule\\end{tabular}\\end{table*}']
open(OUT + 'tab_api.tex', 'w').write(fit(L))

# ---------- API churn ----------
c = pd.read_csv('api/results_churn.csv')
N['api_churn'] = c.to_dict(orient='records')
def lab(s):
    s = s.replace('SUBSTITUTE ', '').replace(' (agy id says -thinking)', '').replace(' (both uncached)', '')
    s = s.replace('CACHED ', '').replace('WS ', '')
    return tt(s.replace('agy_', 'agy/').replace('opencode-go_', 'opencode-go/').replace('clp_', 'clp/'))
L = ['\\begin{table*}[t]\\centering\\scriptsize',
     '\\caption{External API arm: paired churn. (A) Same model name served by two providers. (B$_\\mathrm{cache}$) Identical repeated request; the router returned cached responses, so these zeros carry no information about determinism. (B$_\\mathrm{ws}$) Two uncached runs whose prompts differ by one trailing whitespace character (\\texttt{ws1} = ``\\textbackslash n\'\', \\texttt{ws2} = `` \\textbackslash n\'\'); an upper bound on run-to-run churn. Flips are counted on contracts parsed in both runs; parse-status flips are contracts parsed in one run only. McNemar $b/c$ = first run correct \\& second wrong / the reverse.}\\label{tab:api_churn}',
     '\\begin{tabular}{llrrrrrrr}\\toprule',
     'Type & Pair & Both parsed & Parse-status flips & Binary flips (\\%) & 11-way flips (\\%) & Text differs & $b/c$ & $p$\\\\\\midrule']
sel = []
for _, x in c.iterrows():
    if x.n_common_parsed == 0: continue
    if x.experiment == 'A': t = 'A'
    elif x.pair.startswith('CACHED') or x.pair.startswith('cap/qwen3.8-27b r1 vs r2'): t = 'B$_\\mathrm{cache}$'
    elif 'ws1 vs ws2' in x.pair: t = 'B$_\\mathrm{ws}$'
    else: continue                                    # r1-vs-ws comparisons mix cache/time effects; kept in the CSV only
    n = int(x.n_common_parsed)
    L.append(f'{t} & {lab(x.pair)} & {n} & {int(x.parse_status_flips)} & {int(x.binary_flips)} ({pct(x.binary_flips,n)}) & {int(x.class_flips)} ({pct(x.class_flips,n)}) & {int(x.raw_text_differs)} & {int(x.mcnemar_b_A_right_B_wrong)}/{int(x.mcnemar_c_A_wrong_B_right)} & {pfmt(x.mcnemar_exact_p)}\\\\')
L += ['\\bottomrule\\end{tabular}\\end{table*}']
open(OUT + 'tab_api_churn.tex', 'w').write(fit(L))
json.dump(N, open(OUT + 'numbers.json', 'w'), indent=1, default=str)
print('tables written;', N['api_endpoints_r1'], 'endpoints r1,', N['api_endpoints_ge65_parsed'], '>=65 parsed,', N['api_full_coverage_r1'], 'full coverage')
print('recall range', N['api_recall_range'], 'spec range', N['api_spec_range'])

# ---------- model hashes ----------
H = {}
for line in open('model_sha256.txt'):
    if line.startswith('#') or not line.strip(): continue
    h, fn = line.split(); H[fn.split('/')[-1]] = h
L = ['\\begin{table}[h]\\centering\\scriptsize',
     '\\caption{GGUF files used in the local arm (SHA-256). Sources: \\texttt{Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF} (official), \\texttt{bartowski/Llama-3.2-1B-Instruct-GGUF} (community, imatrix-calibrated quants), \\texttt{ggml-org/Qwen3-0.6B-GGUF} (F16; Q8\\_0 and Q4\\_K\\_M quantized locally with \\texttt{llama\\_model\\_quantize}, no imatrix). The hash of \\texttt{qwen2.5-coder-0.5b-instruct-q8\\_0.gguf} was not recorded before the file was deleted.}\\label{tab:hashes}',
     '\\begin{tabular}{ll}\\toprule File & SHA-256\\\\\\midrule']
for fn in sorted(H, key=str.lower):
    L.append(f'\\texttt{{{tt(fn)}}} & \\texttt{{{H[fn]}}}\\\\')
L.append('\\texttt{qwen2.5-coder-0.5b-instruct-q8\\_0.gguf} & not recorded\\\\')
L += ['\\bottomrule\\end{tabular}\\end{table}']
open(OUT + 'tab_hashes.tex', 'w').write(fit(L))
