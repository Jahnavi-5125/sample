from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import uuid

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator
from src.ai.ai_schemas.validation_utils import validate_password_strength


class AuthMethod(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"


class AccountStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

class AccessLevel(str, Enum):
    PUBLIC = 'public'
    PRIVATE =  'private'
class QueryRequestModel(BaseModel):
    user_query : str
    session_id : str
    realtime_info : bool = True
    search_mode : Literal['fast', 'agentic-planner', 'agentic-reasoning', 'summarizer'] = 'fast' 
    retry_response : bool = False
    message_id : str
    prev_message_id : str
    timezone : str = "UTC"
    doc_ids : list = []
    is_elaborate: bool = False
    is_example: bool = False

    @field_validator('message_id')
    @classmethod
    def validate_message_id(cls, v):
        if not v or v == "":
            return str(uuid.uuid4())
        return v
class Users(Document):
    email: str
    full_name: str
    password: Optional[str] = None
    profile_picture: Optional[str] = None
    apple_id: Optional[str] = None
    auth_provider: AuthMethod = AuthMethod.LOCAL
    account_status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        collection = "users"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            PydanticObjectId: str,
            datetime: lambda v: v.isoformat(),
        }

    def to_dict(self) -> dict:
        """Convert model instance to dictionary with proper serialization"""
        data = self.model_dump(exclude={"password","id","auth_provider","account_status","last_updated"})
        data["created_at"] = self.created_at.isoformat(
        ) if self.created_at else None
        return data
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)
    
class EmailVerificationRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    purpose: Literal["registration", "password_reset"]

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    profile_picture: Optional[str] = None


class Personalization(Document):
    user_id: PydanticObjectId
    introduction: Optional[str] = None
    location: Optional[str] = None
    language: Optional[str] = "English"
    preferred_response_language: Optional[str] = "Automatic"
    autosuggest: bool = True
    email_notifications: bool = False
    ai_data_retention: bool = False
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


    class Settings:
        collection = "personalization"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            PydanticObjectId: str,
            datetime: lambda v: v.isoformat(),
        }

class PersonalizationRequest(BaseModel):
    introduction: Optional[str] = None
    location: Optional[str] = None
    language: Optional[str] = None
    preferred_response_language: Optional[str] = None
    autosuggest: Optional[bool] = None
    email_notifications: Optional[bool] = None
    ai_data_retention: Optional[bool] = None


class returnStatus(BaseModel):
    status: bool
    message: str
    result: Optional[Dict] = None

    def to_dict(self) -> dict:
        """Convert model instance to dictionary with proper serialization"""
        return self.model_dump(exclude_none=True)  # Exclude None values for cleaner output


class MessageLog(Document):
    session_id: str = Field(...)
    message_id: str = Field(...)
    human_input: Optional[dict] = None
    research: Optional[List[dict]] = []
    response: Optional[dict] = None
    # canvas_response: Optional[dict] = None
    sources: Optional[List[dict]] = None
    error: Optional[dict] = None
    stock_chart: Optional[List[dict]] = []
    map_layers: Optional[dict] = None
    metadata: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    time_taken: Optional[int] = 0
    access_level: AccessLevel = AccessLevel.PRIVATE

    class Settings:
        collection = "log_entries"


class MessageFeedback(Document):
    message_id: str = Field(...)
    response_id: str = Field(...)
    liked: Optional[bool] = None
    feedback_tag: Optional[List[List[str]]] = []
    human_feedback: Optional[List[str]] = []

    class Settings:
        collection = "message_feedback"

class SessionLog(Document):
    user_id: PydanticObjectId
    session_id: str = Field(...)
    title: str = Field(...)
    access_level: AccessLevel = AccessLevel.PRIVATE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timezone: Optional[str] = "UTC"
    visible: Optional[bool] = True

    class Settings:
        collection = "sessions"

    def to_dict(self) -> dict:
        """Convert model instance to dictionary with proper serialization"""
        data = self.dict()
        data["_id"] = str(self.id) if hasattr(self, "id") and self.id else None
        data["user_id"] = str(self.user_id)
        return data


class SessionHistory(Document):
    user_id: PydanticObjectId
    session_id: str = Field(...)
    title: Optional[str] = "New Chat"
    history: List[dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        collection = "session_histories"

    def to_dict(self) -> dict:
        data = self.model_dump()
        data["_id"] = str(self.id)
        data["user_id"] = str(self.user_id)
        return data


class MessageOutput(Document):
    user_id: PydanticObjectId
    session_id: str = Field(...)
    message_id: str = Field(...)
    state_data: Dict[str, Any]
    status: str = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        collection = "message_outputs"

    def to_dict(self) -> dict:
        data = self.model_dump()
        data["_id"] = str(self.id)
        data["user_id"] = str(self.user_id)
        return data


class JSONBackup(Document):
    filename: str
    data: dict
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        collection = "json_backup"


class CurrencyRates(BaseModel):
    symbols: str
    created_at: datetime

class ChatContext(BaseModel):
    name: str
    ticker: str
    exchange: str
    context_data: List[Dict]

class RelatedQueriesResponse(BaseModel):
    related_queries: List[str]

class ChartBotLogs(Document):
    user_id: PydanticObjectId
    session_id: str
    message_id: str
    user_input: str
    context: ChatContext
    response: str
    chat_session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        collection = "chart_bot_logs"


class SemiStaticData(Document):
    currency_rates: CurrencyRates = Field(...)

class ExternalData(Document):
    filename: str
    data: Any
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    class Settings:
        collection = "external_data"


class GraphLog(Document):
    session_id: str
    message_id: str
    logs: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "graph_logs"


class MapData(Document):
    session_id: str = Field(...)
    message_id: str = Field(...)
    data: Dict[str, Any] = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        collection = "map_data"


class UploadResponse(Document):
    user_id: str
    file_id: str
    original_filename: Optional[str] = None
    blob: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        collection = "user_uploads"

class CompanyProfile(Document):
    symbol: str = Field(...)
    data: List[Dict[str, Any]] # raw FMP profile data as-is
    last_updated: datetime

    class Settings:
        name = "company_profiles"
class FMPResult(BaseModel):
    symbol: str
    name: str
    currency: str
    stockExchange: str
    exchangeShortName: str

class FMPQueryResult(Document):
    query: str = Field(...)
    source: str = Field(default="https://financialmodelingprep.com/")
    results: List[FMPResult]
    timestamp: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "fmp_query_results"
class HistoricalData(Document):
    ticker: str
    period: str
    data: Dict  # FMP historical data
    last_updated: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "historical_data"

class FinancialStatement(Document):
    symbol: str
    statement_type: Literal["balance_sheet", "cash_flow", "income_statement"]
    period: Literal["annual"]
    data: List[dict]  # FMP returns a list of yearly statements
    last_updated: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "financial_statements"


class StockDataRequest(BaseModel):
    period: str
    message_id: str
    exchange_symbol: str
    ticker: str
    id: Optional[str] = None
