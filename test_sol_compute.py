import json
#!/usr/bin/env python3
import os, tempfile
fd,path=tempfile.mkstemp(); os.close(fd); os.unlink(path)
os.environ["SOL_TOKEN_DB"]=path
import sol_compute_token as t
import sol_compute_adapter as a
r=t.mint("test",5,"test allocation")
assert t.balance("test")==5
x=a.execute("test","wordcount","Sol learns by doing")
assert x["result"]["words"]==4 and x["units_spent"]==1
assert t.balance("test")==4
assert t.verify()["valid"]
print("PASS",json.dumps({"balance":4,"backend":x["backend"],"receipt":x["spend_receipt"]["event_hash"]}))
