# app/ui/dialogs/collection_edit.py
from nicegui import ui

def collection_edit_dialog(initial_data: dict, on_save, on_cancel=None):
    """
    Открывает диалог редактирования коллекции.
    
    Args:
        initial_data: словарь с полями name, description
        on_save: асинхронная функция, принимающая обновлённые данные и возвращающая True/False
        on_cancel: функция без аргументов
    """
    with ui.dialog() as dialog, ui.card():
        ui.label('Редактировать коллекцию').classes('text-h6')
        edit_name = ui.input('Название', value=initial_data.get('name', '')).props('outlined')
        edit_desc = ui.textarea('Описание', value=initial_data.get('description', '')).props('outlined')
        error = ui.label().classes('text-negative')

        async def save():
            data = {
                'name': edit_name.value,
                'description': edit_desc.value,
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