from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# =========================
# Ответ специалиста
# =========================
class ResponseRead(BaseModel):
    id: int
    ticket_id: int
    responder_name: str
    status: str
    text: Optional[str] = None
    media_filename: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True  # обязательно для SQLAlchemy ORM в Pydantic 2.x
    }

class ResponseCreate(BaseModel):
    responder_name: str
    status: str
    text: Optional[str] = None

# =========================
# Тикет
# =========================
class TicketRead(BaseModel):
    id: int
    full_name: str
    contact: str
    description: str
    photo_filename: Optional[str] = None
    created_at: datetime
    response: Optional[ResponseRead] = None  # вложенный ответ

    model_config = {
        "from_attributes": True
    }

class TicketCreate(BaseModel):
    full_name: str
    contact: str
    description: str
