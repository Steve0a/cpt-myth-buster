# PRD: CPT Myth-Buster

**Owner:** Steve O. (Product lead and builder) · **Status:** Live beta · **Last updated:** October 3, 2026
**Live:** https://cptmythbuster.steveoamo960.workers.dev

## 1. Problem

International (F-1) students at Park University and elsewhere make job-search and internship decisions based on CPT (Curricular Practical Training) myths: that they can't apply before CPT is approved, that "no sponsorship" means they can't apply, or that any credit-bearing internship qualifies.

The stakes went up in August 2026. SEVP (the DHS program that oversees CPT) issued Broadcast Messages 2608-01 (Aug 12) and 2608-02 (Aug 24), limiting CPT to practical training that is required of every student in a curriculum. Several universities paused or narrowed CPT approvals, and news coverage has been fast, uneven and sometimes misleading.

Students need one place that gives plain answers, shows the official source for every answer, and says "ask your DSO" when the rules don't clearly answer the question.

## 2. Users

| User | Need |
|---|---|
| **Primary:** F-1 graduate students in job search (IS, Business Analytics, CS, MBA) | Quick, trustworthy answers before applying, interviewing or accepting an offer |
| Undergraduate F-1 students | Basic CPT understanding and timelines |
| Career services and International Student office staff | A link to share at sessions; fewer repeated myth-based questions |
| Recruiters and employers (secondary) | Plain explanation of CPT vs. sponsorship |

## 3. Goals and non-goals

**Goals**
1. Answer common CPT questions correctly, with an official source on every answer.
2. Never invent rules: refuse and point to the DSO when sources don't cover a question.
3. Keep students current on rule changes (news check + email updates).
4. Measure AI quality openly (test sets, human review agreement).

**Non-goals**
- Legal advice or school-specific eligibility decisions (the DSO decides).
- Answering non-CPT immigration questions (green cards, visitor visas).
- Publishing news labels without human review.

## 4. Success metrics

| Metric | Target | Current |
|---|---|---|
| Smart search: right answer first (55-question test set) | ≥ 80% | **84%** (keyword baseline 40%) |
| Off-topic questions refused | 100% | **5/5** |
| Gemini fallback: unverifiable quotes shown to users | 0 | **0** (1 blocked in testing) |
| Gemini vs. human news label agreement | ≥ 80% with article text | 2 of 3 with article text; 0 of 4 headline-only (early) |
| Weekly active users | 50 in first month | To measure after launch |
| Email signups | 30 in first month | To measure after launch |
| "Helpful" rate on answers | ≥ 80% | To measure (feedback logging planned) |

## 5. Features and requirements

| # | Feature | Requirement | Status |
|---|---|---|---|
| F1 | Chat Q&A | 25 sourced FAQs + 28 myths; each answer shows verdict, official quote, source link, match score | Live |
| F2 | Smart search (ML) | bge-small sentence embeddings in the browser; max of question and question+answer similarity; threshold 0.70 | Live |
| F3 | Gemini fallback (LLM) | Only when F2 score < 0.70. Gemini answers from 6 saved official pages only; every quote verified word for word; no verified quote = no answer | Live |
| F4 | Aug 2026 update page | Plain summary of SEVP guidance with official links | Live |
| F5 | CPT news check | Daily collection (Bing News, Google News, Federal Register); Gemini labels claim by claim; human approves before publishing | Live |
| F6 | AI quality page | Search test results, fallback safety check, Gemini vs. human agreement, own classifier vs. baseline | Live |
| F7 | Email updates | Google Form signup with consent; updates only on official rule changes | Live |
| F8 | Quick tools | OPT safety check (1-year full-time CPT rule), hours check, offer-letter checklist, recruiter scripts | Live |
| F9 | Disclaimer | Every page: educational only, official sources are USCIS and Study in the States (DHS/SEVP), confirm with DSO | Live |

## 6. AI approach and guardrails

- **Grounding:** Gemini sees only saved text from SEVP Broadcast Message 2608-02, the USCIS Policy Manual (Vol. 2, Part F, Ch. 5), 8 CFR 214.2(f)(10), USCIS I-9 guidance, the USCIS OPT page and the IRS FICA page.
- **Quote verification:** each quote is normalized and checked as an exact substring of the source text. Unverified quotes are dropped.
- **Refusal by default:** low similarity + no verified quote = "No official answer found. Ask your DSO."
- **Human in the loop:** news labels are suggestions until approved with `scripts/approve.py`; agreement is tracked.
- **Key safety:** the Gemini key lives only as a Cloudflare Worker secret and a GitHub Actions secret, never in the page.
- **Cost:** Gemini 3.5 Flash-Lite, about 8,300 input tokens per fallback question; the free tier covers expected traffic.

## 7. Architecture

```
Browser (public/index.html)
  ├─ Smart search: transformers.js + bge-small (runs locally, no API cost)
  └─ POST /api/ask  ──►  Cloudflare Worker (worker/index.js)
                           └─ Gemini 3.5 Flash-Lite + saved official text + quote check
GitHub Actions (daily 8 AM CT)
  fetch_news.py → fetch_articles.py → label_news.py (Gemini) → review/pending.json
  You: approve.py → public/news.json → site updates
```

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Rules change again | Daily news check, rule-change label, email updates; sources re-checked monthly |
| AI states a wrong rule | Grounding + quote verification + refusal + DSO reminder on every answer |
| Headline-only news judged poorly | Marked low confidence; article text fetched where possible; human review required |
| Students treat it as legal advice | Disclaimer on every page; DSO pointer in every answer |
| Small training data for own classifier | Reported against a majority baseline; retrain as reviews grow |

## 9. Roadmap

1. Launch at a Park job-search session; International Student office content review.
2. Log helpful/not-helpful and unanswered questions to measure usage.
3. Five student interviews; prioritize new FAQs from unanswered questions.
4. Grow the reviewed news set past 50 stories; retrain the classifier.
5. Multilingual answers (official quote stays in English).

## 10. Open questions

- Will Park's International Student office co-sign the content?
- How does the August 2026 guidance apply to each Park graduate program?
- Should email updates move to a newsletter tool once signups pass 100?
