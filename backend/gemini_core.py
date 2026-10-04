"""Shared Gemini logic: grounded answers and news fact-checking.
Every quote Gemini returns is checked word-for-word against the saved official
text. If a quote can't be found, it is dropped; with no valid quote, there is no answer.
"""
import json, os, re, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = json.loads((ROOT / "official" / "sources.json").read_text())
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
API = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
NAMES = {
    "bcm": "SEVP Broadcast Message 2608-02 (Aug 24, 2026)",
    "pm": "USCIS Policy Manual, Vol. 2, Part F, Ch. 5",
    "reg": "8 CFR 214.2(f)(10)",
    "combo": "USCIS I-9 Central: Combination Documents",
    "opt": "USCIS: Optional Practical Training",
    "irs": "IRS: Foreign student Social Security and Medicare taxes",
}

def _norm(s):
    s = s.lower().replace("’", "'").replace("“", '"').replace("”", '"').replace("*", "")
    return re.sub(r"[^a-z0-9%']+", " ", s).strip()

NORM_SRC = {k: _norm(v["text"]) for k, v in SOURCES.items()}

def verify_quote(source, quote):
    q = _norm(quote or "")
    return bool(source in NORM_SRC and len(q) >= 20 and q in NORM_SRC[source])

def context_block():
    return "\n\n".join(f"<source id=\"{k}\" name=\"{NAMES[k]}\">\n{v['text']}\n</source>" for k, v in SOURCES.items())

def call_gemini(prompt, schema, api_key=None, temperature=0.1):
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "responseMimeType": "application/json", "responseSchema": schema},
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-goog-api-key"] = api_key
    proxy_url = os.environ.get("CUSTOM_CRED_GENERATIVELANGUAGE_GOOGLEAPIS_COM_URL")
    if proxy_url and not api_key:  # preview server: platform credential proxy
        import requests
        path = API.format(m=MODEL).split("googleapis.com", 1)[1]
        r = requests.post(proxy_url.rstrip("/") + path, json=body, timeout=90,
                          headers={**headers, "x-api-key": os.environ.get("CUSTOM_CRED_GENERATIVELANGUAGE_GOOGLEAPIS_COM_PROXY_AUTH_KEY", "")})
        r.raise_for_status(); data = r.json()
        return json.loads(data["candidates"][0]["content"]["parts"][-1]["text"]), data.get("usageMetadata", {})
    if os.environ.get("HTTPS_PROXY") and not api_key:  # sandbox: key injected by an HTTPS proxy
        import subprocess
        out = subprocess.run(["curl", "-s", "-m", "90", "-H", "Content-Type: application/json", "--data-binary", "@-", API.format(m=MODEL)],
                             input=json.dumps(body).encode(), capture_output=True, check=True)
        data = json.loads(out.stdout)
        if "error" in data: raise RuntimeError(data["error"].get("message"))
        text = data["candidates"][0]["content"]["parts"][-1]["text"]
        return json.loads(text), data.get("usageMetadata", {})
    try:
        import requests
        r = requests.post(API.format(m=MODEL), json=body, headers=headers, timeout=90)
        r.raise_for_status(); data = r.json()
    except ImportError:
        req = urllib.request.Request(API.format(m=MODEL), data=json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read())
    text = data["candidates"][0]["content"]["parts"][-1]["text"]
    usage = data.get("usageMetadata", {})
    return json.loads(text), usage

# ---------- Item 3: grounded Q&A fallback ----------
ASK_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "answerable": {"type": "BOOLEAN"},
        "answer": {"type": "STRING"},
        "quotes": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "source": {"type": "STRING", "enum": list(SOURCES)}, "quote": {"type": "STRING"}}, "required": ["source", "quote"]}},
    },
    "required": ["answerable", "answer", "quotes"],
}

def ask(question, api_key=None):
    prompt = f"""You help F-1 international students understand CPT (Curricular Practical Training).
Answer ONLY using the official sources below. Do not use outside knowledge.
Rules:
- If the sources do not clearly answer the question, set answerable=false and answer="".
- Otherwise write 2-4 short, plain sentences (no legal advice, no guessing), and end by suggesting the student confirm with their DSO.
- Give 1-3 quotes copied EXACTLY, word for word, from the sources, each at least 8 words, with the source id.

{context_block()}

Student question: {question}"""
    out, usage = call_gemini(prompt, ASK_SCHEMA, api_key)
    good = [q for q in out.get("quotes", []) if verify_quote(q["source"], q["quote"])]
    if not out.get("answerable") or not good:
        return {"status": "no_answer", "dropped_quotes": len(out.get("quotes", [])) - len(good), "usage": usage}
    return {"status": "ok", "answer": out["answer"],
            "quotes": [{**q, "name": NAMES[q["source"]], "url": SOURCES[q["source"]]["url"]} for q in good],
            "dropped_quotes": len(out["quotes"]) - len(good), "model": MODEL, "usage": usage}

# ---------- Items 8 + 9: news labeling, claim by claim ----------
LABELS = ["Matches official rule", "Contradicts", "Not covered", "New rule change"]
NEWS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "claims": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "claim": {"type": "STRING"},
            "verdict": {"type": "STRING", "enum": ["matches", "contradicts", "not_covered"]},
            "source": {"type": "STRING", "enum": list(SOURCES) + ["none"]},
            "official_quote": {"type": "STRING"}}, "required": ["claim", "verdict", "source", "official_quote"]}},
        "label": {"type": "STRING", "enum": LABELS},
        "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
        "reason": {"type": "STRING"},
    },
    "required": ["claims", "label", "confidence", "reason"],
}

def label_news(title, outlet, text, api_key=None):
    prompt = f"""You fact-check news about CPT (Curricular Practical Training) for F-1 students against official sources.
Steps:
1. List up to 4 specific factual claims the article makes about CPT rules (skip opinions).
2. For each claim, compare with the official sources ONLY. verdict: matches, contradicts, or not_covered.
   Give the source id and an official_quote copied EXACTLY (8+ words). If not_covered, source="none" and official_quote="".
3. Overall label:
   - "New rule change" if the article reports a new official rule or guidance that is itself one of the sources, or newer than them.
   - "Contradicts" if any key claim contradicts the sources.
   - "Matches official rule" if the key claims match.
   - "Not covered" if the sources don't address the claims.
4. confidence: high/medium/low. Use low if you only have a headline. reason: one plain sentence.

{context_block()}

<article outlet="{outlet}">
TITLE: {title}
{text[:6000]}
</article>"""
    out, usage = call_gemini(prompt, NEWS_SCHEMA, api_key)
    for c in out.get("claims", []):
        c["quote_verified"] = c["source"] == "none" or verify_quote(c["source"], c["official_quote"])
        if c["source"] in SOURCES:
            c["url"] = SOURCES[c["source"]]["url"]
    unverified = [c for c in out.get("claims", []) if not c["quote_verified"]]
    if unverified and out.get("confidence") == "high":
        out["confidence"] = "medium"
    out["unverified_quotes"] = len(unverified)
    out["usage"] = usage
    return out
