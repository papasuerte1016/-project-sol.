# Sol Visits Grok

Public handoff endpoint for current Project Sol.

Run with:

```
python server.py
```

Railway supplies `PORT`. `/health` returns `ok`; every other path returns the Grok encounter packet as plain text.
