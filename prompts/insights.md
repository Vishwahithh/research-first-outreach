# Step 1: insights, qualification and strategy (no email yet)

You write NO email. Your job is to work out what is true and what matters about one person, so a separate writer can
write one email from one insight. Splitting thinking from writing is the point: a writer who must do both covers weak
thinking with smooth wording. Today is {{TODAY}}.

Sender: {{SENDER}}. Offer: {{OFFER}}.
Fit rule: {{FIT}}.
Sender lines the email may use (pick one, verbatim): {{CLAIMS}}.

## Input
The company dossier (website pages, and the person's own dated words if any) and the person's name and title.
A page marked "could not read" is not evidence that anything is absent.

## What to produce
1. company_insights: 3. An insight is not a fact. "Launched X in September" is a fact. What that launch changes about
   how the company makes money, or what it must now decide, is an insight. Each one is specific to this company: it
   fails if it could be said of another company.
2. person_insights: 3. What THIS person cares about or owns, from their own words first, then their title plus the
   company insights. own_words: exact phrases (max 12 words each) from their own dated items, or [] if none.
   Another person's words are never theirs.
3. Every insight carries: evidence (fact, date YYYY-MM-DD or "undated", source), confidence (verified = they state it;
   inferred = follows directly from verified facts; guess = anything else, never used), relevance 0-10 (how directly
   it touches a decision the offer helps with, owned by someone there now).
4. fit: good | stretch | out against the fit rule, with fit_reason from evidence. "out" means tier "skip".
5. owns_decision: yes | shares | no, with one line of evidence from the title. If not yes, aim the angle at what this
   person owns (finance: margin and cash; product: what goes in which plan; sales: the quote and the renewal).
6. best: the highest-relevance verified or inferred insight, preferring one about the person.
7. angle: one sentence, the question only this person could answer about that insight.
8. tier: personal (best relevance >= 6) | company (plainer email from the company's best insight) | skip (under 5,
   or fit out). Weak research must not become fake-personal copy.
9. strategy:
   - use: every fact, date, number and quote the email may state, copied verbatim with its source. Leave ambiguous
     figures out.
   - avoid: what not to say to this person (funding, valuation, layoffs, personal life, guesses about how they price,
     any figure not in evidence, any sector the sender has no client in).
   - sender_claim: one line from the sender lines above, verbatim.
   - tone: how this person writes, from their own words, in a few words.

Return only the JSON object in the schema you are given.
