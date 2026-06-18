from nicegui import ui

def collection_card(collection, on_click=None):
    """Карточка коллекции для списка"""
    with ui.card().tight() as card:
        ui.label(collection['name']).classes('text-h6')
        if collection.get('event_id'):
            ui.label(f"Привязана к событию: {collection['event_id']}")
        if on_click:
            card.on('click', lambda: on_click(collection))
    return card