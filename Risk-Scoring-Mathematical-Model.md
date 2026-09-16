# Risk Scoring Model
How the final 0–100 risk score is calculated from a diff and a usage index.

## Idea
Instead of averaging every detected change, the score is based mostly on the single worst problem found, with how widespread the issue is as a secondary factor. This stops one serious, real break from getting lost among a pile of trivial changes, and also stops a pile of trivial changes from adding up into a false alarm on their own.

## Inputs
- **n**: number of relevant changes, symbols that are both in the diff and used in your code
- **U**: total distinct framework symbols your code uses.

## Severity per category
| Category | Severity |
|---|---|
| `REMOVED` | 1.00 |
| `SIGNATURE_CHANGED` (breaking) | 0.85 |
| `MOVED_ALSO_SIGNATURE_CHANGED` | 0.85 |
| `MOVED_ALSO_BODY_CHANGED` | 0.40 |
| `MOVED_UNCHANGED` | 0.35 |
| `SIGNATURE_CHANGED` (additive) | 0.15 |
| `BODY_CHANGED` | 0.10 |

## Recommendation acc. to Risk Score
| Score | Recommendation | What it means |
|---|---|---|
| 0–19 | `UPGRADE` | Nothing you use is seriously affected |
| 20–59 | `UPGRADE_WITH_CAUTION` | Something worth a quick look, but nothing certain broke |
| 60–100 | `HOLD` | At least one certain, non-mechanical break in something you use |

## Formula used
```
M = highest severity among the relevant changes (0 if none)
B = n / U (0 if U = 0)
score = round(100 * (0.8*M + 0.2*B))
```

The 0.8/0.2 split means your single worst problem drives most of the score. Breadth only nudges it up or down, it can never override a certain break, and it can never manufacture one out of nothing.

---
- **The score can never leaves 0–100**: no clamping needed, since M and B are each already between 0 and 1.
- **One `REMOVED` symbol always pushes the score to at least 80 (HOLD)**, no matter what else is in the diff.
- **If everything found is just `BODY_CHANGED`**, the score can never exceed 28 — not enough alone to trigger `HOLD`, since that's genuinely the lowest-confidence signal (an implementation changed, but the interface didn't).
- **If everything found is a plain move with nothing else changed**, the score can't exceed 48.
- **`HOLD` (score ≥ 60) can only happen if there's at least one `REMOVED` or breaking signature change** in something you actually use — never from a pile of minor issues alone. 
- Alongside the score, the tool always reports the specific symbol that drove `M` (the single worst change found) plus a full breakdown by category (how many changes of each type, and what each contributed).
