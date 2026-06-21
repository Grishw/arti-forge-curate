# app/ui/dialogs/event_work.py
from nicegui import app, ui
import httpx
from app.ui.api_client import post, put, get, API_BASE_URL
# Определяем базовый URL для статики (без /api/v1)
STATIC_BASE_URL = API_BASE_URL.replace('/api/v1', '')

# --- Диалог выбора работы из каталога ---
async def select_work_dialog(event_id: str, on_work_selected):
    """
    Открывает диалог со списком всех работ.
    При выборе работы вызывает on_work_selected(work_id) и закрывается.
    """
    with ui.dialog() as dialog, ui.card():
        ui.label('Выберите работу').classes('text-h6')
        container = ui.column()
        error_label = ui.label().classes('text-negative')
        
        async def load_works():
            container.clear()
            try:
                resp = await get('works/')
                if resp.status_code == 200:
                    works = resp.json()
                    if not works:
                        with container:
                            ui.label('Нет доступных работ')
                    else:
                        for w in works:
                            with container:
                                with ui.card().tight():
                                    if w.get('preview_path'):
                                        ui.image(f'{STATIC_BASE_URL}/{w["preview_path"]}').style('max-height: 100px')
                                    ui.label(w.get('name', 'Без названия')).classes('text-h6')
                                    ui.label(w.get('description', ''))
                                    ui.label(f"Автор: {w.get('author', 'неизвестен')}")
                                    ui.button('Выбрать', on_click=lambda wid=w['id']: select_work(wid))
                else:
                    error_label.text = 'Не удалось загрузить работы'
            except Exception as e:
                error_label.text = f'Ошибка: {e}'
        
        def select_work(work_id):
            dialog.close()
            if on_work_selected:
                on_work_selected(work_id)
        
        await load_works()
        ui.button('Отмена', on_click=dialog.close)
    dialog.open()

# --- Диалог настроек отображения (для добавления и редактирования) ---
def display_settings_dialog(
    title: str = 'Настройки отображения',
    initial_settings: dict = None,
    initial_status: str = 'pending',
    on_save=None,
    on_cancel=None
):
    """
    Открывает диалог с ползунками для настройки display_settings.
    
    Args:
        title: Заголовок
        initial_settings: словарь с ключами 'scale', 'position', 'rotation' (как в API)
        initial_status: начальный статус
        on_save: асинхронная функция, принимающая (settings, status) и возвращающая None/True
        on_cancel: функция без аргументов
    """
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes('text-h6')
        
        # Создаём реактивные переменные для значений
        scale_x = ui.slider(min=0.1, max=3.0, value=1.0, step=0.1)
        scale_y = ui.slider(min=0.1, max=3.0, value=1.0, step=0.1)
        scale_z = ui.slider(min=0.1, max=3.0, value=1.0, step=0.1)
        pos_x = ui.slider(min=-5, max=5, value=0, step=0.1)
        pos_y = ui.slider(min=-5, max=5, value=0, step=0.1)
        pos_z = ui.slider(min=-5, max=5, value=0, step=0.1)
        rot_x = ui.slider(min=-180, max=180, value=0, step=1)
        rot_y = ui.slider(min=-180, max=180, value=0, step=1)
        rot_z = ui.slider(min=-180, max=180, value=0, step=1)
        rot_w = ui.slider(min=-1, max=1, value=1, step=0.1)
        status_select = ui.select(['pending', 'approved', 'rejected'], value=initial_status)
        error_label = ui.label().classes('text-negative')
        
        # Устанавливаем начальные значения, если переданы
        if initial_settings:
            scale = initial_settings.get('scale', {})
            pos = initial_settings.get('position', {})
            rot = initial_settings.get('rotation', {})
            scale_x.value = scale.get('x', 1.0)
            scale_y.value = scale.get('y', 1.0)
            scale_z.value = scale.get('z', 1.0)
            pos_x.value = pos.get('x', 0)
            pos_y.value = pos.get('y', 0)
            pos_z.value = pos.get('z', 0)
            rot_x.value = rot.get('x', 0)
            rot_y.value = rot.get('y', 0)
            rot_z.value = rot.get('z', 0)
            rot_w.value = rot.get('w', 1)
        
        async def save():
            settings = {
                'scale': {'x': scale_x.value, 'y': scale_y.value, 'z': scale_z.value},
                'position': {'x': pos_x.value, 'y': pos_y.value, 'z': pos_z.value},
                'rotation': {'x': rot_x.value, 'y': rot_y.value, 'z': rot_z.value, 'w': rot_w.value}
            }
            status = status_select.value
            if on_save:
                try:
                    await on_save(settings, status)
                    dialog.close()
                except Exception as e:
                    error_label.text = f'Ошибка: {e}'
            else:
                dialog.close()
        
        ui.button('Сохранить', on_click=save).props('outline')
        ui.button('Отмена', on_click=lambda: (dialog.close(), on_cancel and on_cancel()))
    
    dialog.open()