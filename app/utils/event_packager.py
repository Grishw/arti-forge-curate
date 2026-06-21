from datetime import datetime
import logging
import os
import json
import shutil
import zipfile
from typing import Dict, Any, List, Optional, Union
import asyncio
from app.core.config import settings
from app.repositories.event_repository import EventRepository


class EventPackager:
    def __init__(self, event_folder: str):
        self.event_folder = event_folder
        self.event_id = os.path.basename(event_folder)
        self.models_dir = os.path.join(event_folder, "models")
        self.markers_dir = os.path.join(event_folder, "markers")
        self.previews_dir = os.path.join(event_folder, "previews")
        self.manifest_path = os.path.join(event_folder, "manifest.json")
        self.project_json_path = os.path.join(event_folder, "project.json")
        
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.markers_dir, exist_ok=True)
        os.makedirs(self.previews_dir, exist_ok=True)

    async def _read_manifest_safe(self) -> Dict[str, Any]:
        if not os.path.exists(self.manifest_path):
            return {}
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"Manifest {self.manifest_path} corrupted, using empty dict")
            return {}

    # ------------------------------------------------------------------
    # Вспомогательная функция для рекурсивной замены путей
    # ------------------------------------------------------------------
    def _replace_paths_in_structure(self, obj: Any, mapping: Dict[str, str]) -> Any:
        """
        Рекурсивно обходит структуру (словари, списки, строки) и заменяет
        все строки, которые встречаются как ключи в mapping, на соответствующие значения.
        """
        if isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                # Если ключ — это потенциальный путь, заменяем и его
                new_key = mapping.get(key, key)
                new_dict[new_key] = self._replace_paths_in_structure(value, mapping)
            return new_dict
        elif isinstance(obj, list):
            return [self._replace_paths_in_structure(item, mapping) for item in obj]
        elif isinstance(obj, str):
            # Если строка совпадает с одним из путей — заменяем
            return mapping.get(obj, obj)
        else:
            return obj

    # ------------------------------------------------------------------
    # Добавление работы
    # ------------------------------------------------------------------
    async def add_work(self, work_id: str, zip_path: str, display_settings: Dict[str, Any]) -> None:
        temp_dir = os.path.join(settings.storage_root, "temp_extract", f"work_{work_id}")
        os.makedirs(temp_dir, exist_ok=True)

        def extract():
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)

        await asyncio.to_thread(extract)

        try:
            # 1. Читаем project.json из архива (если есть)
            project_json_path = os.path.join(temp_dir, "project.json")
            project_meta = {}
            if os.path.exists(project_json_path):
                with open(project_json_path, 'r', encoding='utf-8') as f:
                    project_meta = json.load(f)

            # 2. Копируем файлы и запоминаем отображение старых путей -> новые
            path_mapping = {}  # {старый относительный путь: новый относительный путь внутри папки события}

            # Модели (.glb)
            glb_files = []
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f.lower().endswith('.glb'):
                        src = os.path.join(root, f)
                        rel_path = os.path.relpath(src, temp_dir).replace('\\', '/')   # нормализация
                        new_name = f"{work_id}_{f}"
                        dest = os.path.join(self.models_dir, new_name)
                        shutil.copy2(src, dest)
                        glb_files.append(dest)
                        new_rel_path = os.path.join("models", new_name).replace('\\', '/')  # нормализация
                        path_mapping[rel_path] = new_rel_path

            # Маркеры (изображения, кроме preview)
            marker_files = []
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if f.lower().endswith(image_extensions) and 'preview' not in f.lower():
                        src = os.path.join(root, f)
                        rel_path = os.path.relpath(src, temp_dir).replace('\\', '/')
                        new_name = f"{work_id}_{f}"
                        dest = os.path.join(self.markers_dir, new_name)
                        shutil.copy2(src, dest)
                        marker_files.append(dest)
                        new_rel_path = os.path.join("markers", new_name).replace('\\', '/')
                        path_mapping[rel_path] = new_rel_path

            # Preview
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

            # 3. Обновляем пути в project_meta с помощью path_mapping
            if project_meta:
                project_meta = self._replace_paths_in_structure(project_meta, path_mapping)

            # 4. Обновляем манифест, передавая обновлённую project_meta
            await self._update_manifest(
                work_id=work_id,
                display_settings=display_settings,
                glb_files=glb_files,
                marker_files=marker_files,
                preview_path=preview_dest,
                project_metadata=project_meta
            )

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Удаление работы
    # ------------------------------------------------------------------
    async def remove_work(self, work_id: str) -> None:
        for dir_path in [self.models_dir, self.markers_dir, self.previews_dir]:
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    if f.startswith(f"{work_id}_"):
                        os.remove(os.path.join(dir_path, f))
        await self._update_manifest_remove(work_id)

    # ------------------------------------------------------------------
    # Обновление манифеста (добавление/обновление работы)
    # ------------------------------------------------------------------
    async def _update_manifest(
        self,
        work_id: str,
        display_settings: Dict[str, Any],
        glb_files: List[str],
        marker_files: List[str],
        preview_path: Optional[str],
        project_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        manifest = await self._read_manifest_safe()

        # Получаем данные события
        event_repo = EventRepository()
        event = await event_repo.get(self.event_id)
        if not event:
            raise ValueError(f"Event {self.event_id} not found")

        created_at = getattr(event, 'created_at', None)
        if created_at is None:
            created_at = datetime.utcnow().isoformat()
        elif hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()
        elif not isinstance(created_at, str):
            created_at = str(created_at)

        manifest["eventId"] = self.event_id
        manifest["eventName"] = event.name or "Untitled Event"
        manifest["description"] = event.description or ""
        manifest["createdAt"] = created_at
        manifest["lastModified"] = datetime.utcnow().isoformat()

        # Получаем базовую информацию о работе (из БД)
        from app.repositories.work_repository import WorkRepository
        work_repo = WorkRepository()
        work = await work_repo.get(work_id)
        if not work:
            raise ValueError(f"Work {work_id} not found")

        work_entry = {
            "workId": work.id,
            "externalId": work.external_id,
            "name": work.name,
            "displaySettings": display_settings,
            "projectMetadata": project_metadata,   # <-- обновлённая метадата
            "files": {
                "models": [os.path.basename(p) for p in glb_files],
                "markers": [os.path.basename(p) for p in marker_files],
                "preview": os.path.basename(preview_path) if preview_path else None
            }
        }

        if "works" not in manifest:
            manifest["works"] = []
        manifest["works"] = [w for w in manifest["works"] if w["workId"] != work_id]
        manifest["works"].append(work_entry)

        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        await self._update_project_json(manifest)
        return manifest

    # ------------------------------------------------------------------
    # Обновление манифеста (удаление работы)
    # ------------------------------------------------------------------
    async def _update_manifest_remove(self, work_id: str) -> Dict[str, Any]:
        manifest = await self._read_manifest_safe()
        if not manifest:
            return {}

        manifest["works"] = [w for w in manifest.get("works", []) if w["workId"] != work_id]
        manifest["lastModified"] = datetime.utcnow().isoformat()

        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        await self._update_project_json(manifest)
        return manifest

    # ------------------------------------------------------------------
    # Формирование итогового project.json из манифеста
    # ------------------------------------------------------------------
    async def _update_project_json(self, manifest: Dict[str, Any]) -> None:
        # Собираем все маркеры из projectMetadata всех работ
        all_markers = []
        for work_entry in manifest.get("works", []):
            project_meta = work_entry.get("projectMetadata", {})
            markers = project_meta.get("markers", [])
            if isinstance(markers, list):
                all_markers.extend(markers)

        project_data = {
            "projectId": manifest.get("eventId"),
            "projectName": manifest.get("eventName"),
            "description": manifest.get("description"),
            "createdAt": manifest.get("createdAt"),
            "lastModified": manifest.get("lastModified"),
            "markers": all_markers,
            "anchorSettings": {
                "type": 1,
                "planeType": 3,
                "enableImageTracking": True,
                "enablePlaneTracking": False,
                "maxNumberOfMovingImages": 4
            }
        }

        with open(self.project_json_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)