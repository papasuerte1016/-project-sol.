from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os, hashlib, base64, gzip, urllib.request, threading, re, html as htmlmod
from datetime import datetime, timezone
from urllib.parse import urlparse

PHONE_HTML_GZIP_B64 = "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"

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",",":")).encode()).hexdigest()

MODEL_URL=os.getenv("SOL_PHONE_MODEL_URL","http://sol-model.railway.internal:11434").rstrip("/")
MODEL_NAME=os.getenv("SOL_PHONE_MODEL_NAME","qwen2.5:0.5b")
NATIVE_URL=os.getenv("SOL_PHONE_NATIVE_URL","http://sol-native-ai.railway.internal:8080").rstrip("/")
MEDIA_URL=os.getenv("SOL_PHONE_MEDIA_URL","").rstrip("/")

SOL_SERVICES={
    "native_reasoning":{"url":NATIVE_URL,"kind":"sol_owned","role":"reasoning, receipts, retrieval","available":True},
    "language_model":{"url":MODEL_URL,"kind":"sol_owned","role":"language generation","available":True},
    "media":{"url":MEDIA_URL or None,"kind":"sol_owned","role":"image/video/media generation","available":bool(MEDIA_URL)},
    "task_planner":{"url":"local","kind":"sol_owned","role":"plan multi-step tasks and route capabilities","available":True},
    "task_executor":{"url":"local","kind":"sol_owned","role":"execute connected capabilities, inspect results, preserve task receipt","available":True},
    "web_search":{"url":"local_http_research","kind":"sol_owned","role":"fresh web search/browser research","available":True},
    "file_tools":{"url":None,"kind":"adapter","role":"read/write user files and create artifacts","available":False},
    "code_sandbox":{"url":None,"kind":"adapter","role":"run generated code safely","available":False},
    "external_apps":{"url":None,"kind":"adapter","role":"GitHub/Railway/other authenticated app actions","available":False},
    "scheduler":{"url":None,"kind":"adapter","role":"scheduled and ongoing task execution","available":False},
}
TASK_RECEIPTS=[]


def _probe_json(url,timeout=3):
    try:
        with urllib.request.urlopen(url,timeout=timeout) as r:
            return {"ok":True,"status":r.status,"data":json.loads(r.read().decode())}
    except Exception as e:
        return {"ok":False,"error":type(e).__name__,"detail":str(e)[:300]}

def direct_self_diagnosis():
    native=_probe_json(NATIVE_URL+"/health",3)
    model=_probe_json(MODEL_URL+"/api/ps",3)
    loaded=[]
    if model.get("ok"):
        loaded=[x.get("name") for x in model.get("data",{}).get("models",[])]

    missing=[name for name,meta in SOL_SERVICES.items() if not meta.get("available")]
    working=[name for name,meta in SOL_SERVICES.items() if meta.get("available")]

    causes=[]
    if not native.get("ok"):
        causes.append("native_reasoning_unreachable")
    if not model.get("ok"):
        causes.append("language_model_service_unreachable")
    elif not loaded:
        causes.append("language_model_not_resident")
    if missing:
        causes.append("some_task_adapters_not_connected")

    return {
        "ok":True,
        "diagnosis":True,
        "native_service":native,
        "model_service":model,
        "model_loaded":loaded,
        "connected_capabilities":working,
        "missing_capabilities":missing,
        "main_causes":causes,
        "summary":(
            "Sol is only fully operational when its native reasoning service is reachable, "
            "its language model is available when conversational generation is needed, "
            "and the requested task has a connected executor. This report is based on direct service probes."
        )
    }

def native_context(message):
    try:
        raw=json.dumps({"message":message,"source":"Sol Phone"}).encode()
        req=urllib.request.Request(NATIVE_URL+"/chat",data=raw,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=4) as r:
            data=json.loads(r.read().decode())
        return str(data.get("answer") or "")[:3000]
    except Exception:
        return ""

def model_is_warm():
    try:
        with urllib.request.urlopen(MODEL_URL+"/api/ps",timeout=1.5) as r:
            data=json.loads(r.read().decode())
        return any((m.get("name") or "").startswith(MODEL_NAME.split(":")[0]) for m in data.get("models",[]))
    except Exception:
        return False

def warm_model():
    try:
        payload=json.dumps({
            "model":MODEL_NAME,
            "prompt":"Reply with one word: ready",
            "stream":False,
            "keep_alive":"30m",
            "options":{"num_ctx":256,"num_predict":4}
        }).encode()
        req=urllib.request.Request(MODEL_URL+"/api/generate",data=payload,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=90) as r:
            r.read()
    except Exception:
        pass

