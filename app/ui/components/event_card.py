from nicegui import ui

def event_card(event, on_click=None):
    """Карточка события для списка"""
    with ui.card().tight() as card:
        ui.label(event['name']).classes('text-h6')
        ui.label(f"Статус: {event.get('status', 'не указан')}")
        ui.label(f"Даты: {event.get('start_date', '')} – {event.get('end_date', '')}")
        if on_click:
            card.on('click', lambda: on_click(event))
    return card