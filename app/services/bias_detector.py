"""
Bias Detection Module
Detects gender-coded, ageist, and exclusionary language in job descriptions.
Based on research showing that biased JD language reduces diverse applicant pools.
"""
import re

# Gender-coded masculine words (tend to deter women)
MASCULINE_CODED = [
    'aggressive', 'ambitious', 'analytical', 'assertive', 'autonomous',
    'battle', 'boast', 'challenge', 'champion', 'compete', 'competitive',
    'confident', 'courageous', 'decisive', 'determine', 'dominate',
    'driven', 'fearless', 'force', 'head-strong', 'headstrong',
    'hero', 'independent', 'lead', 'leader', 'logic', 'ninja',
    'objective', 'outspoken', 'rock star', 'rockstar', 'self-reliant',
    'self-sufficient', 'strong', 'superior', 'warrior', 'win',
]

# Gender-coded feminine words (tend to deter men — less harmful but still notable)
FEMININE_CODED = [
    'collaborative', 'committed', 'connect', 'considerate', 'cooperative',
    'depend', 'empathy', 'feel', 'flatter', 'gentle', 'honest',
    'inclusive', 'interpersonal', 'kind', 'loyal', 'nurture',
    'pleasant', 'polite', 'quiet', 'responsible', 'sensitive',
    'share', 'sincere', 'support', 'sympathetic', 'together',
    'trust', 'understand', 'warm', 'yield',
]

# Ageist terms
AGEIST_TERMS = [
    'young', 'digital native', 'recent graduate', 'fresh graduate', 'new grad',
    'energy of youth', 'young professional', 'early career only',
]

# Exclusionary terms
EXCLUSIONARY = [
    'native speaker', 'native english', 'born in', 'citizen only',
    'local candidates only', 'men preferred', 'women preferred',
    'must be available on weekends', 'no disability',
]

# Suggestions for masculine-coded terms
SUGGESTIONS = {
    'aggressive': 'results-driven',
    'ninja': 'expert',
    'rock star': 'talented professional',
    'rockstar': 'talented professional',
    'warrior': 'dedicated professional',
    'hero': 'skilled professional',
    'dominate': 'lead',
    'battle': 'challenge',
    'fearless': 'confident',
    'headstrong': 'determined',
}


def detect_bias(text: str) -> dict:
    """
    Detect bias in job description text.
    Returns flags, suggestions, and a bias score (0=unbiased, 100=heavily biased).
    """
    if not text:
        return {'flags': [], 'score': 0.0, 'suggestions': [], 'summary': 'No text provided.'}

    text_lower = text.lower()
    flags = []
    suggestions = []

    # Check masculine-coded words
    masc_found = []
    for word in MASCULINE_CODED:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            masc_found.append(word)
            if word in SUGGESTIONS:
                suggestions.append({
                    'term': word,
                    'suggestion': SUGGESTIONS[word],
                    'type': 'masculine_coded',
                })

    if masc_found:
        flags.append({
            'type': 'masculine_coded_language',
            'severity': 'medium' if len(masc_found) <= 3 else 'high',
            'terms': masc_found,
            'description': f'Masculine-coded words detected: {", ".join(masc_found[:5])}. '
                           f'These may discourage female applicants.',
        })

    # Check feminine-coded words
    fem_found = []
    for word in FEMININE_CODED:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            fem_found.append(word)

    if fem_found and len(fem_found) > 5:
        flags.append({
            'type': 'feminine_coded_language',
            'severity': 'low',
            'terms': fem_found,
            'description': f'High concentration of feminine-coded words: {", ".join(fem_found[:5])}.',
        })

    # Check ageist terms
    age_found = [t for t in AGEIST_TERMS if re.search(r'\b' + re.escape(t) + r'\b', text_lower)]
    if age_found:
        flags.append({
            'type': 'ageist_language',
            'severity': 'high',
            'terms': age_found,
            'description': f'Potentially ageist language: {", ".join(age_found)}.',
        })
        suggestions.append({
            'term': ', '.join(age_found),
            'suggestion': 'Use "all experience levels welcome" or focus on skills instead',
            'type': 'ageist',
        })

    # Check exclusionary terms
    excl_found = [t for t in EXCLUSIONARY if re.search(re.escape(t), text_lower)]
    if excl_found:
        flags.append({
            'type': 'exclusionary_language',
            'severity': 'critical',
            'terms': excl_found,
            'description': f'Exclusionary language found: {", ".join(excl_found)}. May violate equal opportunity guidelines.',
        })

    # Compute bias score
    severity_weights = {'low': 5, 'medium': 20, 'high': 35, 'critical': 50}
    raw_score = sum(severity_weights.get(f['severity'], 10) for f in flags)
    bias_score = min(raw_score, 100.0)

    # Overall summary
    if bias_score == 0:
        summary = 'No significant bias detected. The job description appears inclusive.'
    elif bias_score < 20:
        summary = 'Minor bias indicators found. Minor language adjustments recommended.'
    elif bias_score < 50:
        summary = 'Moderate bias detected. Consider revising highlighted terms to attract diverse talent.'
    else:
        summary = 'High bias risk. Significant revision recommended to ensure fair candidate pool.'

    return {
        'flags': flags,
        'score': round(bias_score, 1),
        'suggestions': suggestions,
        'summary': summary,
        'masculine_count': len(masc_found),
        'feminine_count': len(fem_found),
    }
