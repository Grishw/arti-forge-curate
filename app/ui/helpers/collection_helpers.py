# app/ui/helpers/collection_helpers.py
from nicegui import ui
from ..api_client import put, delete

async def delete_collection(collection_id: str):
    """Удалить коллекцию"""
    resp = await delete(f'collections/{collection_id}')
    if resp.status_code == 200:
        ui.notify('Коллекция удалена', type='positive')
        ui.navigate.to('/dashboard')
    else:
        ui.notify(f'Ошибка удаления: {resp.text}', type='negative')

async def update_collection(collection_id: str, data: dict):
    """Обновить коллекцию"""
    resp = await put(f'collections/{collection_id}', json=data)
    if resp.status_code == 200:
        ui.notify('Коллекция обновлена', type='positive')
        ui.navigate.to(f'/collections/{collection_id}')
    else:
        ui.notify(f'Ошибка обновления: {resp.text}', type='negative')
        return False
    return True