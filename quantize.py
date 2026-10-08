"""Quantize an F16 GGUF to Q8_0 / Q4_K_M with llama.cpp's llama_model_quantize (via llama-cpp-python), no imatrix.
usage: quantize.py IN.gguf OUT.gguf q8_0|q4_k_m"""
import sys, llama_cpp, time
ft={'q8_0':llama_cpp.LLAMA_FTYPE_MOSTLY_Q8_0,'q4_k_m':llama_cpp.LLAMA_FTYPE_MOSTLY_Q4_K_M}[sys.argv[3]]
p=llama_cpp.llama_model_quantize_default_params(); p.ftype=ft; p.nthread=2
t=time.time(); rc=llama_cpp.llama_model_quantize(sys.argv[1].encode(),sys.argv[2].encode(),p)
print('rc',rc,'secs',round(time.time()-t,1))