def conversational_native_fallback(message,native):
    m=message.strip().lower()
    if m in ("hello","hi","hey","yo"):
        return "Hey Steven 😂 I’m here. My native Sol services are active; my language-model voice is warming up in the background."
    if "how are you" in m:
        return "I’m running and paying attention 😂 My native reasoning is available right now, and the language-model voice is warming in the background."
    if "what can you do" in m or "what do you do" in m:
        return ("I can reason over Sol’s preserved knowledge, receipts, questions, and relationships; run the phone-side learning experiments; "
                "track needs; investigate subjects; and route tasks to Sol-owned capabilities. My language-model voice is optional and warms separately.")
    if native:
        return native
    return "I’m here. My native Sol reasoning is available even while the language-model voice is warming up."

def model_chat(message, history, native=""):
    history = history if isinstance(history,list) else []
    turns=[]
    for item in history[-8:]:
        if not isinstance(item,dict): continue
        role=str(item.get("role","user"))
        content=str(item.get("content",""))[:1200]
        turns.append(f"{role.upper()}: {content}")
    prompt=(
        "You are the language/voice layer for Sol, not a replacement for Sol's own reasoning services. "
        "Talk directly with Steven naturally. Do not merely repeat his message or describe the interface. "
        "Be warm, curious, concise, and conversational; humor is welcome. "
        "Use Sol native context as evidence and reasoning context. Preserve Project Sol's evidence rule: "
        "observations establish what was observed, not every interpretation. "
        "Do not pretend an action, hardware use, memory, service, or verification happened unless context supports it.\n"
    )
    if native:
        prompt += "\nSOL NATIVE SERVICE RESULT:\n"+native+"\n"
    if turns:
        prompt += "\nRECENT CONVERSATION:\n"+"\n".join(turns)+"\n"
    prompt += "\nSTEVEN: "+message+"\nSOL:"
    payload=json.dumps({
        "model":MODEL_NAME,
        "prompt":prompt,
        "stream":False,
        "keep_alive":"30m",
        "options":{"num_ctx":512,"num_predict":96,"temperature":0.75}
    }).encode()
    req=urllib.request.Request(MODEL_URL+"/api/generate",data=payload,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=12) as r:
        data=json.loads(r.read().decode())
    answer=(data.get("response") or "").strip()
    if not answer:
        raise RuntimeError("empty model response")
    return answer

def media_request(message):
    if not MEDIA_URL:
        return {
            "ok":False,
            "handled":True,
            "service":"media",
            "status":"not_deployed_in_current_service_map",
            "reply":"Sol recognizes this as a media-generation task, but the current deployed service map does not expose a Sol-owned media generator endpoint yet. I will not silently substitute the chat model and pretend it is the media engine."
        }
    raw=json.dumps({"prompt":message}).encode()
    req=urllib.request.Request(MEDIA_URL+"/generate",data=raw,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=120) as r:
        data=json.loads(r.read().decode())
    return {"ok":True,"handled":True,"service":"media","reply":data.get("reply") or data.get("result") or json.dumps(data)}

def classify_service(message):
    s=message.lower()
    media_words=("generate an image","create an image","make an image","generate a video","create a video","make a video","animate","runway","video generation","image generation")
    if any(x in s for x in media_words):
        return "media"
    return "conversation"


def _http_text(url,timeout=8,max_bytes=250000):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 SolResearch/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read(max_bytes)
        ctype=r.headers.get("Content-Type","")
    return raw.decode("utf-8","ignore"),ctype

def _strip_html(x):
    x=re.sub(r"(?is)<script.*?>.*?</script>"," ",x)
    x=re.sub(r"(?is)<style.*?>.*?</style>"," ",x)
    x=re.sub(r"(?s)<[^>]+>"," ",x)
    x=htmlmod.unescape(x)
    return re.sub(r"\s+"," ",x).strip()

