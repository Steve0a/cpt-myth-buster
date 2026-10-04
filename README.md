# CPT Myth-Buster

**Live:** https://cptmythbuster.steveoamo960.workers.dev

An AI-assisted CPT (Curricular Practical Training) guide for F-1 international students. It answers common questions with official sources, refuses to guess when the rules don't cover a question, and checks CPT news against the official rules with a human reviewing every label. Built by Steve O. as part of the Park Career Toolkit.

> Educational information only, not legal advice. For official CPT rules and news, rely on [USCIS](https://www.uscis.gov) and DHS's [Study in the States](https://studyinthestates.dhs.gov) (the SEVP program that oversees CPT). Always confirm with your DSO.

## Features

- **Chat Q&A:** 25 sourced questions and 28 myths, each with an official quote and link.
- **Smart search (ML):** sentence embeddings (bge-small) run in the browser to match questions by meaning.
- **Gemini fallback (LLM):** when search can't match, Gemini answers only from saved official text; every quote is verified word for word.
- **CPT news check:** daily news collection, Gemini claim-by-claim labeling, human approval before publishing.
- **AI quality page:** test-set accuracy, fallback safety check, Gemini vs. human agreement, own classifier vs. baseline.
- **Aug 2026 update, tools and email updates:** SEVP guidance summary, OPT safety check, offer-letter checklist, recruiter scripts, signup.

## Results so far

| Measure | Result |
|---|---|
| Right answer first, 55-question test set | 84% (keyword matching: 40%) |
| Right answer in top 3 | 96% |
| Off-topic questions refused | 5/5 |
| Unverified quotes shown to users | 0 (1 blocked in testing) |

The test questions were written by the builder, so real-world accuracy may be lower. See the AI quality page for details.

## Repository

```
public/            Website (index.html, kb_emb.json, news.json, ai_report.json)
worker/index.js    Cloudflare Worker: serves public/ and POST /api/ask (Gemini fallback)
wrangler.jsonc     Cloudflare config
scripts/           News collection, Gemini labeling, approval, classifier, embeddings, test set
backend/           Python version of the Gemini logic (used by scripts)
official/          Saved official source text used for grounding
review/            News stories waiting for human review
prd/               Product requirements document
design-system/     Design tokens and components
wireframes/        Low-fidelity wireframes of every screen
.github/workflows/ Daily CPT news check
```

## Deploy

1. Cloudflare: Workers & Pages > connect this repo (or run `npx wrangler deploy`). Add the secret `GEMINI_API_KEY`.
2. GitHub: Settings > Secrets > Actions > add `GEMINI_API_KEY`; Settings > Actions > Workflow permissions > Read and write.
3. Review news weekly: `python scripts/approve.py <id>` (accept), `python scripts/approve.py <id> "<label>" "<note>"` (change), or `--reject`.
4. After editing FAQs or myths: `node scripts/build_emb.mjs public` to rebuild embeddings.

## Tech

HTML/CSS/JavaScript · transformers.js · Gemini API · Cloudflare Workers · Python · scikit-learn · GitHub Actions · Google Forms
