from __future__ import annotations
import re
import os


# ─── Comprehensive Tech & Domain Skills Database ─────────────────────────────
SKILLS_DATABASE = {
    # Programming Languages
    'languages': [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'go', 'golang',
        'rust', 'kotlin', 'swift', 'r', 'scala', 'php', 'ruby', 'perl', 'matlab',
        'bash', 'shell', 'powershell', 'lua', 'haskell', 'dart', 'elixir', 'julia',
        'fortran', 'cobol', 'assembly', 'vba', 'groovy', 'objective-c',
    ],
    # Web Technologies
    'web': [
        'html', 'css', 'html5', 'css3', 'react', 'reactjs', 'angular', 'angularjs',
        'vue', 'vuejs', 'nextjs', 'nuxtjs', 'svelte', 'jquery', 'bootstrap',
        'tailwindcss', 'webpack', 'vite', 'redux', 'graphql', 'rest', 'restful',
        'api', 'rest api', 'soap', 'websocket', 'flask', 'django', 'fastapi',
        'spring', 'spring boot', 'express', 'expressjs', 'node', 'nodejs', 'laravel',
        'rails', 'asp.net', '.net', 'blazor', 'gatsby', 'nuxt',
    ],
    # Machine Learning & AI
    'ml_ai': [
        'machine learning', 'deep learning', 'artificial intelligence', 'ai', 'ml',
        'neural networks', 'nlp', 'natural language processing', 'computer vision',
        'reinforcement learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
        'sklearn', 'xgboost', 'lightgbm', 'catboost', 'hugging face', 'transformers',
        'bert', 'gpt', 'llm', 'large language models', 'fine-tuning', 'rag',
        'stable diffusion', 'gan', 'cnn', 'rnn', 'lstm', 'attention mechanism',
        'sentence-bert', 'sbert', 'word2vec', 'glove', 'fasttext', 'embedding',
        'feature engineering', 'model deployment', 'mlops', 'a/b testing',
    ],
    # Data Science
    'data_science': [
        'data science', 'data analysis', 'data analytics', 'data mining',
        'statistics', 'statistical analysis', 'regression', 'classification',
        'clustering', 'dimensionality reduction', 'pca', 'pandas', 'numpy',
        'scipy', 'matplotlib', 'seaborn', 'plotly', 'tableau', 'power bi',
        'excel', 'r studio', 'jupyter', 'hypothesis testing', 'bayesian',
        'time series', 'forecasting', 'anomaly detection', 'etl',
    ],
    # Databases
    'databases': [
        'sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'mongodb', 'nosql',
        'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'oracle', 'mssql',
        'sql server', 'firebase', 'supabase', 'neo4j', 'influxdb', 'hbase',
        'database design', 'schema design', 'orm', 'sqlalchemy', 'hibernate',
        'indexing', 'query optimization',
    ],
    # Cloud & DevOps
    'cloud_devops': [
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
        'terraform', 'ansible', 'jenkins', 'ci/cd', 'github actions', 'gitlab ci',
        'devops', 'cloud computing', 'microservices', 'serverless', 'lambda',
        'ec2', 's3', 'rds', 'cloudformation', 'helm', 'prometheus', 'grafana',
        'nginx', 'apache', 'linux', 'unix', 'heroku', 'vercel', 'netlify',
    ],
    # Tools & Practices
    'tools': [
        'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'agile',
        'scrum', 'kanban', 'tdd', 'bdd', 'unit testing', 'pytest', 'junit',
        'selenium', 'playwright', 'cypress', 'postman', 'swagger', 'openapi',
        'vs code', 'intellij', 'pycharm', 'eclipse', 'vim', 'linux', 'ubuntu',
        'design patterns', 'solid principles', 'clean code', 'code review',
    ],
    # Soft Skills
    'soft_skills': [
        'communication', 'teamwork', 'leadership', 'problem solving', 'critical thinking',
        'time management', 'project management', 'presentation', 'mentoring',
        'analytical', 'collaborative', 'adaptable', 'self-motivated',
    ],
    # Domain Specific
    'domain': [
        'finance', 'banking', 'healthcare', 'ecommerce', 'fintech', 'edtech',
        'cybersecurity', 'security', 'networking', 'embedded systems', 'iot',
        'blockchain', 'web3', 'mobile development', 'android', 'ios',
        'game development', 'unity', 'unreal engine', 'ar', 'vr',
        'nlp', 'speech recognition', 'ocr', 'image processing',
    ],
}

ALL_SKILLS = []
for category_skills in SKILLS_DATABASE.values():
    ALL_SKILLS.extend(category_skills)

EDUCATION_LEVELS = {
    'phd': 5, 'ph.d': 5, 'doctorate': 5, 'doctoral': 5,
    'master': 4, 'mtech': 4, 'm.tech': 4, 'mba': 4, 'msc': 4, 'm.sc': 4, 'ms': 4, 'me': 4,
    'bachelor': 3, 'btech': 3, 'b.tech': 3, 'be': 3, 'bsc': 3, 'b.sc': 3, 'bs': 3, 'ba': 3, 'bca': 3,
    'diploma': 2, 'associate': 2,
    'high school': 1, 'secondary': 1, 'sslc': 1, 'hsc': 1,
}

