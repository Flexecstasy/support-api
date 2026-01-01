from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
import pathlib

from app import schemas, crud
from app.database import SessionLocal
from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE

router = APIRouter()


def get_db():
    """Dependency: получает DB-сессию и гарантирует её закрытие."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_upload_file(upload_file: Optional[UploadFile], upload_dir: str) -> Optional[str]:
    """
    Сохраняет UploadFile в upload_dir и возвращает имя сохранённого файла.
    Возвращает None если upload_file is None.
    Бросает HTTPException с кодом 413 при превышении размера и 500 при IO-ошибке.
    """
    if upload_file is None:
        return None

    # убеждаемся, что папка существует
    pathlib.Path(upload_dir).mkdir(parents=True, exist_ok=True)

    safe_original = os.path.basename(upload_file.filename or "upload")
    filename = f"{uuid.uuid4().hex}_{safe_original}"
    dest_path = os.path.join(upload_dir, filename)

    try:
        # копируем содержимое из временного файла в целевой файл
        with open(dest_path, "wb") as buffer:
            # shutil.copyfileobj корректно копирует большие файлы по потокам
            shutil.copyfileobj(upload_file.file, buffer)
    except Exception as exc:
        # попытка удалить частично записанный файл
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла: {str(exc)}")
    finally:
        # гарантируем закрытие временного файла
        try:
            upload_file.file.close()
        except Exception:
            pass

    # проверяем размер записанного файла
    try:
        size = os.path.getsize(dest_path)
    except Exception as exc:
        # не удалось прочитать размер — удалим файл и вернём 500
        try:
            os.remove(dest_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Не удалось проверить размер файла: {str(exc)}")

    if size > MAX_UPLOAD_SIZE:
        try:
            os.remove(dest_path)
        except Exception:
            pass
        raise HTTPException(status_code=413, detail="Uploaded file is too large")

    return filename


@router.post("/tickets/", response_model=schemas.TicketRead, status_code=201)
async def create_ticket(
    full_name: str = Form(...),
    contact: str = Form(...),
    description: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Создание тикета. Опционально — загрузка файла (photo).
    Возвращает TicketRead; если файл загружен, в поле photo_filename возвращается путь /uploads/<filename>.
    """
    photo_filename = None
    if photo:
        photo_filename = save_upload_file(photo, UPLOAD_DIR)

    ticket_in = schemas.TicketCreate(full_name=full_name, contact=contact, description=description)
    try:
        ticket = crud.create_ticket(db, ticket_in, photo_filename=photo_filename)
    except Exception as exc:
        # если сохранение в БД провалилось — удалим загруженный файл (чтобы не накапливать мусор)
        if photo_filename:
            try:
                os.remove(os.path.join(UPLOAD_DIR, photo_filename))
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Ошибка при создании заявки: {str(exc)}")

    # подготовим ответ с путём к файлу
    ticket_dict = schemas.TicketRead.from_orm(ticket).dict()
    if ticket.photo_filename:
        ticket_dict["photo_filename"] = f"/uploads/{ticket.photo_filename}"
    return ticket_dict


@router.get("/tickets/", response_model=List[schemas.TicketRead])
def get_tickets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Получить список тикетов. Вложенный ответ (response) включён, если есть.
    Пути до файлов возвращаются в виде /uploads/<filename>.
    """
    tickets = crud.list_tickets(db, skip=skip, limit=limit)
    result = []
    for t in tickets:
        t_dict = schemas.TicketRead.from_orm(t).dict()
        if t.photo_filename:
            t_dict["photo_filename"] = f"/uploads/{t.photo_filename}"
        if t.response:
            resp = schemas.ResponseRead.from_orm(t.response).dict()
            if resp.get("media_filename"):
                resp["media_filename"] = f"/uploads/{resp['media_filename']}"
            t_dict["response"] = resp
        result.append(t_dict)
    return result


@router.get("/tickets/{ticket_id}", response_model=schemas.TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Получить один тикет по id вместе с ответом (если есть).
    """
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    t_dict = schemas.TicketRead.from_orm(ticket).dict()
    if ticket.photo_filename:
        t_dict["photo_filename"] = f"/uploads/{ticket.photo_filename}"
    if ticket.response:
        resp = schemas.ResponseRead.from_orm(ticket.response).dict()
        if resp.get("media_filename"):
            resp["media_filename"] = f"/uploads/{resp['media_filename']}"
        t_dict["response"] = resp
    return t_dict


@router.post("/tickets/{ticket_id}/response", response_model=schemas.ResponseRead, status_code=201)
async def add_response(
    ticket_id: int,
    responder_name: str = Form(...),
    status: str = Form(...),
    text: Optional[str] = Form(None),
    media: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Добавление ответа специалиста к тикету.
    Один ответ на тикет (если уже есть — вернётся 400).
    Опционально можно загрузить файл (media).
    """
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    media_filename = None
    if media:
        media_filename = save_upload_file(media, UPLOAD_DIR)

    response_in = schemas.ResponseCreate(responder_name=responder_name, status=status, text=text)
    try:
        response_obj = crud.create_response(db, ticket_id, response_in, media_filename=media_filename)
    except ValueError as ve:
        # уже есть ответ на заявку
        # удаляем загруженный файл (чтобы не оставлять мусор)
        if media_filename:
            try:
                os.remove(os.path.join(UPLOAD_DIR, media_filename))
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        #ошибка при сохранении в БД
        if media_filename:
            try:
                os.remove(os.path.join(UPLOAD_DIR, media_filename))
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении ответа: {str(exc)}")

    resp_dict = schemas.ResponseRead.from_orm(response_obj).dict()
    if resp_dict.get("media_filename"):
        resp_dict["media_filename"] = f"/uploads/{resp_dict['media_filename']}"
    return resp_dict
