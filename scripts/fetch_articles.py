"""Step 2 of the daily job: download article text for stories waiting for a Gemini label."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import label_news
P = ROOT / "review" / "pending.json"
items = json.loads(P.read_text()); n = 0
for x in items:
    if "gemini" not in x and not x.get("text"):
        t = label_news.article_text(x["url"])
        if t: x["text"] = t; n += 1
P.write_text(json.dumps(items, indent=2)); print(n, "articles downloaded")
