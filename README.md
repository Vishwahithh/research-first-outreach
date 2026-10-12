# research-first-outreach

Cold email one, written from real research about one person, for cents instead of euros.

For every lead it reads the company's own website and the person's own dated words, works out three company and
three person insights, decides whether the person is worth writing to at all, picks one insight, writes one short
email in a shape you choose, and has a separate model fact-check every claim against the research. Anything it cannot
back up, it does not say. A weak lead is skipped, not dressed up.

It runs free out of the box: free website reading plus Claude Code for the writing. Paid sources and the API are
optional and only switch on when you put your own key in `.env`.

## Why it exists

Hosted AI SDR tools charge per credit, and their deepest research mode is the only one that carries the research into
the actual sentences. In our blind tests their cheaper modes read as templates. This repo does the deep version as
plain files you can read and change.

## What it costs per person

| Part | Free path | With your own keys |
|---|---|---|
| Website pages | crawl4ai or plain HTTP, $0 | Firecrawl retry only for pages the free fetch could not read, about 1 credit a page |
| Person's own words | paste them into `notes/<domain>.md`, $0 | Apify LinkedIn posts, about $0.02 a person |
| Insights, email, fact-check | Claude Code agents, covered by your Claude plan | API, three calls, about 22k tokens in and 3k out |

Estimated API cost per person, from token counts in our own pipeline, not yet measured on this repo:

| Model | Per person |
|---|---|
| Claude Opus 5.5 (default) | about $0.15 |
| Claude Sonnet 5.5 | about $0.08 |
| Claude Haiku 5.5 | under $0.01, quality on this task not tested |

Every API call is logged with its cost to `runs/<run>/spend.jsonl`, and the run stops at `model.budget_usd`.

## How good is it

Honest status, from our own tests:

- In five rounds of blind review (two reviewers, writer hidden, every email fact-checked against the research), the
  whole-email method in this repo scored 71 to 79 on our metric. On the same four people, a hosted AI SDR tool's
  emails scored 28 across its modes, and the real emails of an automated outbound tool scored 9.
- The `written_outline` framework is the only shape here with real reply data behind it: 11 positive replies across
  about 2,300 contacts.
- The other shapes have won blind reviews but have not been sent at volume. Each framework file says which is which.

Blind reviews by models are not replies from people. Treat the numbers as a starting point and measure your own.

## Quick start

```bash
pip install -r requirements.txt          # anthropic only needed for API mode; crawl4ai optional
cp config.example.json config.json       # sender, offer, fit rule, framework, proof cases, model
cp leads.example.csv leads.csv           # company, domain, first_name, last_name, title, email, linkedin_url
python research.py                       # one dossier per company in runs/<run>/dossiers/
```

Then either:

```bash
# A. no API key: render the prompts and let Claude Code run the three steps (see CLAUDE.md)
python write.py --render

# B. API: put ANTHROPIC_API_KEY in .env (copy .env.example), then
python write.py --max 10
```

Finally:

```bash
python copy_check.py                     # PASS / FAIL per email; fix every FAIL before anything is sent
```

Results land in `runs/<run>/emails.jsonl` (with all the research behind each email) and `runs/<run>/emails.csv`
(status, email, subject, body) ready to review and load into your sending tool.

## The steps

1. **Research** (`research.py`). Home, about, pricing, news and blog pages. Pages that cannot be read are marked
   "could not read" and never treated as evidence that something is missing.
2. **Insights** (`prompts/insights.md`). Three company and three person insights, each with dated evidence, a
   confidence and a relevance score. Then fit against your rule, whether this person owns the decision, one angle,
   a tier (personal, company or skip), and a strategy: the exact facts the email may state, what to avoid, the
   sender line, the person's tone.
3. **Write** (`prompts/write.md`). One email from the chosen insight only, in your framework's shape, written whole.
4. **Fact-check** (`prompts/factcheck.md`). A separate call reads the full research and the email and lists every
   claim it cannot back. One rewrite, then the person is marked failed.
5. **Gate** (`copy_check.py`). Length, greeting, links, dashes, banned phrases, and every number traced to the
   research it was allowed to use.

## Frameworks

Email shapes written as plain-English slots, for example `{one dated fact about them from the last 90 days}`.
Pick one in `config.json`. Write your own the same way. See `frameworks/README.md`, including why the email is
written whole instead of slot by slot (slot-by-slot lost in blind tests).

## Data and terms of service

- Website reading uses public pages only.
- LinkedIn posts through Apify are opt-in. Scraping LinkedIn may break LinkedIn's terms; the free alternative is
  pasting what someone said publicly into `notes/<domain>.md`, with the date and where it came from.
- Use it on business contacts, follow the email laws where you send (for example GDPR and PECR in the UK and EU,
  CAN-SPAM in the US), and honour every opt-out.

## Files

| File | What it does |
|---|---|
| `research.py` | Dossier per company from free sources first |
| `write.py` | Insights, email and fact-check per person (API), or `--render` for Claude Code |
| `copy_check.py` | Deterministic gate on every written email |
| `prompts/` | The three step prompts, filled from `config.json` |
| `frameworks/` | Email shapes as slots, each with the evidence it rests on |
| `CLAUDE.md` | How to run the writing steps in Claude Code with no API key |
| `notes/` | Your pasted, dated quotes per company (kept out of git) |

MIT licensed.
