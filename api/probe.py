import json,sys,time
from concurrent.futures import ThreadPoolExecutor
from common import *
recs=load_recs(); r=recs[0]
models=sys.argv[1:]
def p(m):
    msgs,_=messages(r['code'])
    try:
        d,lat=call(m,msgs,1024,timeout=120); ch=d['choices'][0]
        c=ch['message'].get('content'); return m,round(lat,1),d.get('model'),ch.get('finish_reason'),d.get('usage'),repr(c)[:150],parse_verdict(c)
    except Exception as e:
        b=''
        try: b=e.read().decode()[:200]
        except: pass
        return m,'ERR',repr(e)[:120],b
with ThreadPoolExecutor(12) as ex:
    for x in ex.map(p,models): print(x,flush=True)
