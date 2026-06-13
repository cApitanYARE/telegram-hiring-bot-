from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any, TypedDict
from langgraph.graph import MessagesState

class CandidateProfile(BaseModel):
    #id_user: Optional[int] = Field(None, description="ID candidate")
    location: Optional[str] = Field(None, description="candidate location")
    work_mode: Optional[str] = Field(None, description="candidate work mode, like office,online, hybrid")
    skills: List[str] = Field(default_factory=list, description="list of candidate hard skils")
    github: Optional[str] = Field(default=None, description="Link to candiate GitHub")
    experience: Optional[float] = Field(None, description="candidate experience in years")

    @field_validator('location', 'work_mode', 'github')
    @classmethod
    def check_not_empty_str(cls, v: str) -> str:
        if v is None:
            return v

        if not v.strip():
            raise ValueError("Поле не може бути порожнім рядком")
        return v


class CandidateState(MessagesState):
    vacancy_data: dict
    candidate: dict
    next_question: Optional[str]
    is_completed: bool = False
    asked_skills: List[str] = []

class ScreeningResponse(BaseModel):
    candidate_profile: CandidateProfile = Field(description="Оновлений профіль кандидата.")
    next_question: str = Field(description="ОДНЕ наступне питання про ПОРОЖНЄ поле.")
    is_completed: bool = Field(description="Встанови в true, якщо ВСІ обов'язкові поля та nice-to-have опитано.")
    just_asked_skill: Optional[str] = Field(
        None, 
        description="Яку конкретно навичку з nice-to-have ти щойно перевірив у цьому кроці? (Наприклад: 'TypeScript', 'TailwindCSS/Bootstrap' або 'Figma'). Якщо питання стосувалося локації чи досвіду, залиш None."
    )