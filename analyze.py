"""Compute churn metrics from raw/*.jsonl. Writes results/results.csv, results/per_class_flips.csv,
results/examples.md, results/metrics.json. Only reports computed values."""
import json, re, glob, os, math, csv
from collections import defaultdict, Counter
from scipy.stats import binomtest
CLASSES=["access_control","arithmetic","bad_randomness","denial_of_service","front_running",
         "reentrancy","short_addresses","time_manipulation","unchecked_low_level_calls","other","none"]
ALIAS={'unchecked_calls':'unchecked_low_level_calls','unchecked_low_level_call':'unchecked_low_level_calls',
       'time_dependence':'time_manipulation','dos':'denial_of_service','integer_overflow':'arithmetic'}
REF='fp16'
os.makedirs('results',exist_ok=True)
recs={r['id']:r for r in json.load(open('data/contracts.json'))}
def parse(txt):
    """returns (strict_ok, vuln or None, cls or None, cls_valid)"""
    if not txt: return False,None,None,False
    m=re.search(r'\{.*?\}',txt,re.S); obj=None; strict=False
    if m:
        try: obj=json.loads(m.group(0)); strict=isinstance(obj,dict) and isinstance(obj.get('vulnerable'),bool)
        except Exception: obj=None
    if strict: v=obj['vulnerable']; c=obj.get('class')
    else:   # lenient regex fallback
        mv=re.search(r'"?vulnerable"?\s*:\s*(true|false)',txt,re.I)
        if not mv: return False,None,None,False
        v=mv.group(1).lower()=='true'; mc=re.search(r'"?class"?\s*:\s*"([^"]*)"',txt); c=mc.group(1) if mc else None
    c=(c or '').strip().lower().replace(' ','_').replace('-','_'); c=ALIAS.get(c,c)
    valid=c in CLASSES
    return strict,v,(c if valid else None),valid
import sys; sys.path.insert(0,'api')
from common import parse_verdict   # shared parser with the API arm (read-only import of api/common.py)
def verdict(row):
    """Primary verdict = api/common.py:parse_verdict (identical to the API arm). Unparsed -> no detection ('none').
    parse() above is kept only for diagnostics (strict-JSON failures, raw inconsistency, invalid class strings)."""
    strict,v,c,valid=parse(row['output'])
    pv,pc,ok=parse_verdict(row['output'])
    vb=bool(pv) if ok else False
    cls=pc if ok else 'none'
    return dict(strict=strict,parsed=ok,cls_valid=valid,vuln=vb,cls=cls,raw_vuln=v,raw_cls=c)
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),)*2
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return ((c-h)/d,(c+h)/d)
def mcnemar(b,c): return 1.0 if b+c==0 else binomtest(b,b+c,0.5).pvalue
runs=defaultdict(dict)
for fn in sorted(glob.glob('raw/*.jsonl')):
    model,quant=os.path.basename(fn)[:-6].split('__')
    for l in open(fn):
        r=json.loads(l); runs[model][quant]={**runs[model].get(quant,{}),r['id']:r}
