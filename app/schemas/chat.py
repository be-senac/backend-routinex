import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    total: int
    page: int
    page_size: int


class DecomposeRequest(BaseModel):
    project_description: str = Field(..., min_length=1)


class DecomposeResponse(BaseModel):
    tasks: list[dict]
    message: str


class SuggestRoutineRequest(BaseModel):
    preferences: str = Field(..., min_length=1)


class SuggestRoutineResponse(BaseModel):
    routine: dict
    message: str
