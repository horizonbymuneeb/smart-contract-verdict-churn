import sys,time,json
from llama_cpp import Llama
llm=Llama(sys.argv[1],n_ctx=4096,n_threads=2,n_batch=512,seed=1,verbose=False)
r=json.load(open('data/contracts.json'))
code=[x for x in r if x['id'].endswith('parity_wallet_bug_1.sol')][0]['code'][:6000]
toks=llm.tokenize(code.encode())
t=time.time(); llm.eval(toks); a=time.time()-t
llm.reset(); t=time.time(); out=llm.create_completion("def f():",max_tokens=32,temperature=0); b=time.time()-t
print(sys.argv[1].split('/')[-1],'prefill tok/s',round(len(toks)/a,1),'decode tok/s~',round(out['usage']['completion_tokens']/b,1))