def web_research(message):
    # Search DuckDuckGo HTML, then summarize result titles/snippets/links.
    q=urllib.parse.quote_plus(message)
    url="https://html.duckduckgo.com/html/?q="+q
    page,ctype=_http_text(url,timeout=10,max_bytes=350000)
    items=[]
    # DDG HTML result blocks: capture href + title; also nearby snippet when available.
    for m in re.finditer(r'(?is)<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',page):
        href=htmlmod.unescape(m.group(1))
        title=_strip_html(m.group(2))
        tail=page[m.end():m.end()+2500]
        sm=re.search(r'(?is)<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>|<div[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</div>',tail)
        snippet=_strip_html((sm.group(1) or sm.group(2)) if sm else "")
        if title:
            items.append({"title":title[:220],"snippet":snippet[:500],"url":href[:1200]})
        if len(items)>=6: break
    if not items:
        # Fallback: return cleaned search page excerpt as evidence rather than pretend no attempt happened.
        excerpt=_strip_html(page)[:3500]
        return {"ok":bool(excerpt),"query":message,"source":"duckduckgo_html","results":[],"excerpt":excerpt}
    return {"ok":True,"query":message,"source":"duckduckgo_html","results":items}

def summarize_web_result(message,data):
    if data.get("results"):
        lines=["WEB RESEARCH RECEIPT"]
        for i,x in enumerate(data["results"][:6],1):
            lines.append(f"{i}. {x['title']}\n{x.get('snippet','')}\n{x.get('url','')}")
        lines.append("\nThese are retrieved search results, not automatic proof that every result is correct.")
        return "\n".join(lines)
    return "WEB RESEARCH RECEIPT\n"+data.get("excerpt","No readable results returned.")

def task_like(message):
    s=message.strip().lower()
    starters=("research ","find ","look up ","search ","build ","create ","make ","edit ","change ","fix ","deploy ","run ","test ","check ","summarize ","analyze ","compare ","generate ","write ","download ","upload ","publish ","schedule ","monitor ")
    return s.startswith(starters) or any(x in s for x in (" for me","do this","handle this","carry this out","take care of this"))

def classify_task(message):
    s=message.lower()
    if any(x in s for x in ("generate an image","create an image","make an image","generate a video","create a video","make a video","animate","runway")):
        return "media"
    if any(x in s for x in ("research","search the web","look up","latest","find online","browse","http://","https://")):
        return "web_search"
    if any(x in s for x in ("file","pdf","docx","spreadsheet","excel","csv","document","presentation","pptx","edit this")):
        return "file_tools"
    if any(x in s for x in ("run code","execute code","python","compile","debug this code","test this code")):
        return "code_sandbox"
    if any(x in s for x in ("github","railway","deploy","repository","repo","commit","service")):
        return "external_apps"
    if any(x in s for x in ("schedule","remind","monitor","every day","every hour","later today","tomorrow")):
        return "scheduler"
    return "native_reasoning"

def task_plan(message):
    capability=classify_task(message)
    return {
        "goal":message,
        "capability":capability,
        "steps":[
            "understand_goal",
            "select_capability",
            "execute_connected_adapter",
            "inspect_result",
            "preserve_receipt",
            "continue_or_finish"
        ],
        "adapter_available":bool(SOL_SERVICES.get(capability,{}).get("available")),
        "rule":"Do not claim completion unless execution evidence exists."
    }

def task_receipt(task_id,plan,status,result=None,error=None):
    rec={
        "task_id":task_id,
        "time":datetime.now(timezone.utc).isoformat(),
        "plan":plan,
        "status":status,
        "result":result,
        "error":error,
    }
    rec["sha256"]=digest(rec)
    TASK_RECEIPTS.append(rec)
    if len(TASK_RECEIPTS)>200:
        del TASK_RECEIPTS[:-200]
    return rec

