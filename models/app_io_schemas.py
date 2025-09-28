from datetime import datetime, timezone
from enum import Enum
from beanie import Document
from beanie.odm.fields import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any, List, Generator, Annotated, Literal
from fastapi import Form
from src.ai.ai_schemas.validation_utils import validate_password_strength


class APIKeys(BaseModel):
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None


class UserQuery(BaseModel):
    session_id: str
    user_query: str
    realtime_info: bool = True
    pro_reasoning: bool = False
    message_id: str = None
    retry: bool = False


class ResponseFeedback(BaseModel):
    message_id: str
    response_id: str
    liked: Optional[bool] = None
    feedback_tag: Optional[List[str]] = None
    human_feedback: Optional[str] = None


class StockDataRequest(BaseModel):
    ticker: str
    exchange_symbol: str
    period: Literal['1M', '3M', '6M', 'YTD', '1Y', '5Y', 'MAX']
    message_id: str
    id: Optional[str] = "id-no8-provided-by-frontend"


class Registration(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)
    
    @field_validator('full_name')
    @classmethod
    def validate_name(cls, full_name: str):
        if len(full_name) > 24:
            raise ValueError('Name too long')
        
        return full_name

class Login(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class ExportResponse(BaseModel):
    message_id: str
    format: Literal['pdf', 'md', 'docx']


class UpdateSessionAccess(BaseModel):
    session_id: str
    access_level: Literal['public', 'private']

class UpdateMessageAccess(BaseModel):
    session_id: str
    message_id: str
    access_level: Literal['public', 'private']

    

class StockPredictionRequest(BaseModel):
    company_name:str
    period: str = "1M"
    ticker: str
    exchange_symbol: str
    message_id: Optional[str] = None

class StockPredictionResponse(BaseModel):
    success: bool
    company_name: str
    ticker: str
    file_path: str
    prediction_results: Optional[Any]  
    error: Optional[str]
    messages: list



class RoleEnum(str, Enum):
    individual_investor = "Individual investor"
    financial_analyst = "Financial analyst"
    student_researcher = "Student / researcher"
    finance_educator = "Finance creator or educator"
    financial_advisor = "Financial advisor / planner"
    others = "Others"

class FinanceExperienceEnum(str, Enum):
    beginner = "Beginner"
    intermediate = "Intermediate"
    expert = "Expert"

class LearningStyleEnum(str, Enum):
    visual = "Visual"
    auditory = "Auditory"
    research = "Research"

class ToolsUsedEnum(str, Enum):
    chatgpt = "ChatGPT"
    claude = "Claude"
    perplexity = "Perplexity"
    others = "Others"

class OnboardingRequest(BaseModel):
    role: Optional[RoleEnum]
    finance_experience: Optional[FinanceExperienceEnum]
    learning_style: Optional[LearningStyleEnum]
    tools_used: Optional[List[ToolsUsedEnum]]
    insight_goal: Optional[str] = None


class Onboarding(Document):
    user_id: PydanticObjectId
    role: Optional[RoleEnum]
    finance_experience: Optional[FinanceExperienceEnum]
    learning_style: Optional[LearningStyleEnum]
    tools_used: Optional[List[ToolsUsedEnum]]
    insight_goal: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        collection = "onboarding"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            PydanticObjectId: str,
            datetime: lambda v: v.isoformat()
        }
