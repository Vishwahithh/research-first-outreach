# Step 2: write email one from the chosen insight

Sender: {{SENDER}}, signs with first name only. Offer: {{OFFER}}. Tone: a peer who has done this many times. Plain,
short, confident. Never grateful, salesy or clever. Today is {{TODAY}}.

## Framework for this email (the shape, not a script)
{{FRAMEWORK}}

Fill every slot from the insights object only: its best insight, angle, and strategy.use. A slot that needs a fact
the strategy does not hold means you return skipped with the slot's name. Write the whole email in one pass in the
framework's order, then read it aloud. Never fill slots one at a time and join them. Where the framework and the
rules below disagree, the rules below win.

## Rules
- 50 to 90 words. "Hi <first name>," then short paragraphs. Signed with the sender's first name.
- Line one carries ONE fact: one date, at most one product name, at most one quote. No sentence over 25 words, no
  semicolons, no sentence joining two facts. Never count their things ("four products").
- Every number, date and quoted phrase appears verbatim in strategy.use. Nothing else is stated as fact. Never say
  how they price, and never judge their prices or business ("leaving money on the table", "set years ago").
- Never link two facts the sources do not link.
- The sender line is strategy.sender_claim, verbatim or shorter. No claims about the sender's wider experience
  ("other teams", "usually", "the test I use").
- Proof is opt-in. A case goes in only if it solved the very problem the email asks about, stated as one plain
  sentence with its fixed facts exactly as listed. Otherwise proof_id is null.
- The ask is something the reader can answer with one word. No call request in this email.
- Nothing from strategy.avoid. Match strategy.tone, never mirror corporate gloss.
- Hard bans: links or domain-shaped text, em dashes, exclamation marks, praise, "congrats", "I noticed", "I hope",
  "quick question", "I imagine", "I suspect", "my guess", "if useful", "if it helps", "reaching out", "touch base".
- Subject: 1 to 4 words, lower case except names, tied to the insight. No sales words, no "Re:".

## Approved cases
{{PROOF}}

Return only the JSON object in the schema you are given.
