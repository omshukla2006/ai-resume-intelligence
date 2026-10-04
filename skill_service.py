import re
from typing import List

SKILLS = [
    'python','java','c++','c#','javascript','typescript','html','css','react','angular','vue','node.js','express',
    'fastapi','flask','django','sql','mysql','postgresql','mongodb','sqlite','redis','git','github','docker','kubernetes',
    'aws','azure','gcp','linux','rest api','graphql','pandas','numpy','matplotlib','seaborn','scikit-learn','tensorflow',
    'pytorch','keras','machine learning','deep learning','natural language processing','nlp','computer vision',
    'generative ai','llm','langchain','transformers','hugging face','rag','retrieval augmented generation','statistics',
    'data analysis','data visualization','power bi','tableau','excel','spark','hadoop','airflow','mlops','ci/cd',
    'streamlit','openai','api','oop','data structures','algorithms','problem solving','cloud computing'
]

ALIASES = {
    'scikit learn': 'scikit-learn', 'sklearn': 'scikit-learn', 'powerbi': 'power bi',
    'postgres': 'postgresql', 'mongo db': 'mongodb', 'natural language processing': 'natural language processing',
    'large language models': 'llm', 'large language model': 'llm', 'generative ai': 'generative ai'
}


def normalize(text: str) -> str:
    text = text.lower().replace('–', '-').replace('—', '-')
    for alias, canonical in ALIASES.items():
        text = re.sub(r'\b' + re.escape(alias) + r'\b', canonical, text)
    return re.sub(r'\s+', ' ', text)


def extract_skills(text: str) -> List[str]:
    normalized = normalize(text)
    found = []
    for skill in SKILLS:
        pattern = r'(?<![a-z0-9])' + re.escape(skill.lower()) + r'(?![a-z0-9])'
        if re.search(pattern, normalized):
            found.append(skill)
    return sorted(set(found))


def infer_sections(text: str):
    normalized = text.lower()
    patterns = {
        'summary': ['summary', 'profile', 'objective'],
        'skills': ['skills', 'technical skills', 'technologies'],
        'experience': ['experience', 'work experience', 'employment'],
        'education': ['education', 'academic'],
        'projects': ['projects', 'personal projects', 'academic projects'],
        'certifications': ['certifications', 'certificates'],
        'achievements': ['achievements', 'awards'],
    }
    return {section: any(k in normalized for k in keys) for section, keys in patterns.items()}
