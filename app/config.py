import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv("DATABASE_URL")
# если DATABASE_URL не задан, используем SQLite в корне проекта для быстрого запуска
if not DATABASE_URL:
    PROJECT_ROOT = BASE_DIR.parent
    DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data.db'}"

# папка для хранения загруженных файлов
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# константы
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10 MB default

# если хотим строить абсолютные ссылки на файлы
BASE_API_URL = os.getenv("BASE_API_URL", "")  
