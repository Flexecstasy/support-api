from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas

def create_ticket(db: Session, ticket_in: schemas.TicketCreate, photo_filename: Optional[str] = None) -> models.Ticket:
    ticket = models.Ticket(
        full_name=ticket_in.full_name,
        contact=ticket_in.contact,
        description=ticket_in.description,
        photo_filename=photo_filename
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

def get_ticket(db: Session, ticket_id: int) -> Optional[models.Ticket]:
    return db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

def list_tickets(db: Session, skip: int = 0, limit: int = 100) -> List[models.Ticket]:
    return db.query(models.Ticket).order_by(models.Ticket.created_at.desc()).offset(skip).limit(limit).all()

def create_response(db: Session, ticket_id: int, response_in: schemas.ResponseCreate, media_filename: Optional[str] = None) -> models.Response:
    # проверим, есть ли уже ответ для этой заявки
    existing = db.query(models.Response).filter(models.Response.ticket_id == ticket_id).first()
    if existing:
        raise ValueError("Response for this ticket already exists")

    response = models.Response(
        ticket_id=ticket_id,
        responder_name=response_in.responder_name,
        status=response_in.status,
        text=response_in.text,
        media_filename=media_filename
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response

def get_response_by_ticket(db: Session, ticket_id: int) -> Optional[models.Response]:
    return db.query(models.Response).filter(models.Response.ticket_id == ticket_id).first()
