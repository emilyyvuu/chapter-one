from pydantic import BaseModel
from typing import Optional

class Books(BaseModel):
    google_books_id: str
    title: Optional[str] = None
    author: list[str] = []
    description: Optional[str] = None
    cover_url: Optional[str] = None