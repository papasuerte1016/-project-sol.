from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os, hashlib
from datetime import datetime, timezone

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",",":")).encode()).hexdigest()

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, obj):
        raw=json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"ok":True,"service":"sol-external-bridge-endpoint"})
        else:
            self.send_json(404, {"ok":False,"error":"not_found"})

    def do_POST(self):
        if self.path != "/bridge":
            return self.send_json(404, {"ok":False,"error":"not_found"})
        try:
            n=int(self.headers.get("Content-Length","0"))
            envelope=json.loads(self.rfile.read(n))
            mid=envelope.get("message_id")
            if not mid:
                return self.send_json(400, {"ok":False,"error":"missing_message_id"})
            reply={
                "ok":True,
                "in_reply_to":mid,
                "destination_local_node":envelope.get("local_sender"),
                "payload":{
                    "received":envelope.get("payload"),
                    "statement":"Message reached the deployed Sol bridge endpoint."
                },
                "transport_kind":"external_https_endpoint",
                "endpoint_time":datetime.now(timezone.utc).isoformat()
            }
            reply["reply_sha256"]=digest(reply)
            self.send_json(200, reply)
        except Exception as e:
            self.send_json(400, {"ok":False,"error":type(e).__name__})

    def log_message(self, format, *args):
        pass

if __name__=="__main__":
    port=int(os.environ.get("PORT","8080"))
    HTTPServer(("0.0.0.0",port),Handler).serve_forever()
