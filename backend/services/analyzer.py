"""
Document Analyzer Service
Performs plagiarism and AI-content analysis on text
"""

import re
import hashlib
from typing import Dict, List, Any
from datetime import datetime


def analyze_document(text_content: str, file_name: str = "") -> Dict[str, Any]:
    """
    Analyze document text for plagiarism and AI-generated content
    
    This is a MOCK analyzer for development/demo purposes.
    In production, replace with real API calls to:
    - GPTZero API for AI detection
    - Copyleaks API for plagiarism detection
    - Turnitin API for similarity checking
    
    Args:
        text_content: Extracted text from the document
        file_name: Original filename for reference
        
    Returns:
        Dictionary containing analysis results
    """
    
    if not text_content or len(text_content.strip()) == 0:
        return {
            "similarity_score": 0,
            "ai_risk_score": 0,
            "ai_confidence": "Low",
            "recommendation": "No content to analyze",
            "matched_sources": []
        }
    
    # Calculate text metrics
    word_count = len(text_content.split())
    char_count = len(text_content)
    sentence_count = len(re.split(r'[.!?]+', text_content))
    avg_word_length = char_count / word_count if word_count > 0 else 0
    
    # Generate deterministic scores based on text characteristics
    # This ensures the same text always gets the same scores (not purely random)
    
    # Create a hash from the text for deterministic randomness
    text_hash = hashlib.md5(text_content.encode()).hexdigest()
    hash_int = int(text_hash[:8], 16)
    
    # Similarity score calculation (0-100)
    # Based on: text length, complexity, and hash
    # Longer, more complex texts tend to have higher similarity scores
    base_similarity = min(word_count / 100, 40)  # Up to 40 points from length
    complexity_factor = min(avg_word_length * 5, 20)  # Up to 20 points from complexity
    hash_factor = (hash_int % 30)  # 0-29 points from hash
    
    similarity_score = min(int(base_similarity + complexity_factor + hash_factor), 100)
    
    # AI risk score calculation (0-100)
    # Based on: sentence structure uniformity, text patterns
    sentences = [s.strip() for s in re.split(r'[.!?]+', text_content) if s.strip()]
    
    if len(sentences) > 1:
        # Calculate sentence length variance (AI text tends to be more uniform)
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
        variance = sum((length - avg_sentence_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
        uniformity_score = min(variance / 10, 30)  # More uniform = higher AI risk
    else:
        uniformity_score = 15
    
    # AI risk based on text characteristics
    base_ai_risk = uniformity_score
    length_factor = min(word_count / 50, 25)  # Longer texts more likely AI
    hash_factor_ai = (hash_int % 45)  # 0-44 points from hash
    
    ai_risk_score = min(int(base_ai_risk + length_factor + hash_factor_ai), 100)
    
    # Determine AI confidence level
    if ai_risk_score >= 70:
        ai_confidence = "High"
    elif ai_risk_score >= 40:
        ai_confidence = "Medium"
    else:
        ai_confidence = "Low"
    
    # Generate recommendation based on scores
    if similarity_score > 60 or ai_risk_score > 75:
        recommendation = "High risk - Manual teacher review required"
    elif similarity_score > 40 or ai_risk_score > 50:
        recommendation = "Medium risk - Recommend checking sources"
    elif similarity_score > 25 or ai_risk_score > 30:
        recommendation = "Low-medium risk - Review suggested"
    else:
        recommendation = "Low risk - No immediate action needed"
    
    # Generate mock matched sources for plagiarism
    matched_sources = _generate_mock_sources(similarity_score, text_content, file_name)
    
    return {
        "similarity_score": similarity_score,
        "ai_risk_score": ai_risk_score,
        "ai_confidence": ai_confidence,
        "recommendation": recommendation,
        "matched_sources": matched_sources,
        "analysis_metadata": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_word_length": round(avg_word_length, 2),
            "analyzed_at": datetime.utcnow().isoformat(),
            "analyzer_version": "1.0.0-mock"
        }
    }


def _generate_mock_sources(similarity_score: int, text_content: str, file_name: str) -> List[Dict[str, Any]]:
    """
    Generate mock matched sources based on similarity score
    
    In production, this would be replaced with real plagiarism detection API results
    
    Args:
        similarity_score: Overall similarity score
        text_content: Document text content
        file_name: Original filename
        
    Returns:
        List of matched sources
    """
    
    if similarity_score < 20:
        return []
    
    # Create deterministic source selection based on text hash
    text_hash = hashlib.md5(text_content.encode()).hexdigest()
    hash_int = int(text_hash[:4], 16)
    
    # Source pool - in production, these come from real plagiarism databases
    sources_pool = [
        {
            "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
            "title": "Artificial Intelligence - Wikipedia",
            "match_percent": 0,
            "type": "web"
        },
        {
            "url": "https://www.britannica.com/technology/machine-learning",
            "title": "Machine Learning | Britannica",
            "match_percent": 0,
            "type": "web"
        },
        {
            "url": "https://arxiv.org/abs/2301.00001",
            "title": "Research Paper Sample",
            "match_percent": 0,
            "type": "academic"
        },
        {
            "url": "https://www.researchgate.net/publication/sample",
            "title": "ResearchGate Publication",
            "match_percent": 0,
            "type": "academic"
        },
        {
            "url": f"Previous submission: {file_name}",
            "title": "Institutional Repository",
            "match_percent": 0,
            "type": "student"
        },
        {
            "url": "https://scholar.google.com/sample",
            "title": "Google Scholar Article",
            "match_percent": 0,
            "type": "academic"
        }
    ]
    
    # Determine number of sources based on similarity score
    if similarity_score > 60:
        num_sources = min(3 + (hash_int % 3), len(sources_pool))
    elif similarity_score > 40:
        num_sources = min(2 + (hash_int % 2), len(sources_pool))
    elif similarity_score > 20:
        num_sources = min(1 + (hash_int % 2), len(sources_pool))
    else:
        num_sources = 0
    
    # Select sources deterministically
    selected_indices = []
    for i in range(num_sources):
        idx = (hash_int + i * 7) % len(sources_pool)
        if idx not in selected_indices:
            selected_indices.append(idx)
    
    # Calculate match percentages
    matched_sources = []
    remaining_match = similarity_score
    
    for idx in selected_indices:
        if remaining_match <= 0:
            break
        
        source = sources_pool[idx].copy()
        
        # Distribute match percentage
        if len(selected_indices) == 1:
            match_percent = min(remaining_match, similarity_score - 5)
        else:
            match_percent = min(remaining_match // len(selected_indices) + (hash_int % 5), remaining_match)
        
        match_percent = max(1, min(match_percent, remaining_match))
        source["match_percent"] = match_percent
        
        matched_sources.append(source)
        remaining_match -= match_percent
    
    return matched_sources


# ========================================
# PRODUCTION API INTEGRATION NOTES
# ========================================

"""
To integrate with real plagiarism/AI detection APIs:

1. GPTZero API (AI Detection):
   - Endpoint: https://api.gptzero.me/v2/predict
   - Requires: API key, text content
   - Returns: AI probability score, confidence level
   
   Example integration:
   ```python
   import requests
   
   def check_ai_with_gptzero(text: str, api_key: str) -> Dict:
       response = requests.post(
           "https://api.gptzero.me/v2/predict",
           headers={"Authorization": f"Bearer {api_key}"},
           json={"document": text}
       )
       return response.json()
   ```

2. Copyleaks API (Plagiarism Detection):
   - Endpoint: https://api.copyleaks.com/v3/scans/submit
   - Requires: API key, email, text content
   - Returns: Similarity score, matched sources
   
   Example integration:
   ```python
   def check_plagiarism_with_copyleaks(text: str, api_key: str) -> Dict:
       # Submit scan
       response = requests.post(
           "https://api.copyleaks.com/v3/scans/submit",
           headers={"Authorization": f"Bearer {api_key}"},
           json={"text": text, "scanType": "static"}
       )
       return response.json()
   ```

3. Turnitin API (Similarity Checking):
   - Requires: LTI integration or direct API access
   - Returns: Similarity report, source matches
   
Replace the mock_analyze_document function in main.py with calls to these real APIs.
"""