# app/ui/pages/events.py
from nicegui import app, ui
from ..theme import page

from ..api_client import get, post
from ..dialogs import (
    confirm_dialog,
    select_work_dialog,
    display_settings_dialog,
    event_edit_dialog      # <-- добавляем
)
from ..components import event_work_item
from ..helpers import (
    add_work_to_container,
    update_work_in_container,
    remove_work_from_container,
    publish_event,
    delete_event,
    update_event,
    unpublish_event
)

# ---------- Создание события ----------
@ui.page('/events/new')
async def create_event_page():
    if not app.storage.user.get('token'):
        ui.navigate.to('/login')
        return
    ui.label('Создание события').classes('text-h4')
    with ui.card():
        name = ui.input('Название', placeholder='Введите название события').props('outlined')
        description = ui.textarea('Описание', placeholder='Описание события').props('outlined')
        start_date = ui.input('Дата начала', placeholder='YYYY-MM-DD HH:MM:SS').props('outlined')
        end_date = ui.input('Дата окончания', placeholder='YYYY-MM-DD HH:MM:SS').props('outlined')
        location = ui.input('Место проведения', placeholder='Локация').props('outlined')
        error = ui.label().classes('text-negative')

        async def do_create():
            data = {
                'name': name.value,
                'description': description.value,
                'start_date': start_date.value,
                'end_date': end_date.value,
                'location': location.value,
                'status': 'draft'
            }
            resp = await post('events/', json=data)
            if resp.status_code == 200:
                event = resp.json()
                ui.notify('Событие создано', type='positive')
                ui.navigate.to(f'/events/{event["id"]}')
            else:
                error.text = f'Ошибка: {resp.status_code} - {resp.text}'

        ui.button('Создать', on_click=do_create).props('outline')
        ui.button('Отмена', on_click=lambda: ui.navigate.to('/dashboard'))

@ui.page('/events/{event_id}')
async def event_page(event_id: str):
    if not app.storage.user.get('token'):
        ui.navigate.to('/login')
        return

    resp = await get(f'events/{event_id}')
    if resp.status_code != 200:
        ui.notify('Событие не найдено', type='negative')
        ui.navigate.to('/dashboard')
        return
    event = resp.json()
    works = []
    resp = await get(f'events/{event_id}/works')
    if resp.status_code == 200:
            works = resp.json()

    # ---------- Вспомогательные функции ----------
    def show_edit_dialog():
        # Используем вынесенный диалог
        event_edit_dialog(
            initial_data={
                'name': event['name'],
                'description': event.get('description', ''),
                'start_date': event.get('start_date', ''),
                'end_date': event.get('end_date', ''),
                'location': event.get('location', ''),
            },
            on_save=lambda data: update_event(event_id, data)
        )

    def show_edit_work_dialog(work_item):
        display_settings_dialog(
            title='Редактирование настроек',
            initial_settings=work_item.get('display_settings', {}),
            initial_status=work_item.get('status', 'pending'),
            on_save=lambda settings, status: update_work_in_container(
                event_id, 'events', work_item['work_id'], settings, status
            )
        )

    async def remove_work(work_id):
        async def do_delete():
            await remove_work_from_container(event_id, 'events', work_id)
        confirm_dialog(
            title='Удалить работу из события?',
            message='Вы уверены, что хотите удалить эту работу?',
            on_confirm=do_delete
        )

    async def show_add_work_dialog():
        await select_work_dialog(event_id, on_work_selected)

    def on_work_selected(work_id):
        display_settings_dialog(
            title='Настройки добавления',
            initial_status='pending',
            on_save=lambda settings, status: add_work_to_container(
                event_id, 'events', work_id, settings, status
            )
        )

    # ---------- Отображение ----------
    ui.label(f'Событие: {event["name"]}').classes('text-h4')
    with ui.row():
        ui.button('Назад', on_click=lambda: ui.navigate.to('/dashboard'))
        if event.get('status') != 'published':
            ui.button('Опубликовать', on_click=lambda: publish_event(event_id))
        elif  event.get('status') == 'published':
            ui.button('В архив', on_click=lambda: unpublish_event(event_id))
        ui.button('Редактировать', on_click=show_edit_dialog)
        ui.button('Удалить', on_click=lambda: confirm_dialog(
            title='Удалить событие?',
            message='Это действие необратимо.',
            on_confirm=lambda: delete_event(event_id)
        ))

    with ui.card():
        ui.label(f"Описание: {event.get('description', '')}")
        ui.label(f"Даты: {event.get('start_date', '')} – {event.get('end_date', '')}")
        ui.label(f"Место: {event.get('location', '')}")
        ui.label(f"Статус: {event.get('status', '')}")

    ui.label('Работы в событии').classes('text-h5')
    if works:
        for ew in works:
            event_work_item(ew, on_edit=show_edit_work_dialog, on_remove=remove_work)
    else:
        ui.label('Нет добавленных работ.')

    ui.button('Добавить работу', on_click=show_add_work_dialog)