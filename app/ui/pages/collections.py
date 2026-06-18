# app/ui/pages/collections.py
from nicegui import app, ui
from ..theme import page

from ..api_client import get, post
from ..dialogs import (
    confirm_dialog,
    select_work_dialog,
    display_settings_dialog,
    collection_edit_dialog   # <-- добавляем
)
from ..components import event_work_item
from ..helpers import (
    add_work_to_container,
    update_work_in_container,
    remove_work_from_container,
    delete_collection,
    update_collection
)

# ... страница создания коллекции ...
@ui.page('/collections/new')
async def create_collection_page():
    if not app.storage.user.get('token'):
        ui.navigate.to('/login')
        return
    ui.label('Создание коллекции').classes('text-h4')
    with ui.card():
        name = ui.input('Название', placeholder='Введите название коллекции').props('outlined')
        description = ui.textarea('Описание', placeholder='Описание коллекции').props('outlined')
        event_select = ui.select([], label='Привязать к событию (опционально)', with_input=True)
        error = ui.label().classes('text-negative')

        async def load_events():
            resp = await get('events/')
            if resp.status_code == 200:
                events = resp.json()
                options = {ev['id']: ev['name'] for ev in events}
                event_select.options = options
                event_select.value = None
        await load_events()

        async def do_create():
            data = {
                'name': name.value,
                'description': description.value,
                'event_id': event_select.value,
            }
            resp = await post('collections/', json=data)
            if resp.status_code == 200:
                collection = resp.json()
                ui.notify('Коллекция создана', type='positive')
                ui.navigate.to(f'/collections/{collection["id"]}')
            else:
                error.text = f'Ошибка: {resp.text}'

        ui.button('Создать', on_click=do_create).props('outline')
        ui.button('Отмена', on_click=lambda: ui.navigate.to('/dashboard'))

@ui.page('/collections/{collection_id}')
async def collection_page(collection_id: str):
    if not app.storage.user.get('token'):
        ui.navigate.to('/login')
        return

    resp = await get(f'collections/{collection_id}')
    if resp.status_code != 200:
        ui.notify('Коллекция не найдена', type='negative')
        ui.navigate.to('/dashboard')
        return
    collection = resp.json()
    works = []
    resp = await get(f'collections/{collection_id}/works')
    if resp.status_code == 200:
            works = resp.json()

    # ---------- Вспомогательные функции ----------
    def show_edit_dialog():
        collection_edit_dialog(
            initial_data={
                'name': collection['name'],
                'description': collection.get('description', ''),
            },
            on_save=lambda data: update_collection(collection_id, data)
        )

    def show_edit_work_dialog(work_item):
        display_settings_dialog(
            title='Редактирование настроек в коллекции',
            initial_settings=work_item.get('display_settings', {}),
            initial_status=work_item.get('status', 'pending'),
            on_save=lambda settings, status: update_work_in_container(
                collection_id, 'collections', work_item['work_id'], settings, status
            )
        )

    async def remove_work(work_id):
        async def do_delete():
            await remove_work_from_container(collection_id, 'collections', work_id)
        confirm_dialog(
            title='Удалить работу из коллекции?',
            message='Вы уверены, что хотите удалить эту работу?',
            on_confirm=do_delete
        )

    async def show_add_work_dialog():
        await select_work_dialog(collection_id, on_work_selected)

    def on_work_selected(work_id):
        display_settings_dialog(
            title='Настройки добавления в коллекцию',
            initial_status='pending',
            on_save=lambda settings, status: add_work_to_container(
                collection_id, 'collections', work_id, settings, status
            )
        )

    # ---------- Отображение ----------
    ui.label(f'Коллекция: {collection["name"]}').classes('text-h4')
    with ui.row():
        ui.button('Назад', on_click=lambda: ui.navigate.to('/dashboard'))
        ui.button('Редактировать', on_click=show_edit_dialog)
        ui.button('Удалить', on_click=lambda: confirm_dialog(
            title='Удалить коллекцию?',
            message='Это действие необратимо.',
            on_confirm=lambda: delete_collection(collection_id)
        ))

    with ui.card():
        ui.label(f"Описание: {collection.get('description', '')}")
        if collection.get('event_id'):
            ui.label(f"Привязана к событию: {collection.get('event_id')}")

    ui.label('Работы в коллекции').classes('text-h5')
    if works:
        for ew in works:
            event_work_item(ew, on_edit=show_edit_work_dialog, on_remove=remove_work)
    else:
        ui.label('Нет работ.')

    ui.button('Добавить работу', on_click=show_add_work_dialog)