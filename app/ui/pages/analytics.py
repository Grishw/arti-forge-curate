
from nicegui import app, ui

from app.ui.theme import page
from ..api_client import get

@ui.page('/analytics')
async def analytics_page():
    if not app.storage.user.get('token'):
        ui.navigate.to('/login')
        return

    ui.label('Аналитика').classes('text-h4')
    
    # Выбор события
    resp = await get('events/')
    events = resp.json() if resp.status_code == 200 else []
    event_select = ui.select(
        {ev['id']: ev['name'] for ev in events},
        label='Выберите событие',
        value=events[0]['id'] if events else None,
        on_change=lambda e: update_stats(e.value)
    )
    
    # Контейнер для статистики
    stats_container = ui.column()
    
    async def update_stats(event_id):
        stats_container.clear()
        if not event_id:
            with stats_container:
                ui.label('Выберите событие')
            return
        
        # Здесь будет запрос к реальному эндпоинту аналитики
        # Пока заглушка
        with stats_container:
            ui.label(f'Статистика для события {event_id}')
            ui.label('Количество работ: 5')
            ui.label('Количество просмотров: 42')
            ui.label('Количество взаимодействий: 12')
    
    if event_select.value:
        await update_stats(event_select.value)
    
    ui.button('Назад', on_click=lambda: ui.navigate.to('/dashboard'))