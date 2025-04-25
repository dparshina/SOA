from pydantic import BaseModel, Field, field_validator
from typing import List
import re

class PostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=30, description="Заголовок, от 3 до 30 символов")
    description: str = Field(..., min_length=10, max_length=100, description="Описание, от 10 до 100 символов")
    user_id: int
    is_private: bool
    tags: List[str] = Field(default_factory=list, description="Список тегов")
