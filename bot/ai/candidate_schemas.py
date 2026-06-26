from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any, TypedDict, Literal
from langgraph.graph import MessagesState

class JobSearchFilters(BaseModel):
    work_mode : Optional[str] = Field(
        None, description="Type of workplace. Opportunity: 'office', 'remote', 'hybrid'."
    )
    work_location: Optional[str] = Field(
        None, description="Location of work. City, Country"
    )
    experience_years: Optional[int] = Field(
        None, description="Experience candidate in years"
    )
    salary_expectations: Optional[int] = Field(
        None, description="Expectation about salary in USD."
    )
    skills: List[str] = Field(
        default_factory=List, description="List of skills that mention candidate in query (example: ['Python', 'FastAPI','PostgreSQL'])"
    )

class CandidateSearchQueryParsed(BaseModel):
    search_phrase: str = Field(
        ..., description="Cleaned and enriched semantic search string for vector embedding. Contains only roles and key tech."
    )
    filters: JobSearchFilters = Field(
        ..., description="Structured filters for precise SQL query."
    )

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
            raise ValueError("The field cannot be an empty string")
        return v

class CandidateState(MessagesState):
    vacancy_data: dict
    candidate: dict
    next_question: Optional[str]
    is_completed: bool = False
    asked_skills: List[str] = []

class ScreeningResponse(BaseModel):
    candidate_profile: CandidateProfile = Field(description="Updated candidate profile.")
    next_question: str = Field(description="ONE more question about the EMPTY field.")
    is_completed: bool = Field(description="Set this to true if ALL required and optional fields have been filled out.")
    just_asked_skill: Optional[str] = Field(
        None, 
        description="Which specific “nice-to-have” skill did you just check in this step?. If the question was about location or experience, leave it as “None.”"
    )

class CandidateVerdict(BaseModel):
    match_percentage: int = Field(
        ..., ge=0, le=100, description="Candidate's match percentage for the job opening: 0 to 100"
    )
    verdict: Literal["Hire", "No Hire"] = Field(
        ..., description="Final Recommendation on the Candidate"
    )
    matched_skills: List[str] = Field(
        ..., description="A list of the candidate's skills that fully meet the job requirements"
    )
    missing_skills: List[str] = Field(
        ..., description="Essential skills for the position that the candidate lacks or cannot demonstrate"
    )
    pros: List[str] = Field(
        ..., description="The candidate's strengths (experience, work style, GitHub profile)"
    )
    cons: List[str] = Field(
        ..., description="Weaknesses or potential risks (e.g., lack of experience)"
    )
    summary: str = Field(
        ..., description="A brief written explanation of the verdict (2–3 sentences)"
    )