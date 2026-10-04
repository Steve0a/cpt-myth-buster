"""Items 8 + 9: Gemini labels each pending news story claim by claim.
Gemini only suggests. You still approve with scripts/approve.py.
Run: GEMINI_API_KEY=... python scripts/label_news.py
"""
import json, os, re, sys, time, pathlib, urllib.request, html
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
try:
    from gemini_core import label_news
except Exception:
    label_news = None

P = ROOT / "review" / "pending.json"
KEY = os.environ.get("GEMINI_API_KEY")
UA = {"User-Agent": "Mozilla/5.0"}

def article_text(url):
    try:
        if True:  # curl handles redirects and TLS reliably
            import subprocess
            raw = subprocess.run(["curl", "-sL", "-m", "12", "-A", UA["User-Agent"], url], capture_output=True).stdout.decode("utf-8", "ignore")
        else:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=12).read().decode("utf-8", "ignore")
        if "news.google.com" in url and len(raw) < 20000:
            return ""
        body = re.sub(r"(?is)<(script|style|nav|header|footer).*?</\1>", " ", raw)
        txt = html.unescape(re.sub(r"<[^>]+>", " ", body))
        txt = re.sub(r"\s+", " ", txt)
        return txt[:8000] if len(txt) > 800 else ""
    except Exception:
        return ""

def main(limit=None):
    items = json.loads(P.read_text())
    todo = [x for x in items if "gemini" not in x][:limit]
    for x in todo:
        text = x.get("text") or ""
        src = "article" if text else "headline"
        try:
            g = label_news(x["title"], x["outlet"], text or "(Only the headline is available.)", KEY)
        except Exception as e:
            print("error", x["id"], e); continue
        g["input"] = src
        if src == "headline" and g["confidence"] == "high":
            g["confidence"] = "medium"
        x["gemini"] = g
        x["suggested_label"] = x["label"] = g["label"]
        x.pop("text", None)  # don't publish copied article text
        print(f'{g["label"]:<22} {g["confidence"]:<6} {src:<8} {x["title"][:70]}')
        P.write_text(json.dumps(items, indent=2))
        time.sleep(4)

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
