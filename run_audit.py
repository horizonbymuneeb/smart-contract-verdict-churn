"""Run one GGUF model over the contract set. Resume-safe (skips ids already in the output jsonl).
usage: run_audit.py MODEL_TAG QUANT GGUF_PATH [limit]"""
import json, sys, time, os, hashlib
from llama_cpp import Llama
tag, quant, path = sys.argv[1:4]; limit=int(sys.argv[4]) if len(sys.argv)>4 else None
MAXCH=4000; SEED=1234
CLASSES=["access_control","arithmetic","bad_randomness","denial_of_service","front_running",
         "reentrancy","short_addresses","time_manipulation","unchecked_low_level_calls","other","none"]
SYS="You are a smart contract security auditor."
INSTR=("Audit the Solidity smart contract below for security vulnerabilities.\n"
"Decide whether it is vulnerable and, if so, give the single most important vulnerability class, "
"chosen from the DASP categories: " + ", ".join(CLASSES[:-1]) + ". Use \"none\" if it is safe.\n"
"Respond with ONLY a JSON object and nothing else, in exactly this format:\n"
"{\"vulnerable\": true or false, \"class\": \"<one category or none>\"}\n\nContract:\n```solidity\n")
def truncate(code):
    if len(code)<=MAXCH: return code, False
    cut=code[:MAXCH]; j=cut.rfind('\n')
    if j>MAXCH//2: cut=cut[:j+1]
    else: cut=cut+'\n'
    return cut+"// ... [truncated]\n", True
recs=json.load(open('data/contracts.json'))
if limit: recs=recs[:limit] if limit>0 else recs
out=f'raw/{tag}__{quant}.jsonl'; os.makedirs('raw',exist_ok=True)
done=set()
if os.path.exists(out):
    for l in open(out):
        try: done.add(json.loads(l)['id'])
        except Exception: pass
todo=[r for r in recs if r['id'] not in done]
if os.environ.get('REVERSE')=='1': todo=todo[::-1]   # noise-floor repeat: different order => different KV-prefix reuse pattern
print(f'{tag} {quant}: {len(done)} done, {len(todo)} to do',flush=True)
if not todo: sys.exit()
t0=time.time()
llm=Llama(path,n_ctx=4096,n_threads=2,n_batch=512,seed=SEED,verbose=False)
print('load s',round(time.time()-t0,1),flush=True)
f=open(out,'a')
for k,r in enumerate(todo):
    code,trunc=truncate(r['code'])
    user=INSTR+code+"```"
    if tag.lower().startswith('qwen3'): user+="\n/no_think"   # Qwen3: disable thinking mode (official soft switch)
    msgs=[{"role":"system","content":SYS},{"role":"user","content":user}]
    t=time.time()
    try:
        res=llm.create_chat_completion(messages=msgs,temperature=0.0,top_k=1,top_p=1.0,seed=SEED,max_tokens=(64 if tag.lower().startswith('qwen3') else 48))
        txt=res['choices'][0]['message']['content']; ptok=res['usage']['prompt_tokens']; err=None
    except Exception as e:
        txt=None; ptok=None; err=repr(e)
    rec=dict(id=r['id'],model=tag,quant=quant,gguf=os.path.basename(path),truncated=trunc,prompt_tokens=ptok,
             output=txt,error=err,secs=round(time.time()-t,2))
    f.write(json.dumps(rec)+'\n'); f.flush()
    print(k,r['id'],rec['secs'],ptok,repr(txt)[:80],flush=True)
print('total s',round(time.time()-t0,1),flush=True)
