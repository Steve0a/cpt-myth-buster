"""Daily CPT news collector. No AI.
Pulls CPT news, suggests a label with keyword rules, and adds new items to
review/pending.json. Nothing appears on the site until you move an item into
news.json with "status": "approved".

Run:  python scripts/fetch_news.py
"""
import json, re, html, urllib.request, urllib.parse, xml.etree.ElementTree as ET, hashlib, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PENDING = ROOT / "review" / "pending.json"
NEWS = ROOT / "public" / "news.json"
UA = {"User-Agent": "Mozilla/5.0 (CPT Myth-Buster news checker)"}

BING = [
    "https://www.bing.com/news/search?q=%22curricular+practical+training%22&format=rss",
    "https://www.bing.com/news/search?q=CPT+international+students+SEVP&format=rss",
]
FEEDS = [
    ("Google News", "https://news.google.com/rss/search?q=%22curricular+practical+training%22+when:14d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News", "https://news.google.com/rss/search?q=SEVP+CPT+guidance+when:14d&hl=en-US&gl=US&ceid=US:en"),
]
SINCE = (datetime.date.today() - datetime.timedelta(days=120)).isoformat()
FEDREG = f"https://www.federalregister.gov/api/v1/documents.json?per_page=10&order=newest&conditions[term]=%22curricular+practical+training%22&conditions[publication_date][gte]={SINCE}"

# Official sources used for comparison (same ones the site cites)
OFFICIAL = {
    "bcm": "https://iso.mit.edu/wp-content/uploads/2026/08/2026_0824_SEVP_BroadcastMessage2608-02_CPT_Guidance.pdf",
    "pm": "https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5",
    "reg": "https://www.nafsa.org/regulatory-information/8cfr2142f",
}

# Keyword rules -> suggested label. Order matters. You make the final call.
RULES = [
    ("New rule change", "bcm", r"(broadcast message|new (federal )?guidance|final rule|proposed rule|interim rule|federal register|sevp (issued|guidance))"),
    ("Matches official rule", "bcm", r"(required (of|for) all students|integral part|elective|halts?|paus(e|es|ed|ing)|restrict|tighten|narrow|new federal (guidelines|rules|immigration rules)|guidelines|limit(s|ing)? internships|changes curricular|work authorization|eligibility criteria)"),
    ("Contradicts", "pm", r"(cpt (is|requires) (visa )?sponsorship|needs? an ead for cpt|cpt (has|with) no (rules|limits)|any internship (qualifies|counts))"),
    ("Matches official rule", "pm", r"(12 months|one year) (of )?full[- ]time cpt|opt eligib"),
]

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()

def suggest(text):
    t = text.lower()
    for label, src, pat in RULES:
        if re.search(pat, t):
            return label, OFFICIAL[src], pat
    return "Not covered", OFFICIAL["reg"], None

def _key(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower().split(" - ")[0])[:60]

def items():
    for url in BING:  # Bing gives direct article links, so the article text can be read
        try:
            x = get(url).decode("utf-8", "ignore")
            for it in re.findall(r"<item>(.*?)</item>", x, re.S):
                f = lambda tag: html.unescape((re.search(f"<{tag}>(.*?)</{tag}>", it, re.S) or [None, ""])[1])
                link = f("link"); link = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("url", [link])[0]
                src = re.search(r"<News:Source>(.*?)</News:Source>", it)
                yield {"title": f("title"), "url": link, "outlet": src.group(1) if src else urllib.parse.urlparse(link).netloc,
                       "date": f("pubDate"), "text": f("title") + " " + re.sub("<[^>]+>", " ", f("description")), "direct": True}
        except Exception as e:
            print("bing error", e)
    for name, url in FEEDS:
        try:
            root = ET.fromstring(get(url))
            for it in root.iter("item"):
                title = (it.findtext("title") or "").strip()
                src = it.find("source")
                yield {"title": title, "url": it.findtext("link"), "outlet": src.text if src is not None else name,
                       "date": it.findtext("pubDate"), "text": title + " " + re.sub("<[^>]+>", " ", it.findtext("description") or "")}
        except Exception as e:
            print("feed error", url, e)
    try:
        for d in json.loads(get(FEDREG))["results"]:
            yield {"title": d["title"], "url": d["html_url"], "outlet": "Federal Register", "date": d["publication_date"],
                   "text": d["title"] + " " + (d.get("abstract") or "") + " final rule federal register"}
    except Exception as e:
        print("federal register error", e)

def main():
    PENDING.parent.mkdir(exist_ok=True)
    pending = json.loads(PENDING.read_text()) if PENDING.exists() else []
    approved = json.loads(NEWS.read_text()) if NEWS.exists() else []
    seen = {x["id"] for x in pending + approved}
    titles = {_key(x["title"]) for x in pending + approved}
    added = 0
    for it in items():
        _id = hashlib.sha1((it["url"] or it["title"]).encode()).hexdigest()[:12]
        if _id in seen or _key(it["title"]) in titles:
            continue
        titles.add(_key(it["title"]))
        label, official, rule = suggest(it["text"])
        pending.append({"id": _id, "status": "pending", "title": it["title"], "url": it["url"], "outlet": it["outlet"],
                        "date": it["date"], "suggested_label": label, "label": label, "official": official,
                        "matched_rule": rule, "note": "", "found": datetime.date.today().isoformat()})
        seen.add(_id); added += 1
    PENDING.write_text(json.dumps(pending, indent=2))
    print(f"{added} new items added to review/pending.json ({len(pending)} waiting for review)")

if __name__ == "__main__":
    main()
