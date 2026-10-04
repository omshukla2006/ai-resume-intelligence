import re
from typing import Any, Dict, List
from .skill_service import extract_skills

REQUIRED_MARKERS = ['required', 'requirements', 'must have', 'must-have', 'qualifications', 'you have', 'what you bring']
PREFERRED_MARKERS = ['preferred', 'nice to have', 'bonus', 'plus', 'good to have']


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if len(s.strip()) >= 25]


def _requirements(text: str) -> List[str]:
    items = []
    for line in text.splitlines():
        clean = line.strip(' •●▪◦-\t')
        if len(clean) >= 20 and re.search(r'\b(?:experience|knowledge|proficiency|proficient|familiarity|ability|build|develop|design|manage|work with|using|requires|required)\b', clean, flags=re.I):
            items.append(clean)
    if not items:
        items = [s for s in _sentences(text) if re.search(r'\b(?:experience|knowledge|proficiency|ability|build|develop|design|using|required)\b', s, flags=re.I)]
    return items[:20]


def extract_jd(text: str) -> Dict[str, Any]:
    skills = extract_skills(text)
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    lower = text.lower()
    required = []
    preferred = []
    current = 'general'
    for line in lines:
        ll = line.lower()
        if any(m in ll for m in REQUIRED_MARKERS): current = 'required'
        if any(m in ll for m in PREFERRED_MARKERS): current = 'preferred'
        if line.startswith(('-', '•', '●', '▪')) or len(line) > 25:
            if current == 'required': required.append(line.strip(' -•●▪'))
            elif current == 'preferred': preferred.append(line.strip(' -•●▪'))
    years = []
    for m in re.finditer(r'(\d+)\+?\s*(?:years?|yrs?)', text, flags=re.I):
        years.append(int(m.group(1)))
    seniority = 'unspecified'
    for label in ['intern', 'entry level', 'junior', 'mid-level', 'mid level', 'senior', 'lead', 'principal', 'manager']:
        if label in lower:
            seniority = label
            break
    return {
        'skills': skills,
        'requirements': _requirements(text),
        'required_items': required[:12],
        'preferred_items': preferred[:10],
        'experience_years': max(years) if years else None,
        'seniority': seniority,
        'responsibility_sentences': [s for s in _sentences(text) if re.search(r'\b(?:responsible|build|develop|design|maintain|deploy|analy[sz]e|collaborate|implement|create|manage)\b', s, flags=re.I)][:12],
    }
