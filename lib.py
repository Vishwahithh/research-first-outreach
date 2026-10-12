"""lib.py - shared helpers: config, .env, run folders, JSON lines. No third-party imports."""
import json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent


def load_env():
    """Read .env into os.environ without overriding variables already set. Missing file is fine."""
    p = ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def env(name):
    return os.environ.get(name, "").strip()


def config():
    p = ROOT / "config.json"
    if not p.exists():
        sys.exit("config.json not found: copy config.example.json to config.json and edit it")
    return json.loads(p.read_text(encoding="utf-8"))


def run_dir(cfg, *parts):
    d = ROOT / "runs" / cfg["run"]
    for part in parts:
        d = d / part
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_jl(path):
    p = pathlib.Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def append_jl(path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def framework_text(cfg):
    name = cfg.get("framework")
    if not name:
        return "None chosen: three short paragraphs, one fact, one question, one ask."
    f = ROOT / "frameworks" / f"{name}.md"
    if not f.exists():
        sys.exit(f"framework '{name}' not found in frameworks/")
    return f.read_text(encoding="utf-8").strip()


def proof_text(cfg):
    rows = []
    for p in cfg.get("proof", []):
        if p["line"].startswith("REPLACE"):
            continue
        rows.append(f"- {p['id']}: {p['line']}\n  use only when the question is about: {p.get('solves', '')}"
                    + (f"\n  fixed facts, must appear exactly: {', '.join(p['facts'])}" if p.get("facts") else ""))
    return "\n".join(rows) or "No approved cases. proof_id must be null."
