from typing import Dict, Any
from .skill_service import extract_skills
from .resume_parser import parse_resume
from .jd_service import extract_jd

_model = None


def semantic_similarity(resume_text: str, jd_text: str) -> float:
    global _model
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        if _model is None:
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = _model.encode([resume_text[:14000], jd_text[:14000]], normalize_embeddings=True)
        return max(0.0, min(1.0, float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])))
    except Exception:
        return 0.0


def _skill_evidence(skill: str, resume_text: str, parsed: Dict[str, Any]) -> str:
    low = resume_text.lower()
    count = low.count(skill.lower())
    section_text = parsed.get('section_text', {})
    skills_section = section_text.get('skills', '').lower()
    non_skill_mentions = max(0, count - skills_section.count(skill.lower()))
    if non_skill_mentions > 0:
        return 'demonstrated'
    if skill.lower() in skills_section:
        return 'listed'
    return 'weak'


def analyze_match(resume_text: str, jd_text: str) -> Dict[str, Any]:
    parsed = parse_resume(resume_text)
    jd = extract_jd(jd_text)
    resume_skills = extract_skills(resume_text)
    jd_skills = jd['skills']
    matched = sorted(set(resume_skills) & set(jd_skills))
    missing = sorted(set(jd_skills) - set(resume_skills))
    extra = sorted(set(resume_skills) - set(jd_skills))
    evidence = {s: _skill_evidence(s, resume_text, parsed) for s in matched}
    strong_matched = [s for s in matched if evidence[s] == 'demonstrated']

    skill_score = len(matched) / len(jd_skills) if jd_skills else 0.0
    evidence_score = (len(strong_matched) + 0.5 * (len(matched) - len(strong_matched))) / max(1, len(jd_skills))
    semantic = semantic_similarity(resume_text, jd_text)

    project_relevance = 0.0
    project_text = ' '.join(p['text'] for p in parsed['projects']).lower()
    if parsed['projects']:
        project_relevance = sum(1 for s in jd_skills if s in project_text) / max(1, len(jd_skills))
    experience_relevance = 0.0
    exp_text = ' '.join(e['text'] for e in parsed['experience']).lower()
    if parsed['experience']:
        experience_relevance = sum(1 for s in jd_skills if s in exp_text) / max(1, len(jd_skills))

    # Alignment score, not a hiring prediction. Keeps semantic similarity important but rewards evidence.
    score = round((0.42 * semantic + 0.30 * skill_score + 0.14 * project_relevance + 0.14 * experience_relevance) * 100, 1)

    quality_flags = []
    sections = parsed['sections']
    for key, label in [('summary', 'professional summary'), ('skills', 'skills'), ('projects', 'projects'), ('experience', 'experience'), ('education', 'education')]:
        if not sections.get(key):
            quality_flags.append(f'No clear {label} section detected.')
    if not parsed['contact']['email']: quality_flags.append('Email address was not detected.')
    if not parsed['contact']['phone']: quality_flags.append('Phone number was not detected.')
    if not parsed['contact']['linkedin']: quality_flags.append('LinkedIn profile was not detected.')
    if not parsed['contact']['github'] and any(s in jd_skills for s in ['github', 'git']):
        quality_flags.append('Git/GitHub is relevant to the target role, but a GitHub profile was not detected.')
    if parsed['word_count'] < 250: quality_flags.append('Resume text is unusually short; important evidence may be missing.')
    weak_projects = sum(1 for p in parsed['projects'] if not p['has_action'] or not p['has_result'])
    if parsed['projects'] and weak_projects == len(parsed['projects']):
        quality_flags.append('Project descriptions contain limited action/result evidence.')

    return {
        'score': score,
        'semantic_similarity': round(semantic * 100, 1),
        'skill_match': round(skill_score * 100, 1),
        'matched_skills': matched,
        'missing_skills': missing,
        'additional_skills': extra,
        'resume_skills': resume_skills,
        'job_skills': jd_skills,
        'skill_evidence': evidence,
        'sections': sections,
        'quality_flags': quality_flags,
        'resume_profile': parsed,
        'job_profile': jd,
        'evidence_score': round(evidence_score * 100, 1),
        'project_relevance': round(project_relevance * 100, 1),
        'experience_relevance': round(experience_relevance * 100, 1),
    }
