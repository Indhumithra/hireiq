"""
Semantic Similarity Engine
Uses Sentence-BERT (SBERT) as primary engine with TF-IDF cosine similarity as fallback.
"""
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

# Global model cache — None means not loaded yet, False means failed to load
_sbert_model = None
_sbert_load_attempted = False


def _load_sbert(model_name: str = None):
    """Load or return cached SBERT model. Only attempts load once."""
    global _sbert_model, _sbert_load_attempted

    if _sbert_load_attempted:
        return _sbert_model  # Return cached result (model or None if failed)

    _sbert_load_attempted = True

    if not model_name:
        try:
            from flask import current_app
            model_name = current_app.config.get('SBERT_MODEL', 'all-mpnet-base-v2')
        except Exception:
            model_name = 'all-mpnet-base-v2'

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SBERT model: {model_name}")
        _sbert_model = SentenceTransformer(model_name)
        logger.info("SBERT model loaded and cached successfully.")
    except Exception as e:
        logger.warning(f"SBERT not available ({e}). Falling back to TF-IDF for all requests.")
        _sbert_model = None

    return _sbert_model


def compute_semantic_similarity(text1: str, text2: str, model_name: str = None) -> float:
    """
    Compute semantic similarity between two texts.
    Returns a score in [0, 100].
    Primary: SBERT cosine similarity
    Fallback: TF-IDF cosine similarity
    """
    if not text1 or not text2:
        return 0.0

    model = _load_sbert(model_name)

    if model is not None:
        try:
            emb1, emb2 = model.encode([text1, text2], convert_to_numpy=True)
            sim = float(cosine_similarity([emb1], [emb2])[0][0])
            return round(min(max(sim * 100, 0.0), 100.0), 2)
        except Exception as e:
            logger.warning(f"SBERT inference failed: {e}. Using TF-IDF.")

    return _tfidf_similarity(text1, text2)


def _tfidf_similarity(text1: str, text2: str) -> float:
    """Compute TF-IDF cosine similarity between two texts."""
    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            min_df=1,
            max_features=5000,
        )
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        return round(min(max(sim * 100, 0.0), 100.0), 2)
    except Exception as e:
        logger.error(f"TF-IDF similarity failed: {e}")
        return 0.0


def compute_skill_match(candidate_skills: list, required_skills: list, preferred_skills: list = None) -> dict:
    """
    Compute skill match score between candidate skills and job requirements.
    Returns score + breakdown details.
    """
    if not required_skills and not preferred_skills:
        return {'score': 50.0, 'matched': [], 'missing': [], 'preferred_matched': []}

    candidate_set = set(s.lower() for s in candidate_skills)
    required_set = set(s.lower() for s in (required_skills or []))
    preferred_set = set(s.lower() for s in (preferred_skills or []))

    matched_required = candidate_set & required_set
    missing_required = required_set - candidate_set
    matched_preferred = candidate_set & preferred_set

    # Score: Required skills = 70%, Preferred = 30%
    if required_set:
        required_score = len(matched_required) / len(required_set) * 70
    else:
        required_score = 70.0

    if preferred_set:
        preferred_score = len(matched_preferred) / len(preferred_set) * 30
    else:
        preferred_score = 30.0

    total_score = min(required_score + preferred_score, 100.0)

    return {
        'score': round(total_score, 2),
        'matched': sorted(list(matched_required)),
        'missing': sorted(list(missing_required)),
        'preferred_matched': sorted(list(matched_preferred)),
        'total_required': len(required_set),
        'total_preferred': len(preferred_set),
    }


def compute_experience_score(candidate_years: float, min_years: int, max_years: int) -> float:
    """
    Score candidate experience vs requirement.
    Returns score in [0, 100].
    """
    if min_years == 0 and max_years == 0:
        return 100.0

    if candidate_years >= min_years:
        if candidate_years <= max_years + 2:
            return 100.0
        else:
            # Overqualified — slight penalty
            return max(70.0, 100.0 - (candidate_years - max_years - 2) * 5)
    else:
        # Underqualified
        if min_years == 0:
            return 100.0
        ratio = candidate_years / min_years
        return round(min(ratio * 100, 95.0), 2)


def compute_education_score(candidate_edu_score: int, required_edu_score: int) -> float:
    """
    Score candidate education vs requirement.
    Returns score in [0, 100].
    """
    if required_edu_score == 0:
        return 100.0
    if candidate_edu_score >= required_edu_score:
        return 100.0
    elif candidate_edu_score == required_edu_score - 1:
        return 70.0
    elif candidate_edu_score == required_edu_score - 2:
        return 40.0
    else:
        return 10.0


def compute_location_score(candidate_loc: str, job_loc: str) -> float:
    """
    Score location match.
    Handled simple string matching and 'Remote' keywords.
    """
    if not job_loc or 'remote' in job_loc.lower():
        return 100.0
    
    if not candidate_loc:
        return 50.0  # Unknown
    
    cl = candidate_loc.lower()
    jl = job_loc.lower()
    
    if jl in cl or cl in jl:
        return 100.0
        
    # Check for common city parts
    j_parts = [p.strip() for p in jl.split(',')]
    c_parts = [p.strip() for p in cl.split(',')]
    
    for jp in j_parts:
        for cp in c_parts:
            if len(jp) > 3 and (jp in cp or cp in jp):
                return 90.0
                
    return 20.0  # Major mismatch
