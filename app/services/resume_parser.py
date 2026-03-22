from ..utils.text_utils import (
    clean_text, extract_email, extract_phone, extract_name,
    extract_skills, extract_experience_years, extract_education_level,
    extract_job_titles,
)


def parse_resume(raw_text: str) -> dict:
    """
    Full resume parsing pipeline.
    Returns a structured dictionary of candidate information.
    """
    if not raw_text:
        return _empty_resume()

    cleaned = clean_text(raw_text)

    name = extract_name(raw_text)
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    skills = extract_skills(cleaned)
    experience_years = extract_experience_years(raw_text)
    education_name, education_score = extract_education_level(raw_text)
    job_titles = extract_job_titles(raw_text)
    summary = _generate_summary(name, skills, experience_years, education_name, job_titles)

    return {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'experience_years': experience_years,
        'education_level': education_name,
        'education_score': education_score,
        'job_titles': job_titles,
        'summary': summary,
        'cleaned_text': cleaned,
    }


def _generate_summary(name, skills, experience_years, education, job_titles) -> str:
    """Generate a brief textual summary of the candidate."""
    parts = []
    if name:
        parts.append(f"{name} is a")
    else:
        parts.append("Candidate is a")

    if experience_years > 0:
        parts.append(f"{experience_years:.0f}-year experienced professional")
    else:
        parts.append("professional")

    if job_titles:
        parts.append(f"with roles as {', '.join(job_titles[:3])}")

    if education and education != 'Not Specified':
        parts.append(f"holding a {education}")

    if skills:
        parts.append(f"skilled in {', '.join(skills[:8])}")

    return ' '.join(parts) + '.'


def _empty_resume() -> dict:
    return {
        'name': None, 'email': None, 'phone': None,
        'skills': [], 'experience_years': 0.0,
        'education_level': 'Not Specified', 'education_score': 0,
        'job_titles': [], 'summary': '',
        'cleaned_text': '',
    }
