import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from nicegui import ui
from app.ui import pages
from app.ui.theme import init_theme  

# Список обязательных JSON-файлов для хранения данных
REQUIRED_DATA_FILES = [
    "users.json",
    "authors.json",
    "works.json",
    "events.json",
    "collections.json",
    "event_works.json",
    "collection_works.json",
    "analytics.json",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём директории
    os.makedirs(settings.storage_root, exist_ok=True)
    os.makedirs(settings.data_root, exist_ok=True)
    for sub in ["zips", "events", "collections", "previews"]:
        os.makedirs(os.path.join(settings.storage_root, sub), exist_ok=True)

    # Инициализируем пустые JSON-файлы, если их нет
    for filename in REQUIRED_DATA_FILES:
        filepath = os.path.join(settings.data_root, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    yield
    # здесь можно добавить код завершения (пока не нужен)

app = FastAPI(
    title="ARTi Forge Curator API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS для разработки (позже можно сузить)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

previews_dir = "storage/previews"
if not os.path.exists(previews_dir):
    os.makedirs(previews_dir, exist_ok=True)

# Монтируем
app.mount("/previews", StaticFiles(directory=previews_dir), name="previews")

# Корневой эндпоинт для проверки
@app.get("/health")
async def health():
    return {"status": "ok"}

# Здесь позже подключим роутеры:
from app.api.v1.router import router as v1_router
app.include_router(v1_router, prefix="/api/v1")


init_theme()

@ui.page('/')
def main():
    ui.navigate.to('/ui/login')  # редирект на логин внутри UI

# Монтируем NiceGUI на путь /ui
ui.run_with(
    app,
    mount_path='/ui',  # важно: все страницы будут доступны по /ui/...
    storage_secret='ваш_секретный_ключ'
)