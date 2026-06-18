from nicegui import ui

def work_card(work, show_preview=True, on_click=None):
    """Карточка работы для каталога"""
    with ui.card().tight() as card:
        if show_preview and work.get('preview_path'):
            ui.image(f'http://localhost:8000/{work["preview_path"]}').style('max-height: 150px')
        ui.label(work.get('name', 'Без названия')).classes('text-h6')
        ui.label(work.get('description', ''))
        ui.label(f"Автор: {work.get('author', 'неизвестен')}")
        if on_click:
            card.on('click', lambda: on_click(work))
    return card