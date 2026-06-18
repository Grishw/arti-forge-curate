# app/ui/dialogs/event_edit.py
from nicegui import ui

def event_edit_dialog(initial_data: dict, on_save, on_cancel=None):
    """
    Открывает диалог редактирования события.
    
    Args:
        initial_data: словарь с полями name, description, start_date, end_date, location
        on_save: асинхронная функция, принимающая обновлённые данные и возвращающая True/False
        on_cancel: функция без аргументов
    """
    with ui.dialog() as dialog, ui.card():
        ui.label('Редактировать событие').classes('text-h6')
        edit_name = ui.input('Название', value=initial_data.get('name', '')).props('outlined')
        edit_desc = ui.textarea('Описание', value=initial_data.get('description', '')).props('outlined')
        edit_start = ui.input('Дата начала', value=initial_data.get('start_date', '')).props('outlined')
        edit_end = ui.input('Дата окончания', value=initial_data.get('end_date', '')).props('outlined')
        edit_location = ui.input('Место', value=initial_data.get('location', '')).props('outlined')
        error = ui.label().classes('text-negative')

        async def save():
            data = {
                'name': edit_name.value,
                'description': edit_desc.value,
                'start_date': edit_start.value,
                'end_date': edit_end.value,
                'location': edit_location.value,
            }
            if on_save:
                try:
                    success = await on_save(data)
                    if success:
                        dialog.close()
                except Exception as e:
                    error.text = f'Ошибка: {e}'
            else:
                dialog.close()

        ui.button('Сохранить', on_click=save).props('outline')
        ui.button('Отмена', on_click=lambda: (dialog.close(), on_cancel and on_cancel()))
    dialog.open()