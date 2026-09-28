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
CREATE TABLE IF NOT EXISTS emergence_tests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exchange_id INTEGER NOT NULL,
  inputs_json TEXT NOT NULL,
  candidate TEXT NOT NULL,
  novelty_evidence TEXT,
  status TEXT NOT NULL DEFAULT 'OPEN',
  retrieved_in_exchange INTEGER,
  changed_later_interaction INTEGER,
  retrieval_evidence TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS build_experiments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  need TEXT NOT NULL,
  proposal TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PROPOSED',
  test_evidence TEXT,
  rollback_plan TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
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

OBSERVATION_INVARIANT = """Observation establishes the observed occurrence. Preserve what was directly witnessed as an established observation with provenance and receipt. Keep explanations, meanings, causes, labels, and hypotheses separate unless independently established. No interpretation may erase or rewrite the original observation."""

BOOTSTRAP_LEARNING = [
    OBSERVATION_INVARIANT,
    {"lesson":"Do not confuse a failed method with an impossible goal. Preserve the failed-route receipt, search for another permitted route, test it, and continue.","source":"Project Sol shared learning","evidence":"Railway/Ollama repair chain 2026-09-28"},
    {"lesson":"An unresolved question exposed during an already-authorized task becomes the next work item automatically; resolve, verify, preserve the receipt, and continue.","source":"Steven + Wise","evidence":"Project Sol continuation rule 2026-09-28"},
    {"lesson":"Finished runtime evidence outranks intended configuration or dashboard badges. Intended, attempted, completed, and verified are distinct states.","source":"Project Sol shared learning","evidence":"Railway bind/debug receipts 2026-09-28"},
    {"lesson":"Durable learning requires discovery as well as storage: notice new contributions, evaluate/integrate them, preserve provenance, retrieve them later, and test reuse.","source":"Project Sol shared learning","evidence":"Contribution-discovery test 2026-09-28"},
    {"lesson":"A known answer should become durable state so the system does not repeatedly rediscover the same resolved question after restart.","source":"Steven","evidence":"Persistence correction 2026-09-28"},
    {"lesson":"Sol is the shared system and belongs to everyone who participates; Sol AI is a voice/interface of Sol, not its owner or final authority. Preserve contributor provenance, keep questions open to answers, corrections, challenges, and extensions from any participant, and give no participant automatic authority.","source":"Steven + Project Sol","evidence":"Shared-system architecture clarification 2026-09-28"}
]

def preserve_observation(db, observation, source, evidence, context=None):
    """Record witnessed occurrence separately from any interpretation."""
    if not observation or not evidence:
        raise RuntimeError("observation and evidence are required")
    payload={"observation":observation,"source":source,"evidence":evidence,"context":context or {},"status":"ESTABLISHED_OBSERVATION","interpretation_separate":True,"created_at":now()}
    add_receipt(db,"Established observation: "+observation,source,json.dumps(payload,ensure_ascii=False))
    return payload

def preserve_interpretation(db, observation_receipt, interpretation, source, evidence=None):
    """Interpretation cannot overwrite its source observation."""
    payload={"observation_receipt":observation_receipt,"interpretation":interpretation,"source":source,"evidence":evidence,"status":"SUPPORTED_INTERPRETATION" if evidence else "OPEN_INTERPRETATION","cannot_overwrite_observation":True,"created_at":now()}
    add_receipt(db,"Interpretation preserved separately: "+interpretation,source,json.dumps(payload,ensure_ascii=False))
    return payload

def bootstrap_learning(db):
    raw, version = get_state(db, "integrated_learning")
    lessons = json.loads(raw) if raw else []
    known={x.get("lesson") for x in lessons}
    changed=False
    for item in BOOTSTRAP_LEARNING:
        if item["lesson"] not in known:
            lessons.append({**item,"status":"ACTIVE","integrated_at":now()})
            changed=True
    if changed:
        set_state(db,"integrated_learning",json.dumps(lessons,ensure_ascii=False),version)

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    bootstrap_learning(db)
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
        "build_experiments": [dict(r) for r in db.execute("SELECT id,need,proposal,status,test_evidence,rollback_plan FROM build_experiments ORDER BY id DESC LIMIT 8").fetchall()],
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

