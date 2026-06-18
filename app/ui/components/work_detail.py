# app/ui/components/work_detail.py
from nicegui import ui

def work_detail(work):
    """Детальная карточка работы"""
    ui.label(f"Работа: {work.get('name', 'Без названия')}").classes('text-h4')
    with ui.card():
        if work.get('preview_path'):
            ui.image(f'http://localhost:8000/{work["preview_path"]}').style('max-height: 400px')
        else:
            ui.label('(нет превью)').classes('text-grey')
        ui.label(f"Описание: {work.get('description', '')}")
        ui.label(f"Автор: {work.get('author', 'неизвестен')}")
        ui.label(f"Внешний ID: {work.get('external_id', '')}")
        if work.get('metadata'):
            ui.label('Метаданные:')
            for key, value in work['metadata'].items():
                ui.label(f"{key}: {value}")