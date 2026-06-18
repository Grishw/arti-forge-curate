# app/ui/dialogs/confirm.py
from nicegui import ui

def confirm_dialog(title: str, message: str, on_confirm, on_cancel=None):
    """
    Создаёт и открывает диалог подтверждения.
    :param title: Заголовок диалога
    :param message: Текст сообщения
    :param on_confirm: Callback при подтверждении (может быть async)
    :param on_cancel: Callback при отмене (опционально)
    """
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes('text-h6')
        ui.label(message)
        with ui.row():
            async def do_confirm():
                dialog.close()
                if on_confirm:
                    result = on_confirm()
                    if hasattr(result, '__await__'):
                        await result
            async def do_cancel():
                dialog.close()
                if on_cancel:
                    result = on_cancel()
                    if hasattr(result, '__await__'):
                        await result
            ui.button('Да', on_click=do_confirm).props('outline')
            ui.button('Нет', on_click=do_cancel).props('outline')
    dialog.open()