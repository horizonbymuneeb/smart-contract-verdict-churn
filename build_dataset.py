"""Build the evaluation set: SmartBugs-curated (vulnerable) + SWC-registry *_fixed.sol samples (labelled safe).
All comments are stripped (SmartBugs files carry '<yes> <report> CLASS' and '@vulnerable_at_lines' annotations
that would leak the label); blank lines collapsed."""
import json, re, os, glob, hashlib
SB='smartbugs-curated'; SWC='SWC-registry/entries/docs'
def strip_comments(src):
    out=[];i=0;n=len(src);st=None
    while i<n:
        c=src[i]
        if st is None:
            if src.startswith('//',i):
                j=src.find('\n',i); i=n if j<0 else j; continue
            if src.startswith('/*',i):
                j=src.find('*/',i+2); 
                seg=src[i:(n if j<0 else j+2)]; out.append('\n'*seg.count('\n')); i=n if j<0 else j+2; continue
            if c in '"\'': st=c
            out.append(c); i+=1
        else:
            out.append(c)
            if c=='\\' and i+1<n: out.append(src[i+1]); i+=2; continue
            if c==st: st=None
            i+=1
    s=''.join(out)
    # collapse long interior whitespace runs (honeypot contracts hide code far to the right)
    lines=[re.sub(r'(?<=\S)[ \t]{8,}',' ',l.rstrip()) for l in s.split('\n')]
    s='\n'.join(lines); s=re.sub(r'\n\s*\n+','\n\n',s).strip()+'\n'
    return s
recs=[]
vj=json.load(open(f'{SB}/vulnerabilities.json'))
for e in vj:
    src=open(f"{SB}/{e['path']}",encoding='utf-8',errors='replace').read()
    cats=sorted({v['category'] for v in e['vulnerabilities']})
    folder=e['path'].split('/')[1]
    recs.append(dict(id='sb/'+e['path'].split('dataset/')[1], source='smartbugs-curated', label=1,
        label_class=folder, all_classes=cats, code=strip_comments(src), raw_len=len(src)))
for md in sorted(glob.glob(f'{SWC}/SWC-*.md')):
    t=open(md).read(); swc=os.path.basename(md)[:-3]
    for m in re.finditer(r'^### (\S*fixed\S*\.sol)\s*\n+```solidity\n(.*?)```',t,re.S|re.M):
        recs.append(dict(id=f'swc/{swc}/{m.group(1)}', source='SWC-registry-fixed', label=0, label_class='none',
            all_classes=[], code=strip_comments(m.group(2)), raw_len=len(m.group(2))))
for r in recs: r['sha1']=hashlib.sha1(r['code'].encode()).hexdigest()[:12]
leak=[r['id'] for r in recs if re.search(r'<yes>|<report>|vulnerable_at',r['code'])]
print('records',len(recs),'vuln',sum(r['label'] for r in recs),'safe',sum(1-r['label'] for r in recs),'leak',leak)
from collections import Counter; print(Counter(r['label_class'] for r in recs))
print('multi-class vulnerable:',sum(len(r['all_classes'])>1 for r in recs))
json.dump(recs,open('data/contracts.json','w'),indent=1)
