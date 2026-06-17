import os
import json
import uuid
import zipfile
import shutil
from typing import Dict, Any, Optional, Tuple
from fastapi import UploadFile
import asyncio
import aiofiles
from app.core.config import settings

async def read_work_metadata(zip_path: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Читает метаданные из zip-архива работы.
    Возвращает (metadata, preview_path_inside_zip).
    metadata содержит содержимое project.json и export.json.
    """
    # Используем asyncio.to_thread для блокирующих операций с zip
    def _read():
        metadata = {}
        preview_path = None
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Читаем project.json
            if 'project.json' in zf.namelist():
                with zf.open('project.json') as f:
                    metadata['project'] = json.load(f)
            # Читаем export.json
            if 'export.json' in zf.namelist():
                with zf.open('export.json') as f:
                    metadata['export'] = json.load(f)
            # Ищем preview (первый найденный)
            for name in zf.namelist():
                if name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    # Если есть previewImagePath из project.json, можно точнее
                    if 'project' in metadata:
                        preview_path_from_meta = metadata['project'].get('previewImagePath')
                        if preview_path_from_meta and preview_path_from_meta in zf.namelist():
                            preview_path = preview_path_from_meta
                            break
                    # Иначе берём первый попавшийся
                    if preview_path is None:
                        preview_path = name
        return metadata, preview_path

    # Запускаем в отдельном потоке
    return await asyncio.to_thread(_read)

async def read_zip_metadata(file: UploadFile, extract_to: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Асинхронно читает zip-архив, извлекает project.json и export.json,
    а также preview-изображение (если есть).
    Возвращает (metadata, preview_path)
    """
    # Сохраняем zip временно, чтобы открыть
    temp_zip_path = os.path.join(settings.storage_root, "zips", f"temp_{file.filename}")
    os.makedirs(os.path.dirname(temp_zip_path), exist_ok=True)
    
    # Сохраняем загруженный файл
    content = await file.read()
    with open(temp_zip_path, "wb") as f:
        f.write(content)
    
    # Распаковываем во временную папку
    extract_temp = os.path.join(settings.storage_root, "temp_extract")
    os.makedirs(extract_temp, exist_ok=True)
    
    # Распаковка в отдельном потоке
    def extract_zip():
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_temp)
    
    await asyncio.to_thread(extract_zip)
    
    # Читаем project.json и export.json
    project_json_path = os.path.join(extract_temp, "project.json")
    export_json_path = os.path.join(extract_temp, "export.json")
    
    metadata = {}
    if os.path.exists(project_json_path):
        with open(project_json_path, 'r', encoding='utf-8') as f:
            metadata["project"] = json.load(f)
    if os.path.exists(export_json_path):
        with open(export_json_path, 'r', encoding='utf-8') as f:
            metadata["export"] = json.load(f)
    
    # Ищем preview: обычно preview.png или preview.jpg в корне или в папке
    preview_path = None
    for root, dirs, files in os.walk(extract_temp):
        for file in files:
            if file.lower().startswith("preview") and file.lower().endswith((".png", ".jpg", ".jpeg")):
                preview_path = os.path.join(root, file)
                break
        if preview_path:
            break
    
    # Если нашли preview, копируем в storage/previews/ с уникальным именем
    saved_preview_path = None
    if preview_path:
        preview_filename = f"preview_{os.path.basename(file.filename)}.png"
        # или можно сгенерировать UUID
        import uuid
        preview_filename = f"{uuid.uuid4()}.png"
        dest_preview = os.path.join(settings.storage_root, "previews", preview_filename)
        shutil.copy2(preview_path, dest_preview)
        saved_preview_path = dest_preview
    
    # Очищаем временные файлы
    os.remove(temp_zip_path)
    shutil.rmtree(extract_temp, ignore_errors=True)
    
    return metadata, saved_preview_path

async def read_zip_metadata_from_file_path(zip_path: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Аналогично read_zip_metadata, но принимает путь к уже сохранённому zip-файлу.
    """
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Распаковываем
        def extract():
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        await asyncio.to_thread(extract)
        
        # Читаем project.json и export.json
        project_json_path = os.path.join(temp_dir, "project.json")
        export_json_path = os.path.join(temp_dir, "export.json")
        
        metadata = {}
        if os.path.exists(project_json_path):
            with open(project_json_path, 'r', encoding='utf-8') as f:
                metadata["project"] = json.load(f)
        if os.path.exists(export_json_path):
            with open(export_json_path, 'r', encoding='utf-8') as f:
                metadata["export"] = json.load(f)
        
        # Ищем preview
        preview_path = None
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().startswith("preview") and file.lower().endswith((".png", ".jpg", ".jpeg")):
                    preview_path = os.path.join(root, file)
                    break
            if preview_path:
                break
        
        saved_preview_path = None
        if preview_path:
            preview_filename = f"{uuid.uuid4()}.png"
            dest_preview = os.path.join(settings.storage_root, "previews", preview_filename)
            shutil.copy2(preview_path, dest_preview)
            saved_preview_path = dest_preview
        
        return metadata, saved_preview_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)