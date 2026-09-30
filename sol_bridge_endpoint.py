from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os, hashlib, base64, gzip
from datetime import datetime, timezone

PHONE_HTML_GZIP_B64 = "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"

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",",":")).encode()).hexdigest()

def phone_html():
    return gzip.decompress(base64.b64decode(PHONE_HTML_GZIP_B64))

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, obj):
        raw=json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_html(self, raw):
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path in ("/", "/sol", "/sol/", "/Sol_Phone.html"):
            return self.send_html(phone_html())
        if self.path == "/health":
            return self.send_json(200, {"ok":True,"service":"sol-external-bridge-endpoint","phone_web":True})
        return self.send_json(404, {"ok":False,"error":"not_found"})

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
