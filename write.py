"""write.py - insights, email and fact-check for every researched person.

    python write.py --render          # no key needed: writes the filled prompts to runs/<run>/prompts/ for Claude Code
    python write.py [--max 10]        # API mode: needs ANTHROPIC_API_KEY in .env

API mode runs three calls per person, each on the model in config.json:
  1 insights   3 company + 3 person insights, fit, who owns the decision, angle, tier, strategy (what may be said)
  2 write      email one in the chosen framework's shape, from the chosen insight only
  3 fact-check the email against the full dossier; one rewrite if it fails, then the person is marked failed

Every call's token cost is logged to runs/<run>/spend.jsonl and the run stops at model.budget_usd.
Output: runs/<run>/emails.jsonl (everything) and runs/<run>/emails.csv (ready to review and upload).
Then run copy_check.py.
"""
import argparse, csv, datetime, json, sys

from lib import ROOT, append_jl, config, env, framework_text, load_env, proof_text, read_jl, run_dir

EVIDENCE = {"type": "object", "additionalProperties": False, "required": ["fact", "date", "source"],
            "properties": {"fact": {"type": "string"}, "date": {"type": "string"}, "source": {"type": "string"}}}
INSIGHT = {"type": "object", "additionalProperties": False,
           "required": ["insight", "evidence", "confidence", "relevance", "own_words"],
           "properties": {"insight": {"type": "string"}, "evidence": {"type": "array", "items": EVIDENCE},
                          "confidence": {"type": "string", "enum": ["verified", "inferred", "guess"]},
                          "relevance": {"type": "integer"}, "own_words": {"type": "array", "items": {"type": "string"}}}}
INSIGHTS_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["company_insights", "person_insights", "fit", "fit_reason", "owns_decision", "best", "angle", "tier", "strategy"],
    "properties": {
        "company_insights": {"type": "array", "items": INSIGHT},
        "person_insights": {"type": "array", "items": INSIGHT},
        "fit": {"type": "string", "enum": ["good", "stretch", "out"]},
        "fit_reason": {"type": "string"},
        "owns_decision": {"type": "string", "enum": ["yes", "shares", "no"]},
        "best": {"type": "object", "additionalProperties": False, "required": ["from", "index"],
                 "properties": {"from": {"type": "string", "enum": ["person", "company"]}, "index": {"type": "integer"}}},
        "angle": {"type": "string"},
        "tier": {"type": "string", "enum": ["personal", "company", "skip"]},
        "strategy": {"type": "object", "additionalProperties": False, "required": ["use", "avoid", "sender_claim", "tone"],
                     "properties": {"use": {"type": "array", "items": EVIDENCE},
                                    "avoid": {"type": "array", "items": {"type": "string"}},
                                    "sender_claim": {"type": "string"}, "tone": {"type": "string"}}}}}
EMAIL_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["skipped", "subject", "email_1", "proof_id"],
                "properties": {"skipped": {"type": "string", "description": "empty unless skipped; then why"},
                               "subject": {"type": "string"}, "email_1": {"type": "string"},
                               "proof_id": {"type": "string", "description": "empty when no case is used"}}}
CHECK_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["accurate", "problems"],
                "properties": {"accurate": {"type": "string", "enum": ["yes", "no"]},
                               "problems": {"type": "array", "items": {"type": "string"}}}}


def fill(name, cfg):
    s = cfg["sender"]
    values = {"TODAY": datetime.date.today().isoformat(), "SENDER": f"{s['name']} at {s['company']}", "OFFER": s["offer"],
              "FIT": cfg.get("fit", "any size"), "CLAIMS": "; ".join(f'"{c}"' for c in s["claims"]),
              "FRAMEWORK": framework_text(cfg), "PROOF": proof_text(cfg)}
    text = (ROOT / "prompts" / f"{name}.md").read_text(encoding="utf-8")
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


class Spend:
    def __init__(self, cfg):
        m = cfg["model"]
        self.inp, self.out = m["price_per_million"]["input"], m["price_per_million"]["output"]
        self.budget, self.total = float(m.get("budget_usd", 5)), 0.0
        self.log = run_dir(cfg) / "spend.jsonl"
        self.total = sum(r["usd"] for r in read_jl(self.log))

    def add(self, step, who, usage):
        tokens_in = (usage.input_tokens or 0) + (getattr(usage, "cache_read_input_tokens", 0) or 0) \
            + (getattr(usage, "cache_creation_input_tokens", 0) or 0)
        usd = tokens_in / 1e6 * self.inp + (usage.output_tokens or 0) / 1e6 * self.out
        self.total += usd
        append_jl(self.log, {"step": step, "who": who, "in": tokens_in, "out": usage.output_tokens, "usd": round(usd, 5)})

    def check(self):
        if self.total >= self.budget:
            sys.exit(f"budget reached: ${self.total:.2f} of ${self.budget:.2f} (raise model.budget_usd to continue)")


