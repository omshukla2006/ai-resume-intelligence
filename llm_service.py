import json
import re
from typing import Any, Dict
from ..config import OPENAI_API_KEY, OPENAI_MODEL

SYSTEM_PROMPT = '''You are a senior resume analyst and technical recruiter assistant. Analyze a candidate resume against a job description with evidence-based reasoning.

Rules:
- Never invent experience, skills, metrics, employers, degrees, or achievements.
- Distinguish demonstrated skills from merely listed skills and missing evidence.
- Analyze the actual projects, experience, education and resume structure.
- Give specific recommendations tied to evidence in the supplied resume and requirements in the supplied job description.
- Rewrites must preserve factual truth. Do not add unsupported metrics.
- Interview questions should reference the candidate's actual projects/skills and the job gaps.
- Do not predict hiring outcomes.
- Return valid JSON only.
'''


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
        text = re.sub(r'\s*```$', '', text)
    start, end = text.find('{'), text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end+1]
    return json.loads(text)


def _skill_phrase(skill: str) -> str:
    return skill.replace('scikit-learn', 'Scikit-learn').replace('api', 'API')


def _experience_alignment(base: Dict[str, Any]) -> str:
    exp = base['resume_profile']['experience']
    jd = base['job_profile']
    if not exp:
        return 'No structured experience bullets were detected. Add concise role, responsibility, technology and outcome evidence so the analyzer can assess professional alignment.'
    tech = sorted({t for e in exp for t in e['technologies']})
    relevant = [s for s in base['matched_skills'] if s in tech or any(s in e['text'].lower() for e in exp)]
    missing = base['missing_skills'][:5]
    parts = [f"The resume contains {len(exp)} experience evidence item(s)."]
    if relevant:
        parts.append(f"Relevant evidence includes {', '.join(_skill_phrase(x) for x in relevant[:6])}.")
    if missing:
        parts.append(f"The experience section does not clearly evidence {', '.join(_skill_phrase(x) for x in missing)}.")
    if not any(e['has_result'] for e in exp):
        parts.append('Most experience bullets lack an explicit measurable outcome; add one only when it is factually available.')
    return ' '.join(parts)


def _project_alignment(base: Dict[str, Any]) -> str:
    projects = base['resume_profile']['projects']
    if not projects:
        return 'No clearly structured projects section was detected. Add 2–3 relevant projects with the problem, technology, your contribution and factual result.'
    names = [p['text'][:90] for p in projects[:3]]
    relevant = [s for s in base['matched_skills'] if any(s in p['text'].lower() for p in projects)]
    missing = base['missing_skills'][:5]
    result = f"The analyzer detected {len(projects)} project evidence item(s), including: {'; '.join(names)}."
    if relevant:
        result += f" The projects contain evidence for {', '.join(_skill_phrase(x) for x in relevant[:6])}."
    if missing:
        result += f" They do not clearly demonstrate {', '.join(_skill_phrase(x) for x in missing)} required by the job description."
    if not any(p['has_result'] for p in projects):
        result += ' Project bullets also lack clear measurable outcomes; add genuine metrics where available.'
    return result


def _ats_analysis(base: Dict[str, Any]) -> str:
    p = base['resume_profile']
    sections = [k for k, v in p['sections'].items() if v]
    strengths = ', '.join(s.title() for s in sections) or 'limited standard sections'
    flags = base['quality_flags']
    text = f"Detected standard sections: {strengths}. Contact checks: email={'present' if p['contact']['email'] else 'missing'}, phone={'present' if p['contact']['phone'] else 'missing'}, LinkedIn={'present' if p['contact']['linkedin'] else 'missing'}, GitHub={'present' if p['contact']['github'] else 'missing'}."
    if flags:
        text += ' Main ATS-quality issues detected: ' + ' '.join(flags[:4])
    else:
        text += ' No major structural issues were detected by the local checks.'
    return text


def _rewrite_examples(base: Dict[str, Any]) -> list[dict[str, str]]:
    examples = []
    for item in (base['resume_profile']['projects'] + base['resume_profile']['experience'])[:5]:
        original = item['text']
        if len(original) < 25:
            continue
        if item['has_action'] and item['has_result']:
            continue
        tech = ', '.join(item['technologies'][:4])
        prefix = 'Developed and implemented' if not re.search(r'\b(?:built|developed|implemented|designed|created|trained|deployed)\b', original, re.I) else ''
        improved = (prefix + (' ' if prefix else '') + original).strip()
        if tech and tech.lower() not in improved.lower():
            improved += f' using {tech}.'
        examples.append({'original': original, 'improved': improved, 'reason': 'Clarifies the action and technical evidence without inventing a metric.'})
    return examples[:4]


