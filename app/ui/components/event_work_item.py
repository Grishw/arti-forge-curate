from nicegui import ui

def event_work_item(work_item, event_id=None, collection_id=None, on_edit=None, on_remove=None):
    """
    Отображает работу в событии или коллекции с кнопками управления.
    
    work_item: объект EventWork или CollectionWork (содержит work_id, display_settings, status, и вложенный work)
    event_id или collection_id: для идентификации контейнера (не обязателен, если on_edit/on_remove уже привязаны)
    on_edit: callback при нажатии "Настроить" (получает work_item)
    on_remove: callback при нажатии "Удалить" (получает work_id)
    """
    work = work_item.get('work', {})
    work_name = work.get('name') or work_item.get('work_name') or 'Без названия'
    
    with ui.card().tight():
        with ui.row().classes('items-center'):
            if work.get('preview_path'):
                ui.image(f'http://localhost:8000/{work["preview_path"]}').style('max-height: 80px; max-width: 80px')
            ui.label(work_name).classes('text-h6')
        ui.label(f"Статус: {work_item.get('status', 'pending')}")
        with ui.row():
            if on_edit:
                ui.button('Настроить', on_click=lambda: on_edit(work_item))
            if on_remove:
                ui.button('Удалить', on_click=lambda: on_remove(work_item['work_id']))