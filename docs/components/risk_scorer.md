# risk_scorer

## What it is
Joins the diff and the usage index together, and produces the final, compact result: a 0–100 risk score, a recommendation, and the specific files affected.

## How it works
Only symbols that are **both** changed **and** actually used matter everything else is discarded at this step, which is what narrows hundreds of real framework changes down to the handful that actually affect a given project.

The score is based mostly on the single worst problem found, with how widespread the issue is as a secondary factor so one serious break can never get lost among trivial changes, and a pile of trivial changes can never add up into a false alarm on their own. Full formula and reasoning: `Risk-Scoring-Mathematical-Model.md`.

Every score points back to one specific symbol as its cause, never just an abstract number.