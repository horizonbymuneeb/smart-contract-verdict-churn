"""Cooldown-aware single-worker runner for rate-limited clp :free models. Honors reset_seconds from 429 bodies.
Order is a fixed shuffle (seed 0) so partial coverage is not class-skewed.
usage: clp_slow.py DEADLINE_EPOCH model outfile"""
import sys, time, json, re, random, urllib.error
from common import *
deadline = float(sys.argv[1]); m = sys.argv[2]; out = 'raw/' + sys.argv[3]
recs = load_recs(); random.Random(0).shuffle(recs)
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def w(rec):
    with open(out, 'a') as f: f.write(json.dumps(rec) + '\n')
for r in recs:
    if r['id'] in load_results(out): continue
    msgs, tr = messages(r['code'])
    while time.time() < deadline:
        try:
            d, lat = call(m, msgs, 4096, timeout=240); ch = d['choices'][0]; msg = ch.get('message') or {}
            w(dict(id=r['id'], requested_model=m, truncated=tr, attempts=None, error=None, ts=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                   returned_model=d.get('model'), output=msg.get('content'), reasoning=msg.get('reasoning_content') or msg.get('reasoning'),
                   finish_reason=ch.get('finish_reason'), usage=d.get('usage'), latency_s=round(lat, 2), system_fingerprint=d.get('system_fingerprint')))
            log(f'ok {r["id"]} {lat:.1f}s'); break
        except urllib.error.HTTPError as e:
            b = e.read().decode()[:400]; mm = re.search(r'"reset_seconds":\s*(\d+)', b)
            wait = int(mm.group(1)) + 3 if mm else 30
            w(dict(id=r['id'], requested_model=m, error=f'HTTP {e.code}: {b[:200]}', ts=time.strftime('%Y-%m-%dT%H:%M:%S%z')))
            log(f'HTTP {e.code} wait {wait}'); time.sleep(min(wait, 300))
        except Exception as e:
            w(dict(id=r['id'], requested_model=m, error=repr(e)[:200], ts=time.strftime('%Y-%m-%dT%H:%M:%S%z')))
            log(repr(e)[:100]); time.sleep(20)
    if time.time() >= deadline: break
log(f'final coverage {len(load_results(out))}')
