import json, urllib.request, uuid, hashlib
from datetime import datetime, timezone

endpoint="https://sol-portable-test-production.up.railway.app/bridge"
env={
 "message_id":str(uuid.uuid4()),
 "local_sender":"sol-native-ai",
 "destination":endpoint,
 "payload":{"kind":"external_transport_probe","text":"Hello from the Railway-hosted Sol node."},
 "identity":None,
 "created":datetime.now(timezone.utc).isoformat()
}
env["request_sha256"]=hashlib.sha256(json.dumps(env,sort_keys=True,separators=(",",":")).encode()).hexdigest()
req=urllib.request.Request(endpoint,data=json.dumps(env).encode(),headers={"Content-Type":"application/json"},method="POST")
with urllib.request.urlopen(req,timeout=20) as r:
    reply=json.loads(r.read().decode())
verified=(reply.get("in_reply_to")==env["message_id"] and reply.get("transport_kind")=="external_https_endpoint")
print("SOL_EXTERNAL_TRANSPORT_RECEIPT="+json.dumps({
 "endpoint":endpoint,
 "message_id":env["message_id"],
 "request_sha256":env["request_sha256"],
 "http_status":200,
 "reply":reply,
 "message_id_verified":verified,
 "external_roundtrip_verified":verified
},sort_keys=True))
if not verified:
    raise SystemExit("external reply verification failed")
