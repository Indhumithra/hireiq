"""
Candidate Ranking Engine
Combines semantic similarity, skill match, experience, and education scores
into a weighted overall score with explainable output.
"""
from .similarity_engine import (
    compute_semantic_similarity,
    compute_skill_match,
    compute_experience_score,
    compute_education_score,
    compute_location_score,
)
from ..utils.text_utils import EDUCATION_LEVELS


def rank_candidates(job, candidates_data: list, weights: dict = None) -> list:
    """
    Rank a list of candidates against a job posting.

    Args:
        job: Job model instance
        candidates_data: List of dicts with {candidate, parsed_resume}
        weights: Optional custom weights dict

    Returns:
        Sorted list of ranking result dicts
    """
    min_exp = job.experience_years_min
    max_exp = job.experience_years_max

    if weights is None:
        if min_exp == 0:
            weights = {
                'semantic': 0.40,
                'skills': 0.35,
                'experience': 0.05,
                'education': 0.10,
                'location': 0.10,
            }
        else:
            weights = {
                'semantic': 0.35,
                'skills': 0.35,
                'experience': 0.10,
                'education': 0.10,
                'location': 0.10,
            }
    else:
        # Normalize custom weights to always sum to 1.0
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {k: v / total_w for k, v in weights.items()}
        # Ensure all expected keys exist
        for k in ('semantic', 'skills', 'experience', 'education', 'location'):
            weights.setdefault(k, 0.0)

    job_text = f"{job.title}\n{job.description}"
    required_skills = job.required_skills
    preferred_skills = job.preferred_skills

    # Education score for job
    job_edu_level = job.education_level or 'Bachelor'
    job_edu_score = _education_name_to_score(job_edu_level)

    results = []
    for item in candidates_data:
        candidate = item['candidate']
        parsed = item.get('parsed_resume', {})

        # Candidate text for semantic comparison
        candidate_text = _build_candidate_text(candidate, parsed)

        # 1. Semantic similarity (SBERT / TF-IDF)
        semantic_score = compute_semantic_similarity(candidate_text, job_text)

        # 2. Skill match
        candidate_skills = candidate.skills if hasattr(candidate, 'skills') else parsed.get('skills', [])
        skill_result = compute_skill_match(candidate_skills, required_skills, preferred_skills)
        skill_score = skill_result['score']

        # 3. Experience match
        candidate_exp = (candidate.experience_years
                         if hasattr(candidate, 'experience_years')
                         else parsed.get('experience_years', 0.0))
        exp_score = compute_experience_score(float(candidate_exp), min_exp, max_exp)

        # 4. Education match
        candidate_edu_str = (candidate.education_level
                              if hasattr(candidate, 'education_level')
                              else parsed.get('education_level', ''))
        candidate_edu_score = _education_name_to_score(candidate_edu_str)
        edu_score = compute_education_score(candidate_edu_score, job_edu_score)

        # 5. Location match
        candidate_loc = (candidate.location 
                         if hasattr(candidate, 'location') 
                         else parsed.get('location', ''))
        loc_score = compute_location_score(candidate_loc, job.location)

        # Weighted overall score
        overall = (
            semantic_score * weights['semantic'] +
            skill_score * weights['skills'] +
            exp_score * weights['experience'] +
            edu_score * weights['education'] +
            loc_score * weights['location']
        )

        # Generate explanation
        explanation = _generate_explanation(
            semantic_score, skill_score, exp_score, edu_score, loc_score,
            skill_result['matched'], skill_result['missing'],
            candidate_exp, min_exp, max_exp,
        )

        # Shortlisting threshold
        status = _determine_status(overall, skill_result['matched'], required_skills)

        results.append({
            'candidate': candidate,
            'overall_score': round(overall, 2),
            'semantic_score': round(semantic_score, 2),
            'skill_match_score': round(skill_score, 2),
            'experience_score': round(exp_score, 2),
            'education_score': round(edu_score, 2),
            'location_score': round(loc_score, 2),
            'matched_skills': skill_result['matched'],
            'missing_skills': skill_result['missing'],
            'explanation': explanation,
            'status': status,
        })

    # Sort by overall score descending
    results.sort(key=lambda x: x['overall_score'], reverse=True)

    # Assign ranks
    for i, r in enumerate(results):
        r['rank'] = i + 1

    return results


def _build_candidate_text(candidate, parsed: dict) -> str:
    """Build a comprehensive text representation of the candidate."""
    parts = []
    if hasattr(candidate, 'raw_text') and candidate.raw_text:
        return candidate.raw_text[:3000]  # Limit for embedding
    name = parsed.get('name', '')
    skills = parsed.get('skills', [])
    titles = parsed.get('job_titles', [])
    summary = parsed.get('summary', '')
    if name:
        parts.append(name)
    if titles:
        parts.append('Roles: ' + ', '.join(titles))
    if skills:
        parts.append('Skills: ' + ', '.join(skills))
    if summary:
        parts.append(summary)
    return ' '.join(parts)


def _education_name_to_score(edu_name: str) -> int:
    """Convert education level name to numeric score."""
    if not edu_name:
        return 0
    edu_lower = edu_name.lower()
    for keyword, score in EDUCATION_LEVELS.items():
        if keyword in edu_lower:
            return score
    return 0


def _generate_explanation(semantic, skills, exp, edu, loc, matched, missing, cand_exp, min_exp, max_exp) -> str:
    """Generate a human-readable explanation of the scoring."""
    parts = []

    if semantic >= 75:
        parts.append('Strong overall profile match.')
    elif semantic >= 50:
        parts.append('Moderate profile match.')
    else:
        parts.append('Low semantic match with job requirements.')

    if matched:
        parts.append(f'Matched skills: {", ".join(matched[:5])}{"..." if len(matched) > 5 else ""}.')

    if missing:
        parts.append(f'Missing skills: {", ".join(missing[:4])}.')

    if exp >= 90:
        if min_exp == 0:
            parts.append('Suitable for freshers/entry-level.')
        else:
            parts.append('Experience meets requirements.')
    elif exp >= 70:
        parts.append('Experience slightly below requirement.')
    else:
        parts.append(f'Experience ({cand_exp:.0f} yrs) below minimum ({min_exp} yrs).')

    if edu >= 100:
        parts.append('Education qualification met.')
    elif edu >= 70:
        parts.append('Education slightly below preferred level.')
    else:
        parts.append('Education below required level.')

    if loc >= 90:
        parts.append('Excellent location match/remote.')
    elif loc >= 70:
        parts.append('Potentially suitable location.')
    else:
        parts.append('Location might be a mismatch.')

    return ' '.join(parts)


def _determine_status(overall: float, matched_skills: list, required_skills: list) -> str:
    """Determine candidate shortlisting status based on score and skill match."""
    if overall >= 70.0:
        return 'shortlisted'
    elif overall >= 40.0:
        return 'pending'
    else:
        return 'rejected'
