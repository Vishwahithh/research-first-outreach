# Running this repo inside Claude Code (no API key)

The writing steps can run as Claude Code agents instead of API calls. Same prompts, same output, same gate.

1. `python research.py` builds `runs/<run>/dossiers/<domain>.json`.
2. `python write.py --render` writes the filled prompts to `runs/<run>/prompts/` (insights, write, factcheck).
3. For each person in each dossier, run three agents in order. Batch up to 5 people per agent.
   - Insights agent: reads `runs/<run>/prompts/insights.md` and the dossier. Returns the insights JSON object
     (fields listed in `write.py` INSIGHTS_SCHEMA). Reads the dossier itself; no keyword scripts.
   - Writer agent: reads `runs/<run>/prompts/write.md` and ONLY that person's insights object, never the dossier.
     Returns {skipped, subject, email_1, proof_id}.
   - Fact-check agent: a fresh agent that did not write the email. Reads `runs/<run>/prompts/factcheck.md`, the full
     dossier and the email. Returns {accurate, problems}. If "no", send the problems back to a writer once; a second
     "no" marks the person "failed fact-check".
4. Append one line per person to `runs/<run>/emails.jsonl`, in the shape `write.py` writes: domain, company, name,
   first_name, title, email, insights, subject, email_1, proof_id, factcheck, status ("written", "skipped: <why>" or
   "failed fact-check").
5. `python copy_check.py`. Fix every FAIL before a person reads the emails.

Rules for every agent: state nothing the dossier does not hold; a page marked "could not read" is not evidence;
NOT FOUND is a valid answer; a weak person gets tier "skip", never fake-personal copy.
