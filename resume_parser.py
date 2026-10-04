import re
from typing import Any, Dict, List

SECTION_ALIASES = {
    'summary': ['summary', 'professional summary', 'profile', 'objective', 'career objective', 'about me'],
    'skills': ['skills', 'technical skills', 'core skills', 'technologies', 'technical expertise', 'skills & technologies'],
    'experience': ['experience', 'work experience', 'professional experience', 'employment', 'work history', 'internship', 'internships'],
    'projects': ['projects', 'personal projects', 'academic projects', 'key projects', 'project experience'],
    'education': ['education', 'academic background', 'academic qualifications', 'qualifications'],
    'certifications': ['certifications', 'certificates', 'licenses'],
    'achievements': ['achievements', 'awards', 'honors'],
}

HEADING_MAP = {alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases}


def clean_lines(text: str) -> List[str]:
    lines = []
    for raw in text.replace('\r', '\n').split('\n'):
        line = re.sub(r'\s+', ' ', raw).strip(' \t•●▪◦-')
        if line:
            lines.append(line)
    return lines


def is_heading(line: str) -> str | None:
    low = re.sub(r'[^a-z& ]', '', line.lower()).strip()
    low = re.sub(r'\s+', ' ', low)
    if low in HEADING_MAP:
        return HEADING_MAP[low]
    if len(low.split()) <= 5:
        for alias, section in HEADING_MAP.items():
            if low == alias:
                return section
    return None


def extract_sections(text: str) -> Dict[str, str]:
    lines = clean_lines(text)
    sections = {k: '' for k in SECTION_ALIASES}
    current = 'other'
    buckets: Dict[str, List[str]] = {'other': []}
    for line in lines:
        heading = is_heading(line)
        if heading:
            current = heading
            buckets.setdefault(current, [])
            continue
        buckets.setdefault(current, []).append(line)
    for key in sections:
        sections[key] = '\n'.join(buckets.get(key, [])).strip()
    sections['other'] = '\n'.join(buckets.get('other', [])).strip()
    return sections


def _split_bullets(text: str) -> List[str]:
    if not text:
        return []
    parts = []
    for line in text.split('\n'):
        line = line.strip(' •●▪◦-')
        if len(line) >= 25:
            parts.append(line)
    return parts


def extract_contact(text: str) -> Dict[str, Any]:
    emails = re.findall(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', text, flags=re.I)
    phones = re.findall(r'(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)', text)
    links = re.findall(r'https?://[^\s)]+|(?:www\.)?(?:linkedin\.com|github\.com)/[^\s)]+', text, flags=re.I)
    low = text.lower()
    return {
        'email': bool(emails),
        'phone': bool(phones),
        'linkedin': 'linkedin.com' in low,
        'github': 'github.com' in low,
        'email_value': emails[0] if emails else '',
    }


def extract_projects(sections: Dict[str, str]) -> List[Dict[str, Any]]:
    bullets = _split_bullets(sections.get('projects', ''))
    if not bullets and sections.get('projects'):
        bullets = [x.strip() for x in re.split(r'(?=\b(?:project|developed|built|created|designed)\b)', sections['projects'], flags=re.I) if len(x.strip()) >= 25][:10]
    projects = []
    for item in bullets[:12]:
        tech = re.findall(r'\b(?:Python|Java|C\+\+|JavaScript|TypeScript|React|Node\.js|Express|Django|Flask|FastAPI|SQL|MySQL|MongoDB|Pandas|NumPy|Scikit-learn|TensorFlow|PyTorch|HTML|CSS|Git|Docker|AWS|Azure|GCP|OpenAI|LLM|NLP|REST API)\b', item, flags=re.I)
        projects.append({
            'text': item,
            'technologies': sorted(set(x.lower() for x in tech)),
            'has_result': bool(re.search(r'\b(?:increased|reduced|improved|achieved|accuracy|precision|recall|f1|users|downloads|%|seconds|ms|x faster|score)\b', item, flags=re.I)),
            'has_action': bool(re.search(r'\b(?:built|developed|created|implemented|designed|trained|deployed|automated|engineered|integrated|developed)\b', item, flags=re.I)),
        })
    return projects


def extract_experience(sections: Dict[str, str]) -> List[Dict[str, Any]]:
    bullets = _split_bullets(sections.get('experience', ''))
    entries = []
    for item in bullets[:15]:
        tech = re.findall(r'\b(?:Python|Java|C\+\+|JavaScript|TypeScript|React|Node\.js|Express|Django|Flask|FastAPI|SQL|MySQL|MongoDB|Pandas|NumPy|Scikit-learn|TensorFlow|PyTorch|HTML|CSS|Git|Docker|AWS|Azure|GCP|OpenAI|LLM|NLP|REST API)\b', item, flags=re.I)
        entries.append({
            'text': item,
            'technologies': sorted(set(x.lower() for x in tech)),
            'has_result': bool(re.search(r'\b(?:increased|reduced|improved|achieved|saved|optimized|accuracy|precision|recall|%|users|revenue|cost)\b', item, flags=re.I)),
            'has_action': bool(re.search(r'\b(?:built|developed|created|implemented|designed|trained|deployed|automated|engineered|integrated|managed|led)\b', item, flags=re.I)),
        })
    return entries


def extract_education(sections: Dict[str, str]) -> List[str]:
    return [x for x in clean_lines(sections.get('education', '')) if len(x) >= 4][:10]


def parse_resume(text: str) -> Dict[str, Any]:
    sections = extract_sections(text)
    contact = extract_contact(text)
    projects = extract_projects(sections)
    experience = extract_experience(sections)
    education = extract_education(sections)
    return {
        'sections': {k: bool(v) for k, v in sections.items() if k != 'other'},
        'section_text': sections,
        'contact': contact,
        'projects': projects,
        'experience': experience,
        'education_items': education,
        'word_count': len(text.split()),
    }