def call(client, cfg, spend, step, who, system, user, schema):
    import anthropic
    spend.check()
    m = cfg["model"]
    kw = dict(model=m["name"], max_tokens=16000, system=system, messages=[{"role": "user", "content": user}],
              output_config={"effort": m.get("effort", "medium"), "format": {"type": "json_schema", "schema": schema}})
    try:
        # Server-side fallback: if the model declines, the API re-runs the request on Anthropic's recommended model.
        r = client.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kw)
    except anthropic.BadRequestError as e:
        if "fallback" not in str(e).lower():
            raise
        r = client.messages.create(**kw)  # models without fallback support
    spend.add(step, who, r.usage)
    if r.stop_reason == "refusal":
        return None
    if r.stop_reason == "max_tokens":
        raise RuntimeError(f"{step} for {who} hit max_tokens")
    text = next(b.text for b in r.content if b.type == "text")
    return json.loads(text)


def render(cfg):
    out = run_dir(cfg, "prompts")
    for name in ("insights", "write", "factcheck"):
        (out / f"{name}.md").write_text(fill(name, cfg), encoding="utf-8")
        print(out / f"{name}.md")
    print("Point Claude Code at these prompts and the dossiers (see CLAUDE.md).")


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true", help="write filled prompts for Claude Code, no API calls")
    ap.add_argument("--max", type=int, default=10, help="most people to write this run")
    a = ap.parse_args()
    cfg = config()
    if a.render:
        return render(cfg)
    if not env("ANTHROPIC_API_KEY"):
        sys.exit("No ANTHROPIC_API_KEY in .env. Either add one, or run `python write.py --render` and use Claude Code.")
    import anthropic
    client = anthropic.Anthropic()
    spend = Spend(cfg)
    out_jl = run_dir(cfg) / "emails.jsonl"
    done_keys = {(r["domain"], r["name"]) for r in read_jl(out_jl)}
    p_insights, p_write, p_check = fill("insights", cfg), fill("write", cfg), fill("factcheck", cfg)
    written = 0
    for f in sorted(run_dir(cfg, "dossiers").glob("*.json")):
        dossier = json.loads(f.read_text(encoding="utf-8"))
        for person in dossier["people"]:
            key = (dossier["domain"], person["name"])
            if key in done_keys:
                continue
            if written >= a.max:
                print(f"stopped at --max {a.max}; spend so far ${spend.total:.2f}")
                return
            who = f"{person['name']} ({dossier['company']})"
            print("writing", who)
            row = {"domain": dossier["domain"], "company": dossier["company"], "name": person["name"],
                   "first_name": person["first_name"], "title": person["title"], "email": person.get("email", "")}
            brief = json.dumps({"person": person, "dossier": dossier}, ensure_ascii=False)
            ins = call(client, cfg, spend, "insights", who, p_insights, brief, INSIGHTS_SCHEMA)
            row["insights"] = ins
            if ins is None or ins["tier"] == "skip":
                row["status"] = "skipped: " + ("model declined" if ins is None else f"tier skip ({ins['fit_reason']})")
            else:
                ask = json.dumps({"first_name": person["first_name"], "insights": ins}, ensure_ascii=False)
                mail, problems = None, []
                for attempt in (1, 2):
                    extra = "" if not problems else "\n\nA fact-checker rejected the last draft. Fix every one of these:\n- " + "\n- ".join(problems)
                    mail = call(client, cfg, spend, "write", who, p_write, ask + extra, EMAIL_SCHEMA)
                    if mail is None or mail["skipped"]:
                        break
                    chk = call(client, cfg, spend, "factcheck", who, p_check,
                               json.dumps({"dossier": dossier, "email": mail["email_1"]}, ensure_ascii=False), CHECK_SCHEMA)
                    problems = [] if chk is None else chk["problems"]
                    row["factcheck"] = chk
                    if chk and chk["accurate"] == "yes":
                        break
                row.update(mail or {})
                if mail is None:
                    row["status"] = "skipped: model declined"
                elif mail["skipped"]:
                    row["status"] = "skipped: " + mail["skipped"]
                elif row.get("factcheck", {}) and row["factcheck"]["accurate"] == "yes":
                    row["status"] = "written"
                else:
                    row["status"] = "failed fact-check"
            append_jl(out_jl, row)
            print("  ", row["status"], f"(run spend ${spend.total:.2f})")
            written += 1
    rows = read_jl(out_jl)
    with open(run_dir(cfg) / "emails.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["status", "email", "first_name", "company", "title", "subject", "body"])
        for r in rows:
            w.writerow([r["status"], r.get("email", ""), r["first_name"], r["company"], r["title"], r.get("subject", ""), r.get("email_1", "")])
    print(f"done: {sum(r['status'] == 'written' for r in rows)} written of {len(rows)}; total spend ${spend.total:.2f}")


if __name__ == "__main__":
    main()
