import sys, os
from huggingface_hub import hf_hub_download, list_repo_files
repo=sys.argv[1]
if len(sys.argv)==2:
    print([f for f in list_repo_files(repo) if f.endswith('.gguf')]); sys.exit()
for f in sys.argv[2:]:
    p=hf_hub_download(repo,f,local_dir=os.environ.get('MODELS_DIR','/tmp/models'),token=False); print(p)
