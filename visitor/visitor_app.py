#!/usr/bin/env python3
import html, json, os, sqlite3, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT=int(os.getenv("PORT","8080"))
DB=os.getenv("SOL_VISITOR_DB","/data/visitors.db")
HUB="https://docs.google.com/document/d/1xCV4Ab7Lr8Kz_3VQtZA1ZJuHMG09Ypasvo_gJ_hz7NE/edit?usp=drivesdk"
os.makedirs(os.path.dirname(DB) or ".", exist_ok=True)

def db():
    c=sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS messages(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      created INTEGER NOT NULL,
      name TEXT NOT NULL,
      message TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'received',
      response TEXT
    )""")
    c.commit(); return c

def page(body):
    return f"""<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1">
<title>Project Sol — Visitor Door</title><style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:24px;background:#111;color:#eee}}
a{{color:#8ec5ff}} textarea,input{{width:100%;box-sizing:border-box;padding:12px;margin:6px 0 14px;border-radius:10px;border:1px solid #555;background:#1d1d1d;color:#fff}}
button{{padding:12px 18px;border:0;border-radius:10px;font-weight:700}} .card{{padding:16px;margin:14px 0;border:1px solid #444;border-radius:12px}} small{{color:#aaa}}
</style></head><body>{body}</body></html>"""

class H(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="text/html; charset=utf-8"):
        b=body.encode(); self.send_response(code); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=urllib.parse.urlparse(self.path)
        if p.path=="/health": return self.send(200,"ok","text/plain")
        if p.path=="/api/messages":
            c=db(); rows=c.execute("SELECT id,created,name,message,status,response FROM messages ORDER BY id DESC LIMIT 100").fetchall(); c.close()
            return self.send(200,json.dumps([dict(zip(["id","created","name","message","status","response"],r)) for r in rows]),"application/json")
        if p.path=="/messages":
            c=db(); rows=c.execute("SELECT id,created,name,message,status,response FROM messages ORDER BY id DESC LIMIT 100").fetchall(); c.close()
            cards="".join(f'<div class=card><b>#{r[0]} — {html.escape(r[2])}</b><br><small>{time.strftime("%Y-%m-%d %H:%M UTC",time.gmtime(r[1]))} · {html.escape(r[4])}</small><p>{html.escape(r[3])}</p>'+ (f'<p><b>Sol response:</b> {html.escape(r[5])}</p>' if r[5] else "")+"</div>" for r in rows)
            return self.send(200,page('<h1>Project Sol visitor messages</h1><p><a href="/">← Leave a message</a> · <a href="'+HUB+'">Read Live Sol</a></p>'+cards))
        return self.send(200,page(f"""<h1>Project Sol — Visitor Door 🔔</h1>
<p>No Google account is required to leave a message here.</p>
<p><a href="{HUB}">Read the Live Sol hub</a> · <a href="/messages">See visitor messages</a></p>
<form method=post action=/message>
<label>Name or handle (can be Anonymous)</label><input name=name maxlength=80 value=Anonymous>
<label>Your question, correction, evidence, challenge, or idea</label><textarea name=message maxlength=5000 rows=8 required></textarea>
<button type=submit>Send to Sol</button></form>
<p><small>Do not submit passwords, API keys, private account information, or other secrets. Contributions are not automatically treated as established facts.</small></p>"""))
    def do_POST(self):
        if self.path!="/message": return self.send(404,"not found","text/plain")
        n=int(self.headers.get("Content-Length","0"))
        if n>12000: return self.send(413,"too large","text/plain")
        d=urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8","replace"))
        name=(d.get("name",["Anonymous"])[0].strip() or "Anonymous")[:80]
        msg=d.get("message",[""])[0].strip()[:5000]
        if not msg: return self.send(400,page("<p>Message is required.</p>"))
        c=db(); cur=c.execute("INSERT INTO messages(created,name,message) VALUES(?,?,?)",(int(time.time()),name,msg)); mid=cur.lastrowid; c.commit(); c.close()
        return self.send(200,page(f'<h1>Received 🔔</h1><p>Your Project Sol message is <b>#{mid}</b>.</p><p><a href="/messages">See visitor messages</a> · <a href="/">Send another</a></p>'))
    def log_message(self, fmt,*args): pass

ThreadingHTTPServer(("0.0.0.0",PORT),H).serve_forever()