EDUCATION_NAMES = {5: 'PhD / Doctorate', 4: 'Master\'s Degree', 3: 'Bachelor\'s Degree',
                   2: 'Diploma / Associate', 1: 'High School', 0: 'Not Specified'}


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ''
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special chars but keep alphanumeric, spaces, basic punctuation
    text = re.sub(r'[^\w\s\.\,\-\+\#\/\(\)\@]', ' ', text)
    return text.strip()


def extract_email(text: str) -> str | None:
    """Extract email from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Extract phone number from text."""
    pattern = r'(?:(?:\+|00)\d{1,3}[\s.-]*)?(?:\(?\d{2,4}\)?[\s.-]*)?\d{3,4}[\s.-]?\d{3,4}[\s.-]?\d{0,4}'
    matches = re.finditer(pattern, text)
    for match in matches:
        m = match.group(0).strip()
        cleaned = re.sub(r'[^\d+]', '', m)
        if 9 <= len(cleaned) <= 15:
            return m
    return None


def extract_name(text: str) -> str | None:
    """Extract candidate name (typically first 2-3 lines)."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:
        # Name lines are usually short and don't have special chars
        if 3 < len(line) < 60 and not any(c in line for c in ['@', 'http', '.com', '|', '/']):
            words = line.split()
            if 1 <= len(words) <= 5 and all(w[0].isupper() or '-' in w for w in words if w.isalpha()):
                # Verify the line is actually readable text (mostly letters/spaces)
                alpha_count = sum(1 for c in line if c.isalpha())
                if alpha_count >= len(line.replace(' ', '')) * 0.7:
                    return line
    # Don't return garbled first line — return None instead
    if lines:
        first = lines[0]
        alpha_count = sum(1 for c in first if c.isalpha())
        if alpha_count >= len(first.replace(' ', '')) * 0.7:
            return first
    return None



def extract_skills(text: str) -> list:
    """Extract skills from text using the skills database."""
    text_lower = text.lower()
    found_skills = set()

    for skill in ALL_SKILLS:
        # Handle symbols in skills properly so '\b' doesn't fail on "c++" or ".net"
        if not skill[0].isalnum():
            start_bound = r'(?:\s|^)'
        else:
            start_bound = r'\b'
            
        if not skill[-1].isalnum():
            end_bound = r'(?:\s|$)'
        else:
            end_bound = r'\b'
            
        pattern = start_bound + re.escape(skill) + end_bound
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    return sorted(list(found_skills))


def extract_experience_years(text: str) -> float:
    """Extract total years of experience from text."""
    patterns = [
        r'(\d+\.?\d*)\+?\s*years?\s+of\s+(?:experience|exp)',
        r'(\d+\.?\d*)\+?\s*years?\s+experience',
        r'experience[:\s]+(\d+\.?\d*)\+?\s*years?',
        r'(\d+\.?\d*)\+?\s*yrs?\s+(?:of\s+)?(?:experience|exp)',
        r'worked\s+for\s+(\d+\.?\d*)\s*years?',
        r'over\s+(\d+\.?\d*)\s*years?',
    ]
    years_found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                y = float(match)
                if 0 < y < 50:
                    years_found.append(y)
            except ValueError:
                pass

    if years_found:
        return max(years_found)

    # Try to calculate from date ranges (e.g., 2018-2022)
    date_pattern = r'(20\d{2})\s*[-–]\s*(20\d{2}|present|current|now)'
    date_ranges = re.findall(date_pattern, text, re.IGNORECASE)
    if date_ranges:
        import datetime
        current_year = datetime.datetime.now().year
        total = 0.0
        for start, end in date_ranges:
            start_yr = int(start)
            end_yr = current_year if end.lower() in ('present', 'current', 'now') else int(end)
            diff = end_yr - start_yr
            if 0 < diff < 30:
                total += diff
        if total > 0:
            return min(total, 30)

    return 0.0


def extract_education_level(text: str) -> tuple:
    """Extract highest education level from text. Returns (level_name, level_score)."""
    text_lower = text.lower()
    max_level = 0

    for keyword, level in EDUCATION_LEVELS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            max_level = max(max_level, level)

    return EDUCATION_NAMES.get(max_level, 'Not Specified'), max_level


def extract_job_titles(text: str) -> list:
    """Extract job titles/roles mentioned in resume."""
    common_titles = [
        'software engineer', 'software developer', 'full stack developer', 'frontend developer',
        'backend developer', 'data scientist', 'data analyst', 'data engineer', 'ml engineer',
        'machine learning engineer', 'ai engineer', 'devops engineer', 'sre', 'cloud engineer',
        'project manager', 'product manager', 'scrum master', 'tech lead', 'team lead',
        'architect', 'solution architect', 'system analyst', 'business analyst',
        'qa engineer', 'test engineer', 'web developer', 'mobile developer',
        'android developer', 'ios developer', 'ui developer', 'ux designer',
        'database administrator', 'dba', 'security engineer', 'network engineer',
        'research scientist', 'research engineer', 'nlp engineer',
        'intern', 'trainee', 'fresher',
    ]
    text_lower = text.lower()
    found = []
    for title in common_titles:
        if re.search(r'\b' + re.escape(title) + r'\b', text_lower):
            found.append(title.title())
    return found


def tokenize_sentences(text: str) -> list:
    """Simple sentence tokenizer."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]
