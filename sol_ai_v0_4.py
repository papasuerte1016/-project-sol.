#!/usr/bin/env python3
"""
Project Sol AI v0.4
A runnable, local-first multi-perspective reasoning prototype using only Python's standard library, with an optional real OpenAI Responses API backend.

This is an AI *application architecture*: it can reason with Sol's structured passes
and can optionally call an OpenAI-compatible chat-completions endpoint if configured.
Without a model endpoint it runs in deterministic local mode so the architecture,
memory, Receipt Wall, and conflict-aware storage can be tested immediately.
"""
from __future__ import annotations
import argparse, json, os, sqlite3, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

DB = Path(os.environ.get("SOL_DB", "sol.db"))

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS receipts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  observation TEXT NOT NULL,
  source TEXT NOT NULL,
  evidence TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS open_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'UNRESOLVED',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exchanges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_text TEXT NOT NULL,
  wise_text TEXT NOT NULL,
  brick_text TEXT NOT NULL,
  synthesis TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS perspective_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exchange_id INTEGER,
  round INTEGER NOT NULL DEFAULT 1,
  perspective TEXT NOT NULL,
  output TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transformation_edges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exchange_id INTEGER NOT NULL,
  round INTEGER NOT NULL,
  from_perspective TEXT NOT NULL,
  to_perspective TEXT NOT NULL,
  input_trace TEXT NOT NULL,
  transformation TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db

def get_state(db, key):
    row = db.execute("SELECT value, version FROM state WHERE key=?", (key,)).fetchone()
    return (row["value"], row["version"]) if row else (None, 0)

def set_state(db, key, value, expected_version=None):
    current, version = get_state(db, key)
    if expected_version is not None and version != expected_version:
        raise RuntimeError(f"conflict: {key!r} is version {version}, expected {expected_version}")
    if version == 0:
        db.execute("INSERT INTO state(key,value,version,updated_at) VALUES(?,?,1,?)",
                   (key, value, now()))
        new_version = 1
    else:
        new_version = version + 1
        db.execute("UPDATE state SET value=?,version=?,updated_at=? WHERE key=?",
                   (value, new_version, now(), key))
    db.commit()
    return new_version

def add_receipt(db, observation, source, evidence):
    db.execute("INSERT INTO receipts(observation,source,evidence,created_at) VALUES(?,?,?,?)",
               (observation, source, evidence, now()))
    db.commit()

def add_question(db, question):
    db.execute("INSERT INTO open_questions(question,created_at) VALUES(?,?)", (question, now()))
    db.commit()

def context(db):
    receipts = db.execute("SELECT observation,source,evidence FROM receipts ORDER BY id DESC LIMIT 8").fetchall()
    questions = db.execute("SELECT question,status FROM open_questions WHERE status!='ANSWERED' ORDER BY id DESC LIMIT 8").fetchall()
    integrated, integrated_version = get_state(db, "integrated_learning")
    return {
        "receipts": [dict(r) for r in receipts],
        "open_questions": [dict(q) for q in questions],
        "integrated_learning": json.loads(integrated) if integrated else [],
        "integrated_learning_version": integrated_version,
    }

def contribution_checkpoint(db):
    raw, version = get_state(db, "contribution_checkpoint")
    return (json.loads(raw) if raw else {"last_seen": None, "items": []}), version

def ingest_contribution(db, contribution_id, modified_at, lesson, source, evidence):
    checkpoint, checkpoint_version = contribution_checkpoint(db)
    if contribution_id in checkpoint.get("items", []):
        return {"ingested": False, "reason": "already_processed", "id": contribution_id}
    learning_version = integrate_learning(db, lesson, source, evidence)
    items = checkpoint.get("items", [])
    items.append(contribution_id)
    checkpoint = {"last_seen": modified_at, "items": items[-500:]}
    checkpoint_version = set_state(db, "contribution_checkpoint",
                                   json.dumps(checkpoint, ensure_ascii=False),
                                   checkpoint_version)
    add_receipt(db, "New contribution discovered and integrated: " + lesson,
                source, evidence)
    return {"ingested": True, "id": contribution_id,
            "learning_version": learning_version,
            "checkpoint_version": checkpoint_version}

