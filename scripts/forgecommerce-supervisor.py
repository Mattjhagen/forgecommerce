#!/usr/bin/env python3
"""Small local supervisor: bounded retries, lock ownership, graceful shutdown."""
import fcntl, os, signal, subprocess, sys, time
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); lock=open(os.path.join(root,".forgecommerce-supervisor.lock"),"w")
try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except OSError: raise SystemExit("another supervisor is already running")
attempts=0; stopping=False
def stop(*_):
    global stopping; stopping=True
signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
while not stopping and attempts < 5:
    proc=subprocess.Popen([sys.executable,"-m","forgecommerce.app"],cwd=root); code=proc.wait()
    if stopping: break
    attempts += 1; time.sleep(min(2 ** attempts, 30))
raise SystemExit(0 if stopping or attempts < 5 else 1)
