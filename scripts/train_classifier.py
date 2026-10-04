"""Item 10: our own news classifier (TF-IDF + logistic regression), compared with Gemini.
Training labels: the human-approved label when a story was reviewed, otherwise Gemini's label.
Evaluation: leave-one-out cross-validation, compared with a majority-class baseline.
Writes the results into ai_report.json for the AI quality page.
Run: python scripts/train_classifier.py
"""
import json, pathlib, collections
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import make_pipeline

ROOT = pathlib.Path(__file__).resolve().parent.parent
pending = json.loads((ROOT / "review" / "pending.json").read_text())
news = json.loads((ROOT / "public" / "news.json").read_text())

rows = []
for x in news + pending:
    label = x["label"] if x.get("status") == "approved" else (x.get("gemini") or {}).get("label")
    if not label:
        continue
    g = x.get("gemini") or {}
    if x.get("status") != "approved" and g.get("input") == "headline":
        continue  # skip weak headline-only labels
    rows.append((x["title"] + " " + x.get("outlet", ""), label, x.get("status") == "approved"))

X = [r[0] for r in rows]; y = [r[1] for r in rows]
counts = collections.Counter(y)
report = {"examples": len(rows), "human_labeled": sum(r[2] for r in rows), "label_counts": dict(counts)}
if len(counts) < 2 or len(rows) < 10:
    report["summary"] = "Not enough labeled stories yet."
else:
    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True),
                          LogisticRegression(max_iter=2000, class_weight="balanced"))
    pred = cross_val_predict(model, X, y, cv=LeaveOneOut())
    acc = sum(p == t for p, t in zip(pred, y)) / len(y)
    base = counts.most_common(1)[0][1] / len(y)
    report.update(agreement_with_gemini=round(acc * 100), majority_baseline=round(base * 100),
        summary=f"Trained on {len(rows)} stories (headline + outlet). Agreed with the reference label on {round(acc*100)}% "
                f"in leave-one-out testing, vs. {round(base*100)}% for always guessing the most common label. "
                "Small data, so treat this as an early result.")
    model.fit(X, y)
out = ROOT / "public" / "ai_report.json"
r = json.loads(out.read_text()); r["classifier"] = report; out.write_text(json.dumps(r, indent=1))
print(json.dumps(report, indent=1))
