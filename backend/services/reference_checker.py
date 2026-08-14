"""
Reference Checker Service
Uses the free CrossRef API to find real academic journal matches
"""

import re
import requests
from difflib import SequenceMatcher

CROSSREF_API = "https://api.crossref.org/works"
HEADERS = {
    "User-Agent": "ScholarGuard/3.2 (academic integrity research; mailto:admin@scholarguard.com)"
}
TIMEOUT = 8


def _http_get(url, params=None):
    """Make a GET request and return parsed JSON, or None on failure."""
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("CROSSREF ERROR:", e)
        return None


def extract_key_sentences(text, limit=3):
    """
    Extract the 2-3 longest/most complex sentences from the text.
    Sentences must be at least 8 words to be considered meaningful.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.split()) >= 8]
    # Sort by length (word count) descending to get the most complex sentences
    sentences.sort(key=lambda s: len(s.split()), reverse=True)
    return sentences[:limit]


def clean(s):
    """Normalize text for comparison."""
    return re.sub(r'[^a-z0-9 ]', '', s.lower())


def search_crossref(query):
    """
    Search the CrossRef API for academic papers matching the query.
    Returns a list of real academic source dictionaries.
    """
    params = {
        "query": query,
        "select": "title,author,DOI,published-print,container-title,score",
        "rows": 3
    }
    data = _http_get(CROSSREF_API, params=params)
    results = []
    if data and "message" in data and "items" in data["message"]:
        for item in data["message"]["items"]:
            # Extract title
            title = ""
            if item.get("title"):
                title = item["title"][0] if isinstance(item["title"], list) else item["title"]

            # Extract authors
            authors = []
            for author in item.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)
            author_str = ", ".join(authors) if authors else "Unknown Author"

            # Extract journal / container title
            journal = ""
            if item.get("container-title"):
                journal = item["container-title"][0] if isinstance(item["container-title"], list) else item["container-title"]

            # Extract publication year
            year = None
            if item.get("published-print"):
                date_parts = item["published-print"].get("date-parts", [[None]])
                if date_parts and date_parts[0]:
                    year = date_parts[0][0]
            if year is None and item.get("published-online"):
                date_parts = item["published-online"].get("date-parts", [[None]])
                if date_parts and date_parts[0]:
                    year = date_parts[0][0]

            # Extract DOI
            doi = item.get("DOI", "")
            url = f"https://doi.org/{doi}" if doi else ""

            # CrossRef relevance score (0-100 scale)
            score = item.get("score", 0)
            match_percent = round(min(100, score * 100), 1)

            results.append({
                "title": title or "Untitled Research Paper",
                "author": author_str,
                "journal": journal or "Unknown Journal",
                "year": year,
                "url": url,
                "doi": doi,
                "match_percent": match_percent
            })
    return results


def check_references(text):
    """
    Check the document text against real academic sources via CrossRef.
    Returns a list of matched sources with real data, or an empty list.
    """
    matched_sources = []
    key_sentences = extract_key_sentences(text)

    for sent in key_sentences:
        # Use the first 12 words of the sentence as the search query
        query = " ".join(sent.split()[:12])
        results = search_crossref(query)

        for r in results:
            # Estimate match percentage based on CrossRef score
            # and text similarity between the sentence and the paper title
            title_similarity = SequenceMatcher(
                None, clean(sent), clean(r["title"])
            ).ratio() if r["title"] else 0

            # Combine CrossRef score with title similarity for a realistic estimate
            combined = (r["match_percent"] * 0.7) + (title_similarity * 100 * 0.3)
            match_percent = round(min(100, combined), 1)

            matched_sources.append({
                "source": f"Research Paper: {r['title']}",
                "title": r["title"],
                "author": r["author"],
                "journal": r["journal"],
                "year": r["year"],
                "url": r["url"],
                "doi": r["doi"],
                "match_percent": match_percent,
                "matched_text": sent[:150]
            })

    # Sort by match percentage descending and return top 8
    matched_sources.sort(key=lambda x: x["match_percent"], reverse=True)
    return matched_sources[:8]