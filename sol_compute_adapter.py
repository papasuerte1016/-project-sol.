#!/usr/bin/env python3
"""Sol Compute Adapter v0.1 — compute happens only after verified Sol-unit authorization."""
import argparse, hashlib, json, math, os, subprocess, sys, time
import sol_compute_token as token

MAX_N=int(os.getenv("SOL_COMPUTE_MAX_N","200000"))

def estimate(job,payload):
    n=len(payload.encode())
    return max(1, math.ceil(n/1024))

def run_local(job,payload):
    if job=="sha256":
        return {"sha256":hashlib.sha256(payload.encode()).hexdigest()}
    if job=="wordcount":
        return {"words":len(payload.split()),"chars":len(payload)}
    if job=="primecount":
        n=int(payload)
        if n<0 or n>MAX_N: raise ValueError(f"primecount n must be 0..{MAX_N}")
        sieve=bytearray(b"\x01")*(n+1)
        if n>=0: sieve[:2]=b"\x00\x00"
        for p in range(2,int(n**0.5)+1):
            if sieve[p]: sieve[p*p:n+1:p]=b"\x00"*(((n-p*p)//p)+1)
        return {"n":n,"primes":sum(sieve)}
    raise ValueError("unsupported job")

def execute(account,job,payload):
    check=token.verify()
    if not check["valid"]: raise RuntimeError("token ledger failed verification")
    units=estimate(job,payload)
    before=token.balance(account)
    if before<units: raise ValueError(f"insufficient compute units: need {units}, have {before}")
    # Perform bounded local computation first; charge only successful jobs.
    started=time.time()
    result=run_local(job,payload)
    receipt=token.spend(account,units,f"compute:{job}")
    return {"backend":"sol-local","job":job,"units_spent":units,
            "balance_before":before,"balance_after":token.balance(account),
            "elapsed_ms":round((time.time()-started)*1000,3),
            "result":result,"spend_receipt":receipt}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("account"); p.add_argument("job",choices=["sha256","wordcount","primecount"]); p.add_argument("payload")
    a=p.parse_args()
    try: print(json.dumps(execute(a.account,a.job,a.payload),indent=2))
    except Exception as e:
        print(json.dumps({"ok":False,"error":str(e)},indent=2)); raise SystemExit(1)
if __name__=="__main__": main()
