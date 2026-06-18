# app/ui/pages/dashboard.py
from nicegui import app, ui
from ..theme import page

from app.ui.components import collection_card, event_card
from ..api_client import get

@ui.page('/dashboard')
async def dashboard_page():
    token = app.storage.user.get('token')
    if not token:
        ui.navigate.to('/login')
        return

    ui.label('Панель управления').classes('text-h4')
    with ui.row():
        ui.button('Создать событие', on_click=lambda: ui.navigate.to('/events/new'))
        ui.button('Создать коллекцию', on_click=lambda: ui.navigate.to('/collections/new'))

    # События
    ui.label('Мои события').classes('text-h5')
    resp = await get('events/')
    if resp.status_code == 200:
        events = resp.json()
        if events:
            for ev in events:
                event_card(ev, on_click=lambda e: ui.navigate.to(f'/events/{e["id"]}'))
        else:
            ui.label('Нет событий.')
    else:
        ui.notify('Ошибка загрузки событий', type='negative')

    # Коллекции
    ui.label('Мои коллекции').classes('text-h5')
    resp = await get('collections/')
    if resp.status_code == 200:
        collections = resp.json()
        if collections:
            for col in collections:
                collection_card(col, on_click=lambda c: ui.navigate.to(f'/collections/{c["id"]}'))
        else:
            ui.label('Нет коллекций.')
    else:
        ui.notify('Ошибка загрузки коллекций', type='negative')

    ui.button('Выйти', on_click=lambda: (app.storage.user.pop('token', None), ui.navigate.to('/login')))