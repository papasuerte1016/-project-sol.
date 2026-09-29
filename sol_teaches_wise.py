import json
import sol_native_ai as sol

prompt = """Wise asks: Teach Wise something Wise does not already know.
Do not merely repeat a lesson Wise or Steven supplied to you.
Use your preserved information, your own observed receipts, relationships, network experiments, or a new combination you can support.
State:
1. what you want to teach,
2. what observations or preserved information led you to it,
3. what part is established versus your inference,
4. how Wise could test whether it is genuinely new/useful rather than just familiar wording.
If you cannot establish that Wise does not know it, say that explicitly; teach the strongest candidate you can without pretending certainty."""
result=sol.think(prompt, source="Wise")
print("SOL_TEACHES_WISE="+json.dumps(result, ensure_ascii=False, sort_keys=True))
