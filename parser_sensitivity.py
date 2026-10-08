"""Parser-policy sensitivity of binary flips: shared last-object parser (api/common.py:parse_verdict) vs a
first-object variant of the same parser. Also counts outputs containing >1 verdict object (format degradation).
Writes results/parser_sensitivity.txt. Regenerates the file that phase 1 wrote by hand-run code."""
import json, glob, os, re, sys
sys.path.insert(0, 'api')
import common
from common import parse_verdict

def parse_first(txt):
    if not txt: return None, None, False
    t = re.sub(r'<think>.*?</think>', '', txt, flags=re.S)
    cands = re.findall(r'\{[^{}]*"vulnerable"[^{}]*\}', t, flags=re.S)
    for c in cands:                     # FIRST parseable object instead of last
        try:
            o = json.loads(c); v = o.get('vulnerable')
            if isinstance(v, str): v = {'true': True, 'false': False}.get(v.strip().lower())
            if isinstance(v, bool):
                cl = common._norm_class(o.get('class')) if v else 'none'
                if v and cl == 'none': cl = 'other'
                return v, cl, True
        except Exception: pass
    return parse_verdict(txt)           # same regex fallback

def nobj(txt):
    if not txt: return 0
    t = re.sub(r'<think>.*?</think>', '', txt, flags=re.S)
    return len(re.findall(r'\{[^{}]*"vulnerable"[^{}]*\}', t, flags=re.S))

runs = {}
for fn in sorted(glob.glob('raw/*.jsonl')):
    model, quant = os.path.basename(fn)[:-6].split('__')
    runs.setdefault(model, {})[quant] = {json.loads(l)['id']: json.loads(l) for l in open(fn)}
L = []
for model in sorted(runs):
    for quant in sorted(runs[model]):
        d = runs[model][quant]
        L.append(f'{model}__{quant}: outputs with >1 verdict object: {sum(nobj(r["output"])>1 for r in d.values())}/{len(d)}')
for model in sorted(runs):
    qs = runs[model]
    if 'fp16' not in qs: continue
    R = qs['fp16']
    for quant in sorted(qs):
        if quant in ('fp16', 'fp16_rep'): continue
        d = qs[quant]; ids = [i for i in d if i in R]
        def vb(f, txt):
            v, c, ok = f(txt); return bool(v) if ok else False
        last = sum(vb(parse_verdict, R[i]['output']) != vb(parse_verdict, d[i]['output']) for i in ids)
        first = sum(vb(parse_first, R[i]['output']) != vb(parse_first, d[i]['output']) for i in ids)
        L.append(f'{model} fp16->{quant}: binary flips last-object(shared parser)={last}, first-object={first}, n={len(ids)}')
open('results/parser_sensitivity.txt', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
