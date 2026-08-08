import re
import math
from collections import Counter
from services.reference_checker import check_references

def analyze_document(text, filename):
    words = re.findall(r'\w+', text.lower())
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    word_count = len(words)
    sentence_count = len(sentences)

    if word_count == 0:
        return {
            "similarity_score": 0, "ai_risk_score": 0, "ai_confidence": "Low",
            "word_count": 0, "sentence_count": 0, "burstiness_score": 0,
            "vocabulary_richness": 0, "recommendation": "Empty document.",
            "matched_sources": [], "improvement_tips": ["Upload a document with text."]
        }

    # --- AI Detection (Burstiness + Vocabulary) ---
    sent_lengths = [len(re.findall(r'\w+', s)) for s in sentences]
    avg_sent_len = sum(sent_lengths) / sentence_count if sentence_count else 0
    variance = sum((l - avg_sent_len)**2 for l in sent_lengths) / sentence_count if sentence_count else 0
    burstiness = min(100, math.sqrt(variance) * 4)
    unique_words = len(set(words))
    ttr = unique_words / word_count if word_count else 0
    vocab_richness = ttr * 100
    ai_risk = max(0, min(100, 100 - (burstiness * 1.2) - (vocab_richness * 0.8)))

    # --- Live Reference Check (Books + Web + Research Papers) ---
    matched_sources = check_references(text)
    top_match = matched_sources[0]["match_percent"] if matched_sources else 0

    # --- Local heuristic (repeated blocks + generic phrases) ---
    academic_phrases = ["in conclusion", "it is important to note", "furthermore", "on the other hand", "as a matter of fact"]
    phrase_hits = sum(1 for p in academic_phrases if p in text.lower())
    ngrams = [tuple(words[i:i+5]) for i in range(len(words)-4)]
    repeated_blocks = sum(1 for c in Counter(ngrams).values() if c > 1)
    heuristic = (phrase_hits * 5) + (repeated_blocks * 3)

    similarity_score = min(100, round(max(heuristic, top_match * 0.9), 1))

    # --- Improvement Coach ---
    suggestions = []
    if matched_sources:
        suggestions.append(f"Text closely matches {len(matched_sources)} real source(s). Ensure every match is properly cited and referenced.")
    if avg_sent_len > 25:
        suggestions.append("Your sentences are quite long. Break them down to improve readability and flow.")
    if vocab_richness < 40:
        suggestions.append("Vocabulary is repetitive. Use a thesaurus to diversify your word choices.")
    if ai_risk > 60:
        suggestions.append("The text structure appears highly uniform. Add personal insights or varied sentence lengths to sound more human.")
    if word_count < 100:
        suggestions.append("The document is very short. Expand on your core arguments with evidence.")
    if not suggestions:
        suggestions.append("Excellent writing! The text is original, well-structured, and reads naturally.")

    return {
        "similarity_score": similarity_score,
        "ai_risk_score": round(ai_risk, 1),
        "ai_confidence": "High" if ai_risk > 70 else ("Medium" if ai_risk > 40 else "Low"),
        "word_count": word_count,
        "sentence_count": sentence_count,
        "burstiness_score": round(burstiness, 1),
        "vocabulary_richness": round(vocab_richness, 1),
        "recommendation": " | ".join(suggestions),
        "matched_sources": matched_sources,
        "improvement_tips": suggestions
    }