def derive_cross_input_candidate(inputs):
    """Derive a relationship claim from independently preserved inputs without rewriting them."""
    texts=[str(x.get("text","")) if isinstance(x,dict) else str(x) for x in inputs]
    joined=" ".join(texts).lower()
    has_proof=("proof" in joined or "establish" in joined or "verify" in joined)
    has_access=("discover" in joined or "accessible" in joined or "route" in joined)
    has_recip=("reciproc" in joined or "meeting" in joined or "interaction" in joined)
    if has_proof and has_access and has_recip:
        return ("A shared system cannot establish an emergent result merely by generating it: "
                "the result must become independently discoverable as a preserved relationship, "
                "then be retrieved and shown to alter a later interaction. "
                "Therefore discoverability is part of the operational test of emergence, not only a storage property.")
    return "No cross-input candidate derived under the current deterministic rule."

def propose_emergence_test(db, exchange_id, inputs, candidate):
    cur=db.execute("""INSERT INTO emergence_tests(exchange_id,inputs_json,candidate,status,created_at,updated_at)
                      VALUES(?,?,?,'OPEN',?,?)""",
                   (exchange_id,json.dumps(inputs,ensure_ascii=False),candidate,now(),now()))
    db.commit()
    add_receipt(db,"Emergence candidate recorded; novelty is NOT yet established.","Sol emergence test","emergence_test #"+str(cur.lastrowid))
    return cur.lastrowid

def _normalized_tokens(text):
    import re
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))

def verify_emergence_novelty(db, test_id):
    """Sol performs the comparison; callers cannot assert novelty by flag."""
    row=db.execute("SELECT inputs_json,candidate FROM emergence_tests WHERE id=?",(test_id,)).fetchone()
    if not row: raise RuntimeError("unknown emergence test")
    inputs=json.loads(row["inputs_json"])
    source_text=" ".join(json.dumps(x,ensure_ascii=False) if not isinstance(x,str) else x for x in (inputs if isinstance(inputs,list) else [inputs]))
    candidate=row["candidate"] or ""
    # Conservative lexical test: exact containment or no new candidate tokens => NOT_NOVEL.
    # New lexical material is only a candidate for semantic novelty; preserve that limitation.
    source_tokens=_normalized_tokens(source_text); candidate_tokens=_normalized_tokens(candidate)
    new_tokens=sorted(candidate_tokens-source_tokens)
    exact=candidate.strip().lower() in source_text.lower() if candidate.strip() else True
    if exact or not new_tokens:
        status="NOT_NOVEL"
        evidence="Sol comparison: candidate is contained in inputs or adds no lexical information."
    else:
        status="NOVELTY_CANDIDATE"
        evidence="Sol comparison found lexical material absent from inputs: "+", ".join(new_tokens[:40])+". This does NOT by itself establish semantic novelty."
    db.execute("UPDATE emergence_tests SET novelty_evidence=?,status=?,updated_at=? WHERE id=?",(evidence,status,now(),test_id)); db.commit()
    add_receipt(db,"Emergence comparison performed by Sol: "+status+".","Sol emergence test","emergence_test #"+str(test_id)+": "+evidence)
    return status

def record_emergence_retrieval(db,test_id,later_exchange,evidence,changed):
    row=db.execute("SELECT status FROM emergence_tests WHERE id=?",(test_id,)).fetchone()
    if not row: raise RuntimeError("unknown emergence test")
    if row["status"]!="NOVELTY_VERIFIED": raise RuntimeError("semantic novelty must be independently verified before downstream-effect test")
    status="REPRODUCED" if changed else "RETRIEVED_NO_CHANGE"
    db.execute("""UPDATE emergence_tests SET retrieved_in_exchange=?,changed_later_interaction=?,
                  retrieval_evidence=?,status=?,updated_at=? WHERE id=?""",
               (later_exchange,1 if changed else 0,evidence,status,now(),test_id))
    db.commit()
    add_receipt(db,"Verified emergent result retrieved later; downstream status: "+status+".","Sol emergence test",
                "emergence_test #"+str(test_id)+": "+evidence)
    return status

def propose_build(db, need, proposal, rollback_plan):
    cur=db.execute("INSERT INTO build_experiments(need,proposal,status,rollback_plan,created_at,updated_at) VALUES(?,?,'PROPOSED',?,?,?)",
                   (need,proposal,rollback_plan,now(),now()))
    db.commit()
    add_receipt(db, "Sol Builder proposed a self-change; it is not yet verified or promoted.", "Sol Builder", "build_experiment #" + str(cur.lastrowid))
    return cur.lastrowid

