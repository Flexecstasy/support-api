from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.database import Base, engine
from app.routes import router as api_router
from app.config import UPLOAD_DIR

app = FastAPI(title="Support API", version="0.1.0")

# подключим маршруты
app.include_router(api_router, prefix="")

# монтируем отдачу загрузок в /uploads
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.on_event("startup")
def on_startup():
    # таблицы при старте 
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}
