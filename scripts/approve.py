"""Approve or reject a reviewed news item (item 16 records whether you agreed with Gemini).
Usage:
  python scripts/approve.py <id>                        # accept Gemini's label
  python scripts/approve.py <id> "<label>" "<note>"     # change the label
  python scripts/approve.py <id> --reject
Labels: "Matches official rule", "Contradicts", "Not covered", "New rule change"
"""
import json, sys, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
P, N = ROOT / "review" / "pending.json", ROOT / "public" / "news.json"
pending, news = json.loads(P.read_text()), json.loads(N.read_text())
item = next(x for x in pending if x["id"] == sys.argv[1])
pending.remove(item)
if "--reject" not in sys.argv:
    g = item.get("gemini", {})
    if len(sys.argv) > 2: item["label"] = sys.argv[2]
    item["note"] = sys.argv[3] if len(sys.argv) > 3 else (item.get("note") or g.get("reason", ""))
    if g:
        item["ai_label"] = g.get("label"); item["agreed"] = item["label"] == g.get("label")
    item["status"] = "approved"; item["reviewed"] = datetime.date.today().isoformat()
    news.insert(0, item)
    N.write_text(json.dumps(news, indent=2))
P.write_text(json.dumps(pending, indent=2))
print("done:", item["title"][:80])