rows=[];pcrows=[];examples=[];M={}
for model,qs in runs.items():
    REF='fp16' if 'fp16' in qs else 'bf16'
    for quant,d in qs.items():
        ids=[i for i in recs if i in d]
        V={i:verdict(d[i]) for i in ids}
        y=[recs[i]['label'] for i in ids]; p=[int(V[i]['vuln']) for i in ids]
        tp=sum(a==1 and b==1 for a,b in zip(y,p)); fp=sum(a==0 and b==1 for a,b in zip(y,p))
        fn_=sum(a==1 and b==0 for a,b in zip(y,p)); tn=sum(a==0 and b==0 for a,b in zip(y,p))
        prec=tp/(tp+fp) if tp+fp else 0; rec=tp/(tp+fn_) if tp+fn_ else 0; f1=2*prec*rec/(prec+rec) if prec+rec else 0
        vids=[i for i in ids if recs[i]['label']==1]
        cls_acc_vuln=sum(V[i]['cls']==recs[i]['label_class'] for i in vids)/len(vids) if vids else float('nan')
        cls_acc_all=sum(V[i]['cls']==recs[i]['label_class'] for i in ids)/len(ids)
        row=dict(model=model,quant=quant,n=len(ids),
            parse_fail_rate=round(sum(not V[i]['parsed'] for i in ids)/len(ids),4),
            strict_json_fail_rate=round(sum(not V[i]['strict'] for i in ids)/len(ids),4),
            invalid_class_rate=round(sum(V[i]['parsed'] and not V[i]['cls_valid'] for i in ids)/len(ids),4),
            inconsistent_rate=round(sum(V[i]['parsed'] and ((V[i]['raw_vuln'] and V[i]['raw_cls']=='none') or (not V[i]['raw_vuln'] and V[i]['raw_cls'] not in (None,'none'))) for i in ids)/len(ids),4),
            truncated=sum(d[i]['truncated'] for i in ids),
            acc=round((tp+tn)/len(ids),4),precision=round(prec,4),recall=round(rec,4),f1=round(f1,4),
            specificity=round(tn/(tn+fp),4) if tn+fp else '',
            pred_vuln_rate=round(sum(p)/len(p),4),
            class_acc_on_vuln=round(cls_acc_vuln,4),class_acc_all_11way=round(cls_acc_all,4),
            mean_secs=round(sum(d[i]['secs'] for i in ids)/len(ids),2),total_secs=round(sum(d[i]['secs'] for i in ids),1))
        if quant!=REF and REF in qs:
            R={i:verdict(qs[REF][i]) for i in ids if i in qs[REF]}; cids=[i for i in ids if i in R]
            bflip=[i for i in cids if R[i]['vuln']!=V[i]['vuln']]
            neg=[i for i in bflip if R[i]['vuln']]; pos=[i for i in bflip if not R[i]['vuln']]
            neg_true=[i for i in neg if recs[i]['label']==1]
            cflip=[i for i in cids if R[i]['cls']!=V[i]['cls']]
            rawflip=[i for i in cids if (R[i]['raw_vuln'],R[i]['raw_cls'])!=(V[i]['raw_vuln'],V[i]['raw_cls'])]
            outdiff=[i for i in cids if qs[REF][i]['output']!=d[i]['output']]
            def corr(v,i): return int(v['vuln'])==recs[i]['label']
            def ccorr(v,i): return v['cls']==recs[i]['label_class']
            b=sum(corr(R[i],i) and not corr(V[i],i) for i in cids); c=sum(not corr(R[i],i) and corr(V[i],i) for i in cids)
            bc=sum(ccorr(R[i],i) and not ccorr(V[i],i) for i in cids); cc=sum(not ccorr(R[i],i) and ccorr(V[i],i) for i in cids)
            lo,hi=wilson(len(bflip),len(cids)); clo,chi=wilson(len(cflip),len(cids))
            row.update(n_paired=len(cids),binary_flips=len(bflip),binary_flip_rate=round(len(bflip)/len(cids),4),
                binary_flip_ci95=f'[{lo:.3f},{hi:.3f}]',neg_flips=len(neg),neg_flips_true_vuln=len(neg_true),pos_flips=len(pos),
                verdict_flips_11way=len(cflip),verdict_flip_rate_11way=round(len(cflip)/len(cids),4),verdict_flip_ci95=f'[{clo:.3f},{chi:.3f}]',
                raw_output_changed=len(outdiff),
                mcnemar_binary_b_c=f'{b}/{c}',mcnemar_binary_p=round(mcnemar(b,c),4),
                mcnemar_class_b_c=f'{bc}/{cc}',mcnemar_class_p=round(mcnemar(bc,cc),4),
                delta_acc=round(row['acc']-((sum(int(R[i]['vuln'])==recs[i]['label'] for i in cids))/len(cids)),4),
                delta_class_acc_11way=round(row['class_acc_all_11way']-sum(R[i]['cls']==recs[i]['label_class'] for i in cids)/len(cids),4))
            byc=defaultdict(list)
            for i in cids: byc[recs[i]['label_class']].append(i)
            for k in sorted(byc):
                L=byc[k]
                pcrows.append(dict(model=model,quant=quant,label_class=k,n=len(L),
                    binary_flips=sum(i in bflip for i in L),neg_flips=sum(i in neg for i in L),pos_flips=sum(i in pos for i in L),
                    verdict_flips_11way=sum(i in cflip for i in L),
                    ref_class_correct=sum(R[i]['cls']==k for i in L),quant_class_correct=sum(V[i]['cls']==k for i in L)))
            for i in cflip:
                examples.append(dict(model=model,quant=quant,id=i,label=recs[i]['label_class'],ref=R[i]['cls'],q=V[i]['cls'],
                    binary=('neg' if i in neg else 'pos' if i in pos else 'class-only'),ref_out=qs[REF][i]['output'],q_out=d[i]['output']))
        rows.append(row)
keys=[]; [keys.append(k) for r in rows for k in r if k not in keys]
with open('results/results.csv','w',newline='') as f:
    w=csv.DictWriter(f,keys); w.writeheader(); w.writerows(rows)
if pcrows:
    with open('results/per_class_flips.csv','w',newline='') as f:
        w=csv.DictWriter(f,list(pcrows[0])); w.writeheader(); w.writerows(pcrows)
# examples: prefer negative flips on truly vulnerable contracts, then class-only, then pos; diverse models
order={'neg':0,'class-only':1,'pos':2}
# prefer negative flips, then flips that destroyed a correct reference verdict; diversify by (model, quant, true class)
examples.sort(key=lambda e:(order[e['binary']],e['ref']!=e['label'],e['label']=='none'))
pick=[];seen=set();seen_mc=set()
for e in examples:
    k=(e['model'],e['quant'],e['label'])
    if e['id'] in seen or k in seen_mc: continue
    pick.append(e); seen.add(e['id']); seen_mc.add(k)
    if len(pick)>=5: break
with open('results/examples.md','w') as f:
    f.write(f'# Example verdict flips (reference = {REF})\n\nTotal 11-way verdict flips across all quantized runs: {len(examples)}\n\n')
    for e in pick:
        f.write(f"## {e['id']} ({e['model']}, {REF} -> {e['quant']}, {e['binary']} flip)\nGround truth: `{e['label']}`. "
                f"{REF}: `{e['ref']}`; {e['quant']}: `{e['q']}`\n\n- {REF} raw: `{e['ref_out']!r}`\n- {e['quant']} raw: `{e['q_out']!r}`\n\n")
json.dump(dict(rows=rows,per_class=pcrows,n_examples=len(examples)),open('results/metrics.json','w'),indent=1)
for r in rows: print({k:r[k] for k in r if k in('model','quant','n','parse_fail_rate','acc','f1','class_acc_all_11way','binary_flip_rate','neg_flips','pos_flips','verdict_flip_rate_11way','mcnemar_binary_p')})