def fallback_analysis(base: Dict[str, Any], resume_text: str, jd_text: str) -> Dict[str, Any]:
    matched = base['matched_skills']
    missing = base['missing_skills']
    evidence = base.get('skill_evidence', {})
    demonstrated = [s for s in matched if evidence.get(s) == 'demonstrated']
    listed = [s for s in matched if evidence.get(s) == 'listed']

    strengths = []
    if demonstrated:
        strengths.append(f"The resume provides evidence beyond the Skills section for: {', '.join(_skill_phrase(s) for s in demonstrated[:6])}.")
    if listed:
        strengths.append(f"The resume explicitly lists: {', '.join(_skill_phrase(s) for s in listed[:6])}, although listing alone is weaker evidence than a project or experience example.")
    if base['resume_profile']['projects']:
        strengths.append(f"{len(base['resume_profile']['projects'])} project evidence item(s) were detected and can be used to demonstrate technical capability.")
    if not strengths:
        strengths.append('The resume has limited direct evidence matching the supplied job requirements.')

    gaps = []
    for s in missing[:10]:
        gaps.append(f"{_skill_phrase(s)} is requested by the job description but was not detected in the resume.")
    if not gaps:
        gaps.append('No major gaps were detected from the supported skill vocabulary; review the responsibility-level requirements as well.')

    actions = []
    if missing:
        actions.append(f"Address the highest-impact gaps first: {', '.join(_skill_phrase(s) for s in missing[:5])}. Only add a skill after you have actually learned or used it.")
    if base['resume_profile']['projects'] and not any(p['has_result'] for p in base['resume_profile']['projects']):
        actions.append('Strengthen project bullets with the problem solved, your technical contribution and a factual outcome or evaluation result.')
    if base['resume_profile']['experience'] and not any(e['has_result'] for e in base['resume_profile']['experience']):
        actions.append('Rewrite experience bullets around action + technology + outcome. Do not invent metrics.')
    actions.append('Move the most relevant skills and projects closer to the top of the resume and mirror job terminology only when it accurately describes existing evidence.')
    if not base['resume_profile']['contact']['linkedin']:
        actions.append('Add a LinkedIn URL if you use LinkedIn professionally.')

    questions = []
    projects = base['resume_profile']['projects']
    if projects:
        questions.append(f"Walk me through your project evidence: {projects[0]['text'][:100]} What was your technical contribution?")
    for s in missing[:3]:
        questions.append(f"The role requires {_skill_phrase(s)}. What practical evidence can you provide for this requirement?")
    if matched:
        questions.append(f"Explain how you used {_skill_phrase(matched[0])} in a real project or work task and what trade-offs you considered.")
    questions.append('Describe one technical decision in your most relevant project and explain why you made it.')
    questions.append('If a system worked in development but failed under production load, how would you diagnose and improve it?')

    score = base['score']
    summary = f"The resume has an estimated {score}/100 alignment with the supplied job description. Semantic relevance is {base['semantic_similarity']}%, explicit skill coverage is {base['skill_match']}%, and the analyzer found {len(missing)} skill gap(s). The score is an evidence-based resume-to-JD alignment measure, not a hiring prediction."
    return {
        'executive_summary': summary,
        'strengths': strengths[:5],
        'gaps': gaps,
        'experience_alignment': _experience_alignment(base),
        'project_alignment': _project_alignment(base),
        'ats_analysis': _ats_analysis(base),
        'priority_actions': actions[:6],
        'rewrite_examples': _rewrite_examples(base),
        'interview_questions': questions[:7],
        'ai_status': 'local evidence analysis',
    }


def generate_ai_analysis(base: Dict[str, Any], resume_text: str, jd_text: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return fallback_analysis(base, resume_text, jd_text)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        payload = {
            'deterministic_analysis': base,
            'resume': resume_text[:18000],
            'job_description': jd_text[:14000],
            'required_output': {
                'executive_summary': 'string', 'strengths': ['string'], 'gaps': ['string'],
                'experience_alignment': 'string', 'project_alignment': 'string', 'ats_analysis': 'string',
                'priority_actions': ['string'], 'rewrite_examples': [{'original': 'string', 'improved': 'string', 'reason': 'string'}],
                'interview_questions': ['string']
            }
        }
        response = client.responses.create(model=OPENAI_MODEL, instructions=SYSTEM_PROMPT, input=json.dumps(payload, ensure_ascii=False))
        result = _extract_json(response.output_text)
        result['ai_status'] = 'OpenAI reasoning layer'
        return result
    except Exception as exc:
        result = fallback_analysis(base, resume_text, jd_text)
        result['ai_status'] = f'AI provider unavailable; local evidence analysis used ({type(exc).__name__}).'
        return result
