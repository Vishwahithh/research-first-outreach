Optional, free, no scraping: paste what a person has said publicly into `notes/<domain>.md`, one item per block,
each starting with its date and where it came from:

    2026-09-21 | LinkedIn post
    Intelligence is getting commoditised fast. Regulated infrastructure isn't.

    2026-08-04 | podcast, Example Show
    We price per seat today and it is starting to hurt our biggest accounts.

research.py reads these as the own words of the first person listed for that domain in leads.csv. Undated items are ignored.