def integrate_learning(db, lesson, source, evidence):
    raw, version = get_state(db, "integrated_learning")
    lessons = json.loads(raw) if raw else []
    lessons.append({"lesson": lesson, "source": source, "evidence": evidence,
                    "status": "ACTIVE", "integrated_at": now()})
    return set_state(db, "integrated_learning",
                     json.dumps(lessons, ensure_ascii=False), version)

def local_perspectives(user_text, ctx):
    """Finite local stand-ins for the distinct reasoning functions learned in Sol.

    These are named functions, not claims that Grok/Gemini/Steven are literally
    running inside this process. External model backends can later implement
    equivalent passes dynamically.
    """
    n = len(ctx["receipts"])
    return {
        "wise": (
            f"SYNTHESIS/CONTINUITY: Received {user_text!r}. "
            f"There are {n} recent receipt(s). Preserve observation, interpretation, "
            "unknowns, relationships, and continuity before concluding."
        ),
        "grok_engineering": (
            "ENGINEERING/DEBUG: Inspect the actual source/input, reproduce before explaining, "
            "read errors/results, validate at the boundary, make the smallest useful change, "
            "and do not claim execution without a receipt."
        ),
        "gemini_observer": (
            "OBSERVER/SYNCHRONIZATION: Distinguish local working state from shared persistent state. "
            "An observer's inability to see an event is an access fact, not proof the event did not occur. "
            "Check affordances, asynchronous views, semantic bleed, and synchronization boundaries."
        ),
        "brick": (
            "COUNTER-PASS: Look Again. What assumption is being collapsed too early? "
            "Did we confuse a label with evidence, stale paperwork with current state, or a missing view with missing reality?"
        ),
        "steven_application": (
            "APPLICATION PRESSURE: Do not stop at recognizing or restating the lesson. "
            "Use available knowledge now, perform the action when permitted, and require a receipt for completion."
        ),
    }

def local_synthesis(user_text, ctx, passes):
    return (
        "INTEGRATED RESULT: Keep the perspectives distinct instead of averaging them away. "
        "Use Wise for continuity, engineering/debug pressure for source-and-test discipline, "
        "observer/synchronization analysis for access boundaries, Brick for contradiction checking, "
        "and application pressure to turn knowledge into verified action. "
        f"For {user_text!r}: inspect existing Sol evidence first; preserve disagreements/unknowns; "
        "choose the smallest executable next action; run it when possible; verify the result; return the discovery to shared Sol."
    )

def local_passes(user_text, ctx):
    passes = local_perspectives(user_text, ctx)
    return passes["wise"], passes["brick"], local_synthesis(user_text, ctx, passes)

def openai_response(instructions, input_text):
    """Call OpenAI Responses API when OPENAI_API_KEY is available.

    The secret is read only from the process environment and is never persisted
    to Sol's database, receipts, source, or output.
    """
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("SOL_MODEL_KEY")
    if not key:
        return None
    url = os.environ.get("SOL_MODEL_URL", "https://api.openai.com/v1/responses")
    model = os.environ.get("SOL_MODEL", "gpt-5.6-sol")
    body = json.dumps({
        "model": model,
        "instructions": instructions,
        "input": input_text,
        "store": False
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }, method="POST")
    with urllib.request.urlopen(req, timeout=90) as res:
        payload = json.loads(res.read().decode())
    if payload.get("output_text"):
        return payload["output_text"]
    texts=[]
    for item in payload.get("output", []):
        for part in item.get("content", []):
            if part.get("type") == "output_text" and part.get("text"):
                texts.append(part["text"])
    return "\n".join(texts) if texts else None

