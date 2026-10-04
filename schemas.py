from pydantic import BaseModel, Field

class AnalysisResult(BaseModel):
    score: float
    semantic_similarity: float
    skill_match: float
    matched_skills: list[str]
    missing_skills: list[str]
    additional_skills: list[str]
