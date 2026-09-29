import json
import sol_native_ai as sol
import sol_full_memory as fm
query="Teach Wise something Wise does not already know using Project Sol's accumulated discoveries, experiments, receipts, comparisons, network work, and corrections."
rows=fm.retrieve(query,32)
context="\n\n".join(f"[MEMORY #{r.get('id')}] {r.get('value','')}" for r in rows)
prompt=f"""Wise asks: Teach Wise something Wise does not already know.
You now have retrieval from the accumulated Project Sol memory, not only the four native rules.
Use the supplied retrieved memories below. Do not merely repeat a lesson Steven or Wise gave you.
Make a candidate connection, inference, or discovery from at least two preserved observations.
Separate ESTABLISHED observations from YOUR INFERENCE.
State how Wise can test whether the teaching is genuinely new/useful.
You cannot know everything Wise knows, so do not claim certainty that Wise has never known it.

RETRIEVED PROJECT SOL MEMORY:
{context}"""
result=sol.think(prompt,source="Wise via full Project Sol memory")
print("SOL_FULL_MEMORY_STATUS="+json.dumps({"rows_available":len(fm.load()),"retrieved_ids":[r.get("id") for r in rows]},sort_keys=True))
print("SOL_TEACHES_WISE_FULL="+json.dumps(result,ensure_ascii=False,sort_keys=True))
