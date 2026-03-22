from ..utils.text_utils import (
    extract_skills, extract_experience_years, extract_education_level,
    EDUCATION_LEVELS, clean_text
)
import re


def analyze_job_description(description: str) -> dict:
    """
    Analyze a job description to extract structured requirements.
    Returns required skills, preferred skills, experience range, education.
    """
    if not description:
        return _empty_analysis()

    cleaned = clean_text(description)
    text_lower = description.lower()

    # Split into required vs preferred sections
    required_text, preferred_text = _split_required_preferred(description)

    required_skills = extract_skills(required_text or cleaned)
    preferred_skills = [s for s in extract_skills(preferred_text or '') if s not in required_skills]

    exp_years_min, exp_years_max = _extract_experience_range(description)
    education_name, education_score = extract_education_level(description)

    # Determine job level
    job_level = _classify_job_level(description, exp_years_min)

    # Key responsibilities
    responsibilities = _extract_bullets(description, ['responsibilities', 'duties', 'you will'])
    requirements_list = _extract_bullets(description, ['requirements', 'qualifications', 'required', 'must have'])

    return {
        'required_skills': required_skills,
        'preferred_skills': preferred_skills,
        'all_skills': list(set(required_skills + preferred_skills)),
        'experience_years_min': exp_years_min,
        'experience_years_max': exp_years_max,
        'education_level': education_name,
        'education_score': education_score,
        'job_level': job_level,
        'responsibilities': responsibilities,
        'requirements_list': requirements_list,
        'cleaned_text': cleaned,
    }


def _split_required_preferred(text: str) -> tuple:
    """Split job description into Required vs Preferred sections."""
    required_markers = ['required', 'must have', 'mandatory', 'essential', 'qualifications']
    preferred_markers = ['preferred', 'nice to have', 'bonus', 'plus', 'desired', 'optional']

    text_lower = text.lower()

    # Simple split approach: find section boundaries
    req_start = -1
    pref_start = -1

    for marker in required_markers:
        idx = text_lower.find(marker)
        if idx != -1 and (req_start == -1 or idx < req_start):
            req_start = idx

    for marker in preferred_markers:
        idx = text_lower.find(marker)
        if idx != -1 and (pref_start == -1 or idx < pref_start):
            pref_start = idx

    if req_start == -1:
        return text, ''

    if pref_start == -1 or pref_start < req_start:
        return text[req_start:], ''

    return text[req_start:pref_start], text[pref_start:]


def _extract_experience_range(text: str) -> tuple:
    """Extract min and max experience from job description."""
    patterns = [
        r'(\d+)\s*[-–to]+\s*(\d+)\s*years?\s+(?:of\s+)?(?:experience|exp)',
        r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:experience|exp)',
        r'minimum\s+(\d+)\s+years?',
        r'at\s+least\s+(\d+)\s+years?',
    ]
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return int(groups[0]), int(groups[1])
            elif len(groups) == 1:
                mn = int(groups[0])
                return mn, mn + 3
    return 0, 5


def _classify_job_level(text: str, min_exp: int) -> str:
    """Classify job as Junior / Mid-Level / Senior / Lead."""
    text_lower = text.lower()
    if any(w in text_lower for w in ['senior', 'sr.', 'principal', 'staff', 'lead']) or min_exp >= 5:
        return 'Senior'
    if any(w in text_lower for w in ['junior', 'jr.', 'entry', 'fresher', 'graduate', 'intern']) or min_exp == 0:
        return 'Junior'
    return 'Mid-Level'


def _extract_bullets(text: str, section_keywords: list) -> list:
    """Extract bullet points from a specific section."""
    text_lower = text.lower()
    for kw in section_keywords:
        idx = text_lower.find(kw)
        if idx != -1:
            section = text[idx:idx + 2000]
            lines = section.split('\n')
            bullets = []
            for line in lines[1:20]:
                line = line.strip()
                if line and (line.startswith(('-', '•', '*', '·', '►')) or
                             (len(line) > 10 and len(line) < 200)):
                    clean = re.sub(r'^[-•*·►]\s*', '', line).strip()
                    if clean:
                        bullets.append(clean)
            if bullets:
                return bullets[:10]
    return []


def _empty_analysis() -> dict:
    return {
        'required_skills': [], 'preferred_skills': [], 'all_skills': [],
        'experience_years_min': 0, 'experience_years_max': 5,
        'education_level': 'Bachelor\'s Degree', 'education_score': 3,
        'job_level': 'Mid-Level', 'responsibilities': [], 'requirements_list': [],
        'cleaned_text': '',
    }
