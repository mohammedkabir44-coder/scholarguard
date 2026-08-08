import re
import json
import urllib.request
import urllib.parse
from difflib import SequenceMatcher

def _http_get(url, timeout=6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ScholarGuard/3.2 (academic integrity research)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print("REF CHECK ERROR:", e)
        return None

def extract_key_sentences(text, limit=3):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.split()) >= 8]
    sentences.sort(key=lambda s: len(s.split()), reverse=True)
    return sentences[:limit]

def clean(s):
    return re.sub(r'[^a-z0-9 ]', '', s.lower())

def search_books(query):
    url = "https://www.googleapis.com/books/v1/volume?q=" + urllib.parse.quote(query) + "&maxResults=3"
    data = _http_get(url)
    results = []
    if data and "items" in data:
        for item in data["items"]:
            vi = item.get("volumeInfo", {})
            results.append({
                "type": "Book",
                "title": vi.get("title", "Unknown Book"),
                "author": ", ".join(vi.get("authors", ["Unknown Author"])),
                "url": vi.get("infoLink", "https://books.google.com"),
                "snippet": (vi.get("description", "") or vi.get("title", ""))[:300]
            })
    return results

def search_wikipedia(query):
    url = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + urllib.parse.quote(query) + "&format=json&srslimit=3"
    data = _http_get(url)
    results = []
    if data and "query" in data:
        for item in data["query"].get("search", []):
            title = item.get("title", "")
            snippet = re.sub(r'<[^>]+>', '', item.get("snippet", ""))
            results.append({
                "type": "Web (Wikipedia)",
                "title": title,
                "author": "Wikipedia",
                "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
                "snippet": snippet
            })
    return results

def search_scholar(query):
    url = "https://api.openalex.org/works?search=" + urllib.parse.quote(query) + "&per-page=3"
    data = _http_get(url)
    results = []
    if data and "results" in data:
        for item in data["results"]:
            author = ""
            if item.get("authorships"):
                author = item["authorships"][0].get("author", {}).get("display_name", "")
            results.append({
                "type": "Research Paper",
                "title": item.get("title") or "Untitled Research",
                "author": author,
                "url": item.get("id", ""),
                "snippet": item.get("title") or ""
            })
    return results

def check_references(text):
    matched_sources = []
    for sent in extract_key_sentences(text):
        query = " ".join(sent.split()[:12])
        all_results = search_books(query) + search_wikipedia(query) + search_scholar(query)
        for r in all_results:
            ratio = SequenceMatcher(None, clean(sent), clean(r["snippet"])).ratio()
            if ratio > 0.40:
                matched_sources.append({
                    "source": f"{r['type']}: {r['title']} ({r['author']})",
                    "url": r["url"],
                    "match_percent": round(ratio * 100, 1),
                    "matched_text": sent[:150]
                })
    matched_sources.sort(key=lambda x: x["match_percent"], reverse=True)
    return matched_sources[:8]