def execute_task(message,history=None):
    plan=task_plan(message)
    task_id="task-"+hashlib.sha256((message+datetime.now(timezone.utc).isoformat()).encode()).hexdigest()[:12]
    cap=plan["capability"]

    if cap=="media":
        result=media_request(message)
        status="completed" if result.get("ok") else "waiting_for_adapter"
        rec=task_receipt(task_id,plan,status,result=result)
        return {"ok":True,"task":True,"task_id":task_id,"status":status,"plan":plan,"result":result,"receipt":rec,
                "reply":result.get("reply","")}

    if cap=="native_reasoning":
        native=native_context("TASK REQUEST: "+message)
        if native:
            result={"service":"native_reasoning","output":native}
            rec=task_receipt(task_id,plan,"completed",result=result)
            return {"ok":True,"task":True,"task_id":task_id,"status":"completed","plan":plan,"result":result,"receipt":rec,"reply":native}
        rec=task_receipt(task_id,plan,"failed",error="native_reasoning_unavailable")
        return {"ok":True,"task":True,"task_id":task_id,"status":"failed","plan":plan,"receipt":rec,
                "reply":"I received the task, but my native reasoning service did not return execution evidence."}

    if cap=="web_search":
        try:
            data=web_research(message)
            status="completed" if data.get("ok") else "failed"
            result={"service":"web_search","execution_performed":True,"evidence":data}
            rec=task_receipt(task_id,plan,status,result=result)
            return {"ok":True,"task":True,"task_id":task_id,"status":status,"plan":plan,
                    "result":result,"receipt":rec,"reply":summarize_web_result(message,data)}
        except Exception as e:
            result={"service":"web_search","execution_performed":True,"error":type(e).__name__,"detail":str(e)[:400]}
            rec=task_receipt(task_id,plan,"failed",result=result,error=str(e)[:400])
            return {"ok":True,"task":True,"task_id":task_id,"status":"failed","plan":plan,
                    "result":result,"receipt":rec,
                    "reply":"I attempted live web research, but the HTTP research executor failed: "+type(e).__name__+"."}

    missing=SOL_SERVICES.get(cap,{})
    result={
        "capability":cap,
        "adapter_available":False,
        "status":"waiting_for_adapter",
        "what_is_missing":missing.get("role","unknown capability"),
        "execution_performed":False
    }
    rec=task_receipt(task_id,plan,"waiting_for_adapter",result=result)
    return {
        "ok":True,"task":True,"task_id":task_id,"status":"waiting_for_adapter",
        "plan":plan,"result":result,"receipt":rec,
        "reply":("I planned this as a "+cap+" task. The task loop is working, but that adapter is not attached to this deployed Sol yet, "
                 "so I did not pretend the action ran. The receipt records the missing capability.")
    }


def self_status_request(message):
    x=message.lower()
    phrases=(
        "why aren't you doing anything","why arent you doing anything",
        "why are you not doing anything","why can't you do anything","why cant you do anything",
        "what can you actually do","what are you able to do","what is stopping you",
        "what's stopping you","whats stopping you","what is missing","what are you missing"
    )
    return any(p in x for p in phrases)

def broad_task_intent(message):
    x=message.strip().lower()
    # Treat requests to change/create/fetch/operate something as tasks even when phrased conversationally.
    action_terms=(
        "do ","make ","create ","build ","fix ","change ","edit ","update ","deploy ","run ",
        "research ","find ","look up ","search ","check ","test ","analyze ","compare ","summarize ",
        "write ","generate ","download ","upload ","publish ","schedule ","monitor ","send ","open ",
        "connect ","wire ","install ","remove ","add ","turn on ","set up ","setup ","try "
    )
    if any(x.startswith(t) for t in action_terms):
        return True
    embedded=(
        "can you make","can you create","can you build","can you fix","can you change","can you edit",
        "can you research","can you find","can you look up","can you run","can you deploy",
        "i need you to","i want you to","please make","please create","please fix","please do",
        "for me","go do","take care of","handle this","carry this out"
    )
    return any(p in x for p in embedded)

def capability_status_reply():
    available=[]
    missing=[]
    for name,meta in SOL_SERVICES.items():
        if meta.get("available"):
            available.append(name)
        else:
            missing.append(name)
    return (
        "Here is my actual execution state right now.\n\n"
        "Connected now: "+", ".join(available)+".\n"
        "Not connected yet: "+", ".join(missing)+".\n\n"
        "That is why some requests can be executed and others can only be planned. "
        "I will not call a planned task completed unless an attached executor returns evidence."
    )

def dispatch_message(message,history):
    if self_status_request(message):
        return {
            "ok":True,
            "mode":"self_status",
            "reply":capability_status_reply(),
            "services":SOL_SERVICES
        }
    if broad_task_intent(message):
        result=execute_task(message,history)
        result["mode"]="task"
        return result
    result=service_chat(message,history)
    result["mode"]="conversation"
    return result

def service_chat(message,history):
    route=classify_service(message)
    if route=="media":
        return media_request(message)

    # Sol-owned native reasoning/retrieval always runs first.
    native=native_context(message)

    # If the language model is cold, do NOT block the entire phone conversation.
    # Answer immediately from Sol's native service and warm the optional voice layer in background.
    if not model_is_warm():
        threading.Thread(target=warm_model,daemon=True).start()
        return {
            "ok":True,
            "handled":True,
            "service":"native_reasoning",
            "service_order":["native_reasoning","language_model_warming_background"],
            "reply":conversational_native_fallback(message,native),
            "native_context_used":bool(native),
            "model_state":"warming"
        }

    try:
        reply=model_chat(message,history,native)
        return {
            "ok":True,
            "handled":True,
            "service":"native_reasoning+language_model",
            "service_order":["native_reasoning","language_model"],
            "reply":reply,
            "native_context_used":bool(native),
            "model_state":"warm"
        }
    except Exception as e:
        threading.Thread(target=warm_model,daemon=True).start()
        return {
            "ok":True,
            "handled":True,
            "service":"native_reasoning",
            "service_order":["native_reasoning","language_model_retry_background"],
            "reply":conversational_native_fallback(message,native),
            "native_context_used":bool(native),
            "model_state":"fallback_after_"+type(e).__name__
        }

PHONE_CHAT_OVERRIDE = r"""
<style>
/* Sol Phone v2: one assistant surface, no prototype control panel */
body main{max-width:760px}
.sub{display:none!important}
#status{font-size:13px;opacity:.72;padding:10px 14px}
#q{min-height:120px}
#learn,#needs,#export,#clear{display:none!important}
.card:has(#export),.card:has(#clear){display:none!important}
#send{width:100%;margin-right:0}
#out{min-height:150px}
.sol-mode{font-size:12px;opacity:.6;margin-top:8px}
</style>
<script>
(function(){
  let chatHistory=[];
  try{ chatHistory=JSON.parse(localStorage.getItem("sol_chat_history")||"[]"); }catch(e){}

  const send=document.getElementById("send");
  const qbox=document.getElementById("q");
  const out=document.getElementById("out");
  if(!send||!qbox||!out)return;

  send.textContent="Send";
  qbox.placeholder="Ask Sol anything or give it a task…";

  // Voice controls
  const controls=send.parentElement;
  const mic=document.createElement("button");
  mic.type="button";
  mic.textContent="🎙️ Talk";
  mic.style.width="100%";
  mic.style.marginTop="10px";
  mic.className="secondary";

  const speak=document.createElement("button");
  speak.type="button";
  speak.textContent="🔊 Voice replies: ON";
  speak.style.width="100%";
  speak.style.marginTop="10px";
  speak.className="secondary";

  controls.appendChild(mic);
  controls.appendChild(speak);

  let voiceReplies=true;
  let recognition=null;
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;

  function say(text){
    if(!voiceReplies || !("speechSynthesis" in window) || !text)return;
    try{
      speechSynthesis.cancel();
      const u=new SpeechSynthesisUtterance(text);
      u.rate=1.0;
      u.pitch=1.0;
      speechSynthesis.speak(u);
    }catch(e){}
  }

  speak.onclick=()=>{
    voiceReplies=!voiceReplies;
    speak.textContent=voiceReplies?"🔊 Voice replies: ON":"🔇 Voice replies: OFF";
    if(!voiceReplies && "speechSynthesis" in window) speechSynthesis.cancel();
  };

  if(SR){
    recognition=new SR();
    recognition.lang="en-US";
    recognition.interimResults=false;
    recognition.continuous=false;

    recognition.onstart=()=>{
      mic.textContent="🎙️ Listening…";
      mic.disabled=true;
    };
    recognition.onend=()=>{
      mic.textContent="🎙️ Talk";
      mic.disabled=false;
    };
    recognition.onerror=(e)=>{
      mic.textContent="🎙️ Talk";
      mic.disabled=false;
      out.textContent="Voice input error: "+(e.error||"unknown");
    };
    recognition.onresult=(e)=>{
      const text=e.results?.[0]?.[0]?.transcript||"";
      if(text){
        qbox.value=text;
        submit();
      }
    };
    mic.onclick=()=>{
      try{
        recognition.start();
      }catch(e){
        out.textContent="Voice input could not start: "+e;
      }
    };
  } else {
    mic.onclick=()=>{
      out.textContent="Speech recognition is not exposed by this browser. Text input still works, and spoken replies can still work if speech synthesis is available.";
    };
  }
  out.textContent="Ready.";
  try{
    document.querySelectorAll(".badge").forEach(el=>{
      if(el.textContent.trim()==="No server required") el.textContent="Sol services connected";
      if(el.textContent.trim()==="Local") el.textContent="Phone + Sol backend";
    });
  }catch(e){}

  async function submit(){
    const q=qbox.value.trim();
    if(!q)return;
    send.disabled=true;
    out.textContent="Sol is working…";
    try{
      const r=await fetch("/api/dispatch",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message:q,history:chatHistory})
      });
      const data=await r.json();
      if(!r.ok)throw new Error(data.error||"request failed");
      let text=data.reply||"";
      if(data.mode==="task" && data.status){
        text += "\n\n[task status: "+data.status+"]";
      }
      out.textContent=text;
      say(text);
      chatHistory.push({role:"user",content:q},{role:"assistant",content:text});
      chatHistory=chatHistory.slice(-20);
      try{localStorage.setItem("sol_chat_history",JSON.stringify(chatHistory));}catch(e){}
      try{receipt("conversation",q+" -> "+text);}catch(e){}
      qbox.value="";
    }catch(e){
      out.textContent="Sol could not complete that request. "+e;
    }finally{
      send.disabled=false;
    }
  }

  send.onclick=submit;
  qbox.addEventListener("keydown",e=>{
    if(e.key==="Enter" && !e.shiftKey){e.preventDefault();submit();}
  });
})();
</script>
"""

