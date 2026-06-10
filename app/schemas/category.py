import uuid

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field("#000000", pattern="^#[0-9a-fA-F]{6}$")


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    color: str
    is_default: bool
    created_at: str

    model_config = {"from_attributes": True}