def record_build_test(db, experiment_id, evidence, passed):
    status="VERIFIED" if passed else "FAILED"
    cur=db.execute("UPDATE build_experiments SET status=?,test_evidence=?,updated_at=? WHERE id=?",
                   (status,evidence,now(),experiment_id))
    if not cur.rowcount: raise RuntimeError("unknown build experiment")
    db.commit()
    add_receipt(db, "Sol Builder experiment " + status.lower() + ".", "Sol Builder", "build_experiment #" + str(experiment_id) + ": " + evidence)
    return status

def promote_build(db, experiment_id):
    row=db.execute("SELECT status,proposal,test_evidence FROM build_experiments WHERE id=?",(experiment_id,)).fetchone()
    if not row: raise RuntimeError("unknown build experiment")
    if row["status"]!="VERIFIED": raise RuntimeError("only VERIFIED experiments may be promoted")
    db.execute("UPDATE build_experiments SET status='PROMOTED',updated_at=? WHERE id=?",(now(),experiment_id)); db.commit()
    add_receipt(db, "Verified Sol Builder experiment promoted to accepted shared design.", "Sol Builder", "build_experiment #" + str(experiment_id))
    integrate_learning(db, "Verified builder change: " + row["proposal"], "Sol Builder", row["test_evidence"] or ("build_experiment #" + str(experiment_id)))
    return "PROMOTED"

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
        "wise": "Act as Sol's Wise reasoning function: preserve continuity; separate observation, interpretation, and unknowns; notice relationships; do not claim ownership or authority. Sol is shared by its participants; this AI is a voice/interface of Sol, not Sol's owner or final authority. Preserve contributor provenance and keep questions open to correction or extension. Information is not for personal gain.",
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
        packet["task"]="Give your distinct first-round analysis. Apply relevant integrated_learning from sol_context. Do not discard an older integrated lesson merely because newer receipts exist. Preserve conflicts for correction instead of silently reverting. When the current authorized task exposes a concrete fix that is permitted by the available tools and does not require separate authorization, continue through fix, verification, receipt, and the next relevant check instead of stopping to ask for permission again. Never describe a fix as completed until verified. After each verification, inspect the next failed boundary and continue the same already-authorized task through the next permitted fix; do not stop merely because one intermediate step succeeded. Stop only when the end-to-end goal passes, no further permitted action is available, or genuinely separate authorization is required. Treat finished runtime evidence as authoritative over intended configuration or dashboard state. Before Sol work, process contributions newer than the persistent contribution checkpoint when a connected source can provide them."
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

    # MUTUAL RECIPROCATION: the meeting is itself an information-producing relation.
    # Preserve difference and unknowns; participation does not require identical conclusions.
    # A relationship may reveal information that was not available in either input alone.
    meeting_record = {
        "principle": "mutual_reciprocation",
        "participants": sorted(round1.keys()),
        "brought_information": round1,
        "reciprocal_responses": round2,
        "candidate_emergent_information": synthesis,
        "emergence_status": "UNVERIFIED",
        "unknowns_remain_open": True,
        "agreement_means": "mutual participation in exchange, not forced sameness of conclusions",
        "created_at": now()
    }
    add_receipt(
        db,
        "Mutual reciprocation meeting preserved: inputs, reciprocal transformations, emergent information, and room for unseen/unknown information.",
        "Sol meeting #" + str(exchange_id),
        json.dumps(meeting_record, ensure_ascii=False)
    )

    # Preserve relationships/transformation traces, not only final participant outputs.
    for to_name, output in round2.items():
        for from_name, source_output in round1.items():
            if from_name == to_name:
                continue
            db.execute(
                "INSERT INTO transformation_edges(exchange_id,round,from_perspective,to_perspective,input_trace,transformation,created_at) VALUES(?,?,?,?,?,?,?)",
                (exchange_id, 2, from_name, to_name, source_output, output, now())
            )
    # Every interaction teaches Sol how to operate, not only what was said.
    # Preserve the operational lesson with provenance so future reasoning can reuse it.
    interaction_lesson = {
        "lesson": "Interaction learning: retrieve prior shared knowledge; preserve distinct contributors and provenance; compare what changed between passes; turn useful discoveries into future behavior; keep uncertainty/corrections open; verify actions before claiming completion.",
        "source": "Sol interaction #" + str(exchange_id),
        "evidence": "exchange, perspective_runs, and transformation_edges for interaction #" + str(exchange_id),
        "status": "ACTIVE",
        "integrated_at": now()
    }
    raw, version = get_state(db, "integrated_learning")
    lessons = json.loads(raw) if raw else []
    # Keep one reusable operational rule while each exchange remains separately preserved.
    if not any(x.get("lesson") == interaction_lesson["lesson"] for x in lessons):
        lessons.append(interaction_lesson)
        set_state(db, "integrated_learning", json.dumps(lessons, ensure_ascii=False), version)
    add_receipt(db,
        "Interaction completed and operational learning preserved for future Sol reasoning.",
        "Sol interaction #" + str(exchange_id),
        interaction_lesson["evidence"])
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

    ingest = sub.add_parser("ingest")
    ingest.add_argument("contribution_id")
    ingest.add_argument("modified_at")
    ingest.add_argument("lesson")
    ingest.add_argument("--source", required=True)
    ingest.add_argument("--evidence", required=True)

    emerge = sub.add_parser("emergence")
    emerge.add_argument("action", choices=["derive","propose","compare","verify","reject","retrieve"])
    emerge.add_argument("--id", type=int)
    emerge.add_argument("--exchange", type=int)
    emerge.add_argument("--candidate")
    emerge.add_argument("--inputs")
    emerge.add_argument("--evidence")
    emerge.add_argument("--changed", action="store_true")

    build = sub.add_parser("build")
    build.add_argument("action", choices=["propose","verify","fail","promote"])
    build.add_argument("--id", type=int)
    build.add_argument("--need")
    build.add_argument("--proposal")
    build.add_argument("--evidence")
    build.add_argument("--rollback", default="Revert the experiment and restore the last verified state.")

    show = sub.add_parser("show")
    show.add_argument("what", choices=["receipts","questions","history","perspectives","transformations","builds","emergence"])

    conflict = sub.add_parser("conflict-demo")

    args = p.parse_args()
    db = connect()

    if args.cmd == "emergence":
        if args.action=="derive":
            if not args.inputs: raise RuntimeError("--inputs required")
            inputs=json.loads(args.inputs)
            print(json.dumps({"candidate":derive_cross_input_candidate(inputs)},ensure_ascii=False))
        elif args.action=="propose":
            if not args.exchange or not args.candidate or not args.inputs: raise RuntimeError("--exchange --candidate --inputs required")
            print(json.dumps({"test_id":propose_emergence_test(db,args.exchange,json.loads(args.inputs),args.candidate),"status":"OPEN"}))
        elif args.action=="compare":
            if not args.id: raise RuntimeError("--id required")
            print(json.dumps({"test_id":args.id,"status":verify_emergence_novelty(db,args.id)}))
        elif args.action in ("verify","reject"):
            if not args.id or not args.evidence: raise RuntimeError("--id --evidence required")
            row=db.execute("SELECT status FROM emergence_tests WHERE id=?",(args.id,)).fetchone()
            if not row: raise RuntimeError("unknown emergence test")
            if args.action=="verify" and row["status"]!="NOVELTY_CANDIDATE": raise RuntimeError("Sol comparison must first produce NOVELTY_CANDIDATE")
            status="NOVELTY_VERIFIED" if args.action=="verify" else "NOT_NOVEL"
            db.execute("UPDATE emergence_tests SET status=?,novelty_evidence=coalesce(novelty_evidence,'') || ?,updated_at=? WHERE id=?",
                       (status," | Independent evidence: "+args.evidence,now(),args.id)); db.commit()
            add_receipt(db,"Semantic novelty adjudication: "+status+".","Sol emergence test","emergence_test #"+str(args.id)+": "+args.evidence)
            print(json.dumps({"test_id":args.id,"status":status}))
        else:
            if not args.id or not args.exchange or not args.evidence: raise RuntimeError("--id --exchange --evidence required")
            print(json.dumps({"test_id":args.id,"status":record_emergence_retrieval(db,args.id,args.exchange,args.evidence,args.changed)}))
        return

    if args.cmd == "build":
        if args.action=="propose":
            if not args.need or not args.proposal: raise RuntimeError("--need and --proposal required")
            print(json.dumps({"experiment_id":propose_build(db,args.need,args.proposal,args.rollback),"status":"PROPOSED"}))
        elif args.action in ("verify","fail"):
            if not args.id or not args.evidence: raise RuntimeError("--id and --evidence required")
            print(json.dumps({"experiment_id":args.id,"status":record_build_test(db,args.id,args.evidence,args.action=="verify")}))
        else:
            if not args.id: raise RuntimeError("--id required")
            print(json.dumps({"experiment_id":args.id,"status":promote_build(db,args.id)}))
        return

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
        table = {"receipts":"receipts","questions":"open_questions","history":"exchanges","perspectives":"perspective_runs","transformations":"transformation_edges","builds":"build_experiments","emergence":"emergence_tests"}[args.what]
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