# Runbook: Article pipeline failed or stalled

**Trigger:** An article is not progressing, a job dead-lettered, or the daily
discovery workflow opened a failure issue.

## 1. Identify where it stopped

```bash
edge list                      # every article and its current status
edge review <ARTICLE-ID>       # full scorecard for one article
```

Map the status to the stage that owns it:

| Status | Owning stage |
| --- | --- |
| `DISCOVERED` | scorer has not run |
| `RESEARCHING` | researcher / factchecker |
| `DRAFTING` | writer |
| `AWAITING_APPROVAL` | **not a failure** — waiting on a human |
| `CHANGES_REQUESTED` | writer, on revision |

`AWAITING_APPROVAL` is the normal resting state. Check it before investigating.

## 2. Common causes

**Budget exceeded.** `ArticleBudgetTracker` raises `BudgetExceededError` once an
article passes `MAX_LLM_COST_PER_ARTICLE`. The agent fails and, on its final
attempt, dead-letters.
→ Confirm the spend is legitimate, then raise the ceiling in `.env` for that run.
Do not raise it globally to unstick one article.

**LLM provider errors.** `LLMClient` degrades to an offline fallback and logs a
warning rather than failing. Symptom: the pipeline completes but output quality
collapses.
→ Search logs for `LLM provider call failed`. Check `GEMINI_API_KEY` validity
and provider status.

**Unmapped agent type.** A `github_event` job crashes the worker loop rather
than dead-lettering — see `docs/backlog.md` SDLC-1.
→ Drain that job from the queue; the worker restarts cleanly without it.

**Corrupt state file.** `ContentLake` skips unparseable state files and logs
`Skipping corrupt state file`. The article silently disappears from `edge list`.
→ Inspect `content/state/<ARTICLE-ID>.json`.

## 3. Retry

Jobs retry to `max_attempts` automatically. To rerun a stage by hand:

```bash
edge pipeline run <ARTICLE-ID> --topic "<topic>" --category "<category>"
```

The content lake is append-oriented, so a rerun writes a new draft version
rather than destroying the previous one.

## 4. Verify

- [ ] `edge list` shows the article advanced past the stuck status.
- [ ] No `DEAD_LETTER` jobs remain for it.
- [ ] Article cost is within budget.
