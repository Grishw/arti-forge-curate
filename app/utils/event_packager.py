import os
import json
import shutil
import zipfile
from typing import Dict, Any, List, Optional
import asyncio
from app.core.config import settings

class EventPackager:
    def __init__(self, event_folder: str):
        self.event_folder = event_folder
        self.models_dir = os.path.join(event_folder, "models")
        self.markers_dir = os.path.join(event_folder, "markers")
        self.previews_dir = os.path.join(event_folder, "previews")
        self.manifest_path = os.path.join(event_folder, "manifest.json")
        self.project_json_path = os.path.join(event_folder, "project.json")
        
        # Создаём поддиректории
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.markers_dir, exist_ok=True)
        os.makedirs(self.previews_dir, exist_ok=True)

    async def add_work(self, work_id: str, zip_path: str, display_settings: Dict[str, Any]) -> None:
        """
        Добавляет работу в папку события: копирует модель, маркеры, preview.
        """
        # Распаковываем zip во временную папку
        temp_dir = os.path.join(settings.storage_root, "temp_extract", f"work_{work_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        def extract():
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)
        
        await asyncio.to_thread(extract)
        
        try:
            # Копируем все .glb файлы в models/ с префиксом work_id_
            glb_files = []
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f.lower().endswith('.glb'):
                        src = os.path.join(root, f)
                        dest = os.path.join(self.models_dir, f"{work_id}_{f}")
                        shutil.copy2(src, dest)
                        glb_files.append(dest)
            
            # Копируем изображения (маркеры) в markers/ с префиксом work_id_
            marker_files = []
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f.lower().endswith(image_extensions):
                        # Пропускаем preview-изображения (обычно называются preview.*)
                        if 'preview' in f.lower():
                            continue
                        src = os.path.join(root, f)
                        dest = os.path.join(self.markers_dir, f"{work_id}_{f}")
                        shutil.copy2(src, dest)
                        marker_files.append(dest)
            
            # Копируем preview (если есть)
            preview_src = None
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if 'preview' in f.lower() and f.lower().endswith(('.png', '.jpg', '.jpeg')):
                        preview_src = os.path.join(root, f)
                        break
                if preview_src:
                    break
            
            preview_dest = None
            if preview_src:
                preview_dest = os.path.join(self.previews_dir, f"{work_id}_preview.png")
                shutil.copy2(preview_src, preview_dest)
            
            # После копирования обновляем manifest и project.json
            await self._update_manifest(work_id, display_settings, glb_files, marker_files, preview_dest)
            
        finally:
            # Очищаем временную папку
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def remove_work(self, work_id: str) -> None:
        """Удаляет все файлы работы из папки события."""
        # Удаляем файлы с префиксом work_id_
        for dir_path in [self.models_dir, self.markers_dir, self.previews_dir]:
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    if f.startswith(f"{work_id}_"):
                        os.remove(os.path.join(dir_path, f))
        
        # Обновляем manifest и project.json (убираем работу)
        await self._update_manifest_remove(work_id)

    async def _update_manifest(self, work_id: str, display_settings: Dict[str, Any],
                               glb_files: List[str], marker_files: List[str], preview_path: Optional[str]) -> None:
        """Обновляет manifest.json: добавляет или обновляет информацию о работе."""
        # Читаем текущий manifest, если есть
        manifest = {}
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        
        # Получаем метаданные работы из work.json
        from app.repositories.work_repository import WorkRepository
        work_repo = WorkRepository()
        work = await work_repo.get(work_id)
        if not work:
            raise ValueError(f"Work {work_id} not found")
        
        # Подготавливаем информацию о работе для манифеста
        work_entry = {
            "workId": work.id,
            "externalId": work.external_id,
            "name": work.name,
            "displaySettings": display_settings,
            "projectMetadata": work.metadata.get("project", {}),
            "files": {
                "models": [os.path.basename(p) for p in glb_files],
                "markers": [os.path.basename(p) for p in marker_files],
                "preview": os.path.basename(preview_path) if preview_path else None
            }
        }
        
        # Обновляем список работ в манифесте
        if "works" not in manifest:
            manifest["works"] = []
        
        # Удаляем старую запись, если есть
        manifest["works"] = [w for w in manifest["works"] if w["workId"] != work_id]
        manifest["works"].append(work_entry)
        
        # Обновляем временную метку
        from datetime import datetime
        manifest["generatedAt"] = datetime.utcnow().isoformat()
        
        # Сохраняем manifest
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        # Обновляем project.json
        await self._update_project_json(manifest)

    async def _update_manifest_remove(self, work_id: str) -> None:
        """Удаляет работу из manifest.json."""
        if not os.path.exists(self.manifest_path):
            return
        
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        manifest["works"] = [w for w in manifest.get("works", []) if w["workId"] != work_id]
        
        from datetime import datetime
        manifest["generatedAt"] = datetime.utcnow().isoformat()
        
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        # Обновляем project.json
        await self._update_project_json(manifest)

    async def _update_project_json(self, manifest: Dict[str, Any]) -> None:
        """
        Создаёт project.json на основе projectMetadata всех работ из manifest.
        Формат: { work_id: projectMetadata, ... }
        """
        project_data = {}
        for work_entry in manifest.get("works", []):
            work_id = work_entry.get("workId")
            project_meta = work_entry.get("projectMetadata", {})
            if work_id:
                project_data = project_meta
        
        with open(self.project_json_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)