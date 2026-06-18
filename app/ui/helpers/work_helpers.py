# app/ui/helpers/work_helpers.py
from nicegui import ui
from ..api_client import post, put, delete
from ..dialogs import display_settings_dialog

async def add_work_to_container(container_id: str, container_type: str, work_id: str, settings: dict, status: str):
    """
    Добавляет работу в событие или коллекцию.
    container_type: 'events' или 'collections'
    """
    endpoint = f'{container_type}/{container_id}/works'
    data = {
        'work_id': work_id,
        'display_settings': settings,
        'status': status,
    }
    # Для коллекций бэкенд может ожидать collection_id в теле, добавим если нужно
    if container_type == 'collections':
        data['collection_id'] = container_id
    resp = await post(endpoint, json=data)
    if resp.status_code == 200:
        ui.notify('Работа добавлена', type='positive')
        ui.navigate.to(f'/{container_type}/{container_id}')
    else:
        ui.notify(f'Ошибка: {resp.text}', type='negative')

async def update_work_in_container(container_id: str, container_type: str, work_id: str, settings: dict, status: str):
    endpoint = f'{container_type}/{container_id}/works/{work_id}'
    data = {'display_settings': settings, 'status': status}
    resp = await put(endpoint, json=data)
    if resp.status_code == 200:
        ui.notify('Настройки обновлены', type='positive')
        ui.navigate.to(f'/{container_type}/{container_id}')
    else:
        ui.notify(f'Ошибка: {resp.text}', type='negative')

async def remove_work_from_container(container_id: str, container_type: str, work_id: str):
    endpoint = f'{container_type}/{container_id}/works/{work_id}'
    resp = await delete(endpoint)
    if resp.status_code == 200:
        ui.notify('Работа удалена', type='positive')
        ui.navigate.to(f'/{container_type}/{container_id}')
    else:
        ui.notify(f'Ошибка: {resp.text}', type='negative')