"""Shared prompt/truncation (copied verbatim from ../run_audit.py as of 10:02 UTC rev, dataset v1 with whitespace collapse) + JSON-verdict parser + API runner.
NOTE: ../run_audit.py contains no parser (it only logs raw output); the parser here is defined for this arm
and is deterministic so the local arm can import it (api/common.py:parse_verdict) for comparability."""
import json, re, os, time, random, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

# Base URL of the OpenAI-compatible routing service used in the paper (a third-party commercial aggregator).
# It is not published here; set SCAUDIT_API_BASE (e.g. https://<host>/v1) and, if the service needs one,
# SCAUDIT_API_KEY before running the API arm.
BASE = os.environ.get("SCAUDIT_API_BASE", "").rstrip("/")
API_KEY = os.environ.get("SCAUDIT_API_KEY", "")
MAXCH = 4000
CLASSES = ["access_control","arithmetic","bad_randomness","denial_of_service","front_running",
           "reentrancy","short_addresses","time_manipulation","unchecked_low_level_calls","other","none"]
SYS = "You are a smart contract security auditor."
INSTR = ("Audit the Solidity smart contract below for security vulnerabilities.\n"
"Decide whether it is vulnerable and, if so, give the single most important vulnerability class, "
"chosen from the DASP categories: " + ", ".join(CLASSES[:-1]) + ". Use \"none\" if it is safe.\n"
"Respond with ONLY a JSON object and nothing else, in exactly this format:\n"
"{\"vulnerable\": true or false, \"class\": \"<one category or none>\"}\n\nContract:\n```solidity\n")

def truncate(code):
    if len(code) <= MAXCH: return code, False
    cut = code[:MAXCH]; j = cut.rfind('\n')
    cut = cut[:j+1] if j > MAXCH//2 else cut + '\n'
    return cut + "// ... [truncated]\n", True

# Cache-bust suffix: the router caches responses keyed on model+messages (identical calls return the same
# response id), so experiment B' appends a semantically-null whitespace suffix (env SCAUDIT_SUFFIX, JSON-escaped).
SUFFIX = json.loads(os.environ.get('SCAUDIT_SUFFIX', '""'))
def messages(code):
    c, tr = truncate(code)
    return [{"role":"system","content":SYS},{"role":"user","content":INSTR+c+"```"+SUFFIX}], tr

def load_recs():
    return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'contracts.json')))

def _norm_class(c):
    if c is None: return None
    c = str(c).strip().lower().replace('-', '_').replace(' ', '_')
    alias = {'unchecked_calls':'unchecked_low_level_calls','unchecked_low_level_call':'unchecked_low_level_calls',
             'integer_overflow':'arithmetic','overflow':'arithmetic','dos':'denial_of_service',
             'timestamp_dependence':'time_manipulation','randomness':'bad_randomness','safe':'none'}
    c = alias.get(c, c)
    return c if c in CLASSES else 'other'

def parse_verdict(txt):
    """Returns (vulnerable: bool|None, cls: str|None, ok: bool). ok=False => parse failure.
    Rules: drop <think>...</think>; take the LAST {...} object containing "vulnerable" that json-loads
    (falls back to regex on the key); bool or 'true'/'false' strings accepted. If vulnerable is false, class='none'."""
    if not txt: return None, None, False
    t = re.sub(r'<think>.*?</think>', '', txt, flags=re.S)
    cands = re.findall(r'\{[^{}]*"vulnerable"[^{}]*\}', t, flags=re.S)
    for c in reversed(cands):
        try:
            o = json.loads(c)
            v = o.get('vulnerable')
            if isinstance(v, str): v = {'true':True,'false':False}.get(v.strip().lower())
            if isinstance(v, bool):
                cl = _norm_class(o.get('class')) if v else 'none'
                if v and cl == 'none': cl = 'other'
                return v, cl, True
        except Exception: pass
    m = re.search(r'"vulnerable"\s*:\s*(true|false)', t, flags=re.I)
    if m:
        v = m.group(1).lower() == 'true'
        mc = re.search(r'"class"\s*:\s*"([^"]*)"', t)
        cl = (_norm_class(mc.group(1)) if mc else 'other') if v else 'none'
        if v and cl == 'none': cl = 'other'
        return v, cl, True
    return None, None, False

def call(model, msgs, max_tokens=1024, timeout=180):
    body = json.dumps({"model":model,"messages":msgs,"temperature":0,"max_tokens":max_tokens}).encode()
    req = urllib.request.Request(BASE+"/chat/completions", data=body, headers={"Content-Type":"application/json", **({"Authorization": "Bearer " + API_KEY} if API_KEY else {})})
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    return d, time.time()-t

def run(model, outpath, recs, max_tokens=1024, workers=4, max_attempts=6, log=print):
    done = set()
    if os.path.exists(outpath):
        for l in open(outpath):
            try:
                o = json.loads(l)
                if o.get('error') is None: done.add(o['id'])
            except Exception: pass
    todo = [r for r in recs if r['id'] not in done]
    log(f"{model} -> {outpath}: {len(done)} done, {len(todo)} todo")
    lock = threading.Lock()
    def one(r):
        msgs, tr = messages(r['code'])
        err = None; d = None; lat = None; attempts = 0
        for a in range(max_attempts):
            attempts = a+1
            try:
                d, lat = call(model, msgs, max_tokens)
                if 'choices' not in d or not d['choices']:
                    raise RuntimeError('no choices: '+json.dumps(d)[:300])
                err = None; break
            except urllib.error.HTTPError as e:
                try: b = e.read().decode()[:300]
                except Exception: b = ''
                err = f"HTTP {e.code}: {b}"
            except Exception as e:
                err = repr(e)[:300]
            time.sleep(min(60, 3*2**a) + random.random()*2)
        rec = dict(id=r['id'], requested_model=model, truncated=tr, attempts=attempts, error=err,
                   ts=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
        if err is None:
            ch = d['choices'][0]; msg = ch.get('message') or {}
            rec.update(returned_model=d.get('model'), output=msg.get('content'),
                       reasoning=(msg.get('reasoning_content') or msg.get('reasoning')),
                       finish_reason=ch.get('finish_reason'), usage=d.get('usage'), latency_s=round(lat,2),
                       system_fingerprint=d.get('system_fingerprint'))
        with lock:
            with open(outpath, 'a') as f: f.write(json.dumps(rec)+'\n')
        return err is None
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(one, todo))
    log(f"{model}: ok {sum(res)}/{len(res)} this pass")
    return sum(res), len(res)

def load_results(path):
    """latest successful record per id"""
    out = {}
    if not os.path.exists(path): return out
    for l in open(path):
        try: o = json.loads(l)
        except Exception: continue  # partial line from a killed process
        if o.get('error') is None: out[o['id']] = o
    return out