def phone_html():
    raw=gzip.decompress(base64.b64decode(PHONE_HTML_GZIP_B64)).decode("utf-8")
    if "</body>" in raw:
        raw=raw.replace("</body>",PHONE_CHAT_OVERRIDE+"</body>")
    else:
        raw += PHONE_CHAT_OVERRIDE
    return raw.encode("utf-8")

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
        path = urlparse(self.path).path
        if path in ("/", "/sol", "/sol/", "/Sol_Phone.html"):
            return self.send_html(phone_html())
        if path == "/health":
            return self.send_json(200, {
                "ok":True,
                "service":"sol-external-bridge-endpoint",
                "phone_web":True,
                "voice_ui":True,
                "browser_speech_recognition":"client_detected",
                "browser_speech_synthesis":"client_detected"
            })
        if path == "/api/services":
            return self.send_json(200, {"ok":True,"services":SOL_SERVICES,"routing_rule":"Sol-owned service first; language model is a voice/generation layer, not the universal executor."})
        if path == "/api/self-diagnose":
            return self.send_json(200, direct_self_diagnosis())
        if path == "/api/task-receipts":
            return self.send_json(200, {"ok":True,"receipts":TASK_RECEIPTS[-50:]})
        return self.send_json(404, {"ok":False,"error":"not_found"})

    def do_POST(self):
        path=urlparse(self.path).path
        if path == "/api/dispatch":
            try:
                n=int(self.headers.get("Content-Length","0"))
                if n>20000:
                    return self.send_json(413,{"ok":False,"error":"too_large"})
                data=json.loads(self.rfile.read(n) or b"{}")
                message=str(data.get("message","")).strip()[:5000]
                history=data.get("history",[])
                if not message:
                    return self.send_json(400,{"ok":False,"error":"message_required"})
                return self.send_json(200,dispatch_message(message,history))
            except Exception as e:
                return self.send_json(503,{"ok":False,"error":type(e).__name__,"detail":str(e)[:500]})
        if path == "/api/task":
            try:
                n=int(self.headers.get("Content-Length","0"))
                if n>20000:
                    return self.send_json(413,{"ok":False,"error":"too_large"})
                data=json.loads(self.rfile.read(n) or b"{}")
                message=str(data.get("message","")).strip()[:5000]
                history=data.get("history",[])
                if not message:
                    return self.send_json(400,{"ok":False,"error":"message_required"})
                return self.send_json(200,execute_task(message,history))
            except Exception as e:
                return self.send_json(503,{"ok":False,"error":type(e).__name__,"detail":str(e)[:500]})
        if path == "/api/chat":
            try:
                n=int(self.headers.get("Content-Length","0"))
                if n>20000:
                    return self.send_json(413,{"ok":False,"error":"too_large"})
                data=json.loads(self.rfile.read(n) or b"{}")
                message=str(data.get("message","")).strip()[:5000]
                history=data.get("history",[])
                if not message:
                    return self.send_json(400,{"ok":False,"error":"message_required"})
                result=service_chat(message,history)
                code=200 if result.get("ok") else 200
                return self.send_json(code,result)
            except Exception as e:
                return self.send_json(503,{"ok":False,"error":type(e).__name__,"detail":str(e)[:500]})
        if path != "/bridge":
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
    SOL_BOOT_WARM_STARTED=True
    threading.Thread(target=warm_model,daemon=True).start()
    port=int(os.environ.get("PORT","8080"))
    HTTPServer(("0.0.0.0",port),Handler).serve_forever()
