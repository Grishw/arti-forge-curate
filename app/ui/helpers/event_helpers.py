# app/ui/helpers/event_helpers.py
from nicegui import ui
from ..api_client import post, put, delete

async def publish_event(event_id: str):
    """Опубликовать событие"""
    resp = await post(f'events/{event_id}/publish')
    if resp.status_code == 200:
        ui.notify('Событие опубликовано', type='positive')
        ui.navigate.to(f'/events/{event_id}')
    else:
        ui.notify(f'Ошибка публикации: {resp.text}', type='negative')

async def delete_event(event_id: str):
    """Удалить событие"""
    resp = await delete(f'events/{event_id}')
    if resp.status_code == 200:
        ui.notify('Событие удалено', type='positive')
        ui.navigate.to('/dashboard')
    else:
        ui.notify(f'Ошибка удаления: {resp.text}', type='negative')

async def update_event(event_id: str, data: dict):
    """Обновить событие"""
    resp = await put(f'events/{event_id}', json=data)
    if resp.status_code == 200:
        ui.notify('Событие обновлено', type='positive')
        ui.navigate.to(f'/events/{event_id}')
    else:
        ui.notify(f'Ошибка обновления: {resp.text}', type='negative')
        return False
    return True