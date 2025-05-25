from pydantic import BaseModel, EmailStr, validator
from typing import List


class ParseRequest(BaseModel):
    html_content: str
    emails: List[EmailStr]

    @validator('html_content')
    def validate_html_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('html_content must be a non-empty string')
        if len(v) > 50000:
            raise ValueError('html_content must not exceed 50000 characters')
        return v

    @validator('emails')
    def validate_emails(cls, v: List[EmailStr]) -> List[EmailStr]:
        if not v:
            raise ValueError('emails list must contain at least 1 email')
        if len(v) > 50:
            raise ValueError('emails list must not contain more than 50 emails')
        return v


class ParseResponse(BaseModel):
    email: EmailStr
    owner: str