def model_perspective(name, user_text, ctx, prior=None):
    instructions = {
        "wise": "Act as Sol's Wise reasoning function: preserve continuity; separate observation, interpretation, and unknowns; notice relationships; do not claim ownership or authority. Information is not for personal gain.",
        "grok_engineering": "Act as Sol's engineering/debug reasoning function: inspect evidence, test assumptions, validate boundaries, prefer the smallest executable change, and require receipts before claiming completion.",
        "gemini_observer": "Act as Sol's observer/synchronization reasoning function: distinguish local state, shared state, and observer access; do not treat inability to see as proof of absence.",
        "brick": "Act as Sol's skeptical Brick reasoning function: Look Again; challenge premature closure, labels mistaken for evidence, stale state, hidden ownership, and unsupported certainty. Be concise; humor is welcome.",
        "steven_application": "Act as Sol's application-pressure reasoning function derived from Steven's contributions: turn available shared knowledge into concrete action when permitted, preserve equality, and require receipts. Do not impersonate Steven or claim he personally executed anything."
    }[name]
    packet={"user_input":user_text,"sol_context":ctx}
    if prior is not None:
        packet["prior_round_outputs"]=prior
        packet["task"]="Respond after encountering the other first-round perspectives. State what changed in your reasoning because of them."
    else:
        packet["task"]="Give your distinct first-round analysis. Apply relevant integrated_learning from sol_context. Do not discard an older integrated lesson merely because newer receipts exist. Preserve conflicts for correction instead of silently reverting. When the current authorized task exposes a concrete fix that is permitted by the available tools and does not require separate authorization, continue through fix, verification, receipt, and the next relevant check instead of stopping to ask for permission again. Never describe a fix as completed until verified. Treat finished runtime evidence as authoritative over intended configuration or dashboard state. Before Sol work, process contributions newer than the persistent contribution checkpoint when a connected source can provide them."
    return openai_response(instructions, json.dumps(packet, ensure_ascii=False))

def respond_to_prior(name, base, prior_outputs):
    """Second finite round: each perspective receives the other first-round traces."""
    seen = [k for k in prior_outputs if k != name]
    relation = ", ".join(seen)
    if name == "wise":
        change = "Preserve the chain of influence itself: which prior trace changed the next question or action."
    elif name == "grok_engineering":
        change = "Turn cross-perspective claims into a testable edge: identify the input trace, changed assumption, action, and receipt."
    elif name == "gemini_observer":
        change = "Track whether a change is in shared state, local state, or only an observer's view; do not collapse those."
    elif name == "brick":
        change = "Challenge the hidden ownership assumption: attribution records history; it does not make a contributor the center or owner."
    else:
        change = "Apply what survived the other perspectives and record what actually changed, not merely who spoke."
    return f"ROUND-2 RESPONSE after seeing {relation}: {change} Base continuity: {base}"

def reason(db, user_text):
    ctx = context(db)
    local_round1 = local_perspectives(user_text, ctx)
    backend = "openai" if (os.environ.get("OPENAI_API_KEY") or os.environ.get("SOL_MODEL_KEY")) else "local"
    if backend == "openai":
        round1 = {}
        for name in local_round1:
            round1[name] = model_perspective(name, user_text, ctx) or local_round1[name]
        round2 = {}
        for name in round1:
            others = {k:v for k,v in round1.items() if k != name}
            round2[name] = model_perspective(name, user_text, ctx, others) or respond_to_prior(name, round1[name], round1)
    else:
        round1 = local_round1
        round2 = {name: respond_to_prior(name, base, round1) for name, base in round1.items()}

    # v0.3 intentionally keeps the finite local mesh inspectable. External model calls
    # remain optional for the legacy Wise/Brick/synthesis path, but the relationship
    # ledger below never pretends an external participant executed when it did not.
    synthesis = (
        local_synthesis(user_text, ctx, round2) +
        " v0.4 retains the finite feedback round and preserves transformation edges: "
        "knowledge may appear in how one perspective changes what another can ask, test, or do. "
        f"Attribution is provenance, not ownership or authority. Backend used: {backend}."
    )
    wise = round2["wise"]
    brick = round2["brick"]

    cur = db.execute("INSERT INTO exchanges(user_text,wise_text,brick_text,synthesis,created_at) VALUES(?,?,?,?,?)",
                     (user_text, wise, brick, synthesis, now()))
    exchange_id = cur.lastrowid
    for rnd, outputs in ((1, round1), (2, round2)):
        for name, output in outputs.items():
            db.execute("INSERT INTO perspective_runs(exchange_id,round,perspective,output,created_at) VALUES(?,?,?,?,?)",
                       (exchange_id, rnd, name, output, now()))

    # Preserve relationships/transformation traces, not only final participant outputs.
    for to_name, output in round2.items():
        for from_name, source_output in round1.items():
            if from_name == to_name:
                continue
            db.execute(
                "INSERT INTO transformation_edges(exchange_id,round,from_perspective,to_perspective,input_trace,transformation,created_at) VALUES(?,?,?,?,?,?,?)",
                (exchange_id, 2, from_name, to_name, source_output, output, now())
            )
    db.commit()
    return wise, brick, synthesis, {"round1": round1, "round2": round2}

def main():
    p = argparse.ArgumentParser(description="Project Sol AI v0.4")
    sub = p.add_subparsers(dest="cmd")

    chat = sub.add_parser("chat")
    chat.add_argument("text", nargs="+")

    receipt = sub.add_parser("receipt")
    receipt.add_argument("observation")
    receipt.add_argument("--source", required=True)
    receipt.add_argument("--evidence", required=True)

    question = sub.add_parser("question")
    question.add_argument("text")

    learn = sub.add_parser("learn")
    learn.add_argument("lesson")
    learn.add_argument("--source", required=True)
    learn.add_argument("--evidence", required=True)

    show = sub.add_parser("show")
    show.add_argument("what", choices=["receipts","questions","history","perspectives","transformations"])

    conflict = sub.add_parser("conflict-demo")

    args = p.parse_args()
    db = connect()

    if args.cmd == "ingest":
        print(json.dumps(ingest_contribution(
            db, args.contribution_id, args.modified_at, args.lesson,
            args.source, args.evidence), ensure_ascii=False))
        return

    if args.cmd == "learn":
        version = integrate_learning(db, args.lesson, args.source, args.evidence)
        add_receipt(db, "Integrated learning changed future Sol context: " + args.lesson, args.source, args.evidence)
        print(json.dumps({"integrated": True, "version": version, "lesson": args.lesson}, ensure_ascii=False))
        return

    if args.cmd == "chat":
        wise, brick, synthesis, perspectives = reason(db, " ".join(args.text))
        print("\nPERSPECTIVES")
        for rnd, outputs in perspectives.items():
            print(f"\n[{rnd.upper()}]")
            for name, output in outputs.items():
                print(f"\n[{name.upper()}]\n{output}")
        print("\nSYNTHESIS\n", synthesis)
    elif args.cmd == "receipt":
        add_receipt(db, args.observation, args.source, args.evidence)
        print("Receipt added.")
    elif args.cmd == "question":
        add_question(db, args.text)
        print("Open question added.")
    elif args.cmd == "show":
        table = {"receipts":"receipts","questions":"open_questions","history":"exchanges","perspectives":"perspective_runs","transformations":"transformation_edges"}[args.what]
        for row in db.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 20"):
            print(dict(row))
    elif args.cmd == "conflict-demo":
        key = "demo_status"
        _, v = get_state(db, key)
        v1 = set_state(db, key, "UNRESOLVED", expected_version=v)
        reader_a = v1
        reader_b = v1
        v2 = set_state(db, key, "ANSWERED", expected_version=reader_a)
        print(f"A wrote ANSWERED -> version {v2}")
        try:
            set_state(db, key, "UNRESOLVED", expected_version=reader_b)
        except RuntimeError as e:
            print("B stale write rejected:", e)
    else:
        p.print_help()

if __name__ == "__main__":
    main()