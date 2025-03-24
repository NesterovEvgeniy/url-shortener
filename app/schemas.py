from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional
from datetime import datetime

class LinkBase(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None
    project: Optional[str] = None  

class LinkCreate(LinkBase):
    pass

class LinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None
    project: Optional[str] = None 

class Link(LinkBase):
    id: int
    short_code: str
    created_at: datetime
    last_accessed: Optional[datetime]
    access_count: int
    owner_id: Optional[int]

    class Config:
        orm_mode = True

# Схема для статистики ссылок 
class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    access_count: int
    last_accessed: Optional[datetime] = None

    class Config:
        orm_mode = True
        # json_encoders для datetime
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    links: list[Link] = []

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None