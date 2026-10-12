"""copy_check.py - deterministic gate on every written email, before a person reads them.

    python copy_check.py

Per email: 50-90 words; greeting "Hi <first name>,"; no links or domain-shaped text, em dashes, exclamation marks or
banned phrases; every number in the email appears in the research it was allowed to use (strategy.use) or in the
chosen case's fixed facts; the chosen case's fixed facts all appear; subject 1-4 words with no sales words.
Writes runs/<run>/copy_check.csv and prints PASS / FAIL per email. Fix every FAIL before anything is sent.
"""
import csv, re

from lib import config, read_jl, run_dir

BANNED = ["congrat", "impressive", "great ", "exciting", "i hope", "quick question", "i imagine", "i suspect", "my guess",
          "just checking", "reaching out", "touch base", "leverage", "synerg", "i'm curious", "i noticed", "if useful",
          "if it helps", "same question", "had the same", "faced the same", "other teams", "other platforms",
          "leaving money", "on the table", "never revisited", "teardown", "diagnostic"]
SUBJECT_BAN = ["offer", "discount", "free", "deal", "urgent", "re:", "fwd:", "!"]
DOMAIN = re.compile(r"\b[\w-]+\.(com|co|io|ai|net|org|uk|app|dev)\b|https?://|www\.", re.I)


def check(r, cfg):
    f, e, subj = [], r.get("email_1") or "", r.get("subject") or ""
    banned = BANNED + [b.lower() for b in cfg.get("extra_banned_phrases", [])]
    n = len(re.findall(r"[A-Za-z0-9'%$.]+", e))
    if not 50 <= n <= 90:
        f.append(f"{n} words")
    if not e.startswith(f"Hi {r.get('first_name', '')},"):
        f.append("greeting is not 'Hi <first name>,'")
    if DOMAIN.search(e):
        f.append("link or domain")
    if "—" in e or "–" in e:
        f.append("dash")
    if "!" in e:
        f.append("exclamation mark")
    f += [f"banned '{b.strip()}'" for b in banned if b in e.lower()]
    allowed = " ".join(u["fact"] for u in (r.get("insights") or {}).get("strategy", {}).get("use", []))
    proof = {p["id"]: p for p in cfg.get("proof", [])}
    case = proof.get(r.get("proof_id") or "")
    if r.get("proof_id") and not case:
        f.append(f"unknown proof_id {r['proof_id']}")
    if case:
        allowed += " " + " ".join(case.get("facts", [])) + " " + case["line"]
        f += [f"case fact missing '{x}'" for x in case.get("facts", []) if x not in e]
    for num in re.findall(r"\d[\d,.]*%?", e):
        if num.rstrip(".,") not in allowed:
            f.append(f"number '{num}' not in the allowed research")
    sw = len(subj.split())
    if not 1 <= sw <= 4:
        f.append(f"subject {sw} words")
    f += [f"subject uses '{b}'" for b in SUBJECT_BAN if b in subj.lower()]
    return f


def main():
    cfg = config()
    rows = [r for r in read_jl(run_dir(cfg) / "emails.jsonl") if r.get("status") == "written"]
    out = []
    for r in rows:
        issues = check(r, cfg)
        out.append({"company": r["company"], "name": r["name"], "result": "FAIL" if issues else "PASS", "issues": "; ".join(issues)})
        print(f"{out[-1]['result']:4} {r['company'][:24]:24} {r['name'][:24]:24} {out[-1]['issues']}")
    with open(run_dir(cfg) / "copy_check.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["company", "name", "result", "issues"])
        w.writeheader()
        w.writerows(out)
    print(f"\n{sum(o['result'] == 'PASS' for o in out)} pass / {sum(o['result'] == 'FAIL' for o in out)} fail")


if __name__ == "__main__":
    main()
