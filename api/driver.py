"""usage: driver.py DEADLINE_EPOCH WORKERS model:outfile [model:outfile ...]  (runs sequentially; repeats passes until complete or deadline)"""
import sys,time,os
from common import *
deadline=float(sys.argv[1]); W=int(sys.argv[2])
recs=load_recs()
def log(s): print(time.strftime('%H:%M:%S'),s,flush=True)
for spec in sys.argv[3:]:
    m,out=spec.rsplit(':',1)
    out='raw/'+out
    p=0
    while time.time()<deadline:
        p+=1
        ok,n=run(m,out,recs,max_tokens=4096,workers=W,max_attempts=8,log=log)
        if n==0 or ok==n: break
        if ok==0 and p>=3 and len(load_results(out))==0: log(f'{m}: giving up, nothing succeeded'); break
        time.sleep(30)
    log(f'{m}: final coverage {len(load_results(out))}/{len(recs)}')
