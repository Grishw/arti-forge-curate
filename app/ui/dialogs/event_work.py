# app/ui/dialogs/event_work.py
from nicegui import app, ui
import httpx
from app.ui.api_client import post, put, get, API_BASE_URL
# Определяем базовый URL для статики (без /api/v1)
STATIC_BASE_URL = API_BASE_URL.replace('/api/v1', '')

async def add_work_dialog(parent_id: str, parent_type: str, headers: dict, on_success=None):
    """
    Открывает диалог для добавления работы в событие или коллекцию.
    :param parent_id: ID события или коллекции
    :param parent_type: 'event' или 'collection'
    :param headers: заголовки с токеном
    :param on_success: callback после успешного добавления
    """
    endpoint = f'events/{parent_id}/works' if parent_type == 'event' else f'collections/{parent_id}/works'
    
    with ui.dialog() as add_dialog, ui.card():
        ui.label('Выберите работу').classes('text-h6')
        work_container = ui.column()
        error = ui.label().classes('text-negative')
        selected_work_id = {'id': None}

        async def load_all_works():
            work_container.clear()
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get('http://localhost:8000/api/v1/works/', headers=headers)
                if resp.status_code == 200:
                    all_works = resp.json()
                    if not all_works:
                        with work_container:
                            ui.label('Нет доступных работ')
                    else:
                        for w in all_works:
                            with work_container:
                                with ui.card().tight():
                                    if w.get('preview_path'):
                                        ui.image(f'http://localhost:8000/{w["preview_path"]}').style('max-height: 100px')
                                    ui.label(w.get('name', 'Без названия')).classes('text-h6')
                                    ui.label(w.get('description', ''))
                                    ui.label(f"Автор: {w.get('author', 'неизвестен')}")
                                    ui.button('Выбрать', on_click=lambda w=w: open_settings_dialog(w['id']))
                else:
                    ui.notify('Не удалось загрузить работы', type='negative')
            except Exception as e:
                ui.notify(f'Ошибка: {e}', type='negative')

        # Диалог настроек (вложенный)
        settings_dialog = ui.dialog()
        with settings_dialog, ui.card():
            ui.label('Настройки отображения').classes('text-h6')
            # Ползунки
            with ui.row():
                ui.label('Масштаб:')
                scale_x = ui.slider(min=0.1, max=3.0, value=1.0, step=0.1)
                scale_y = ui.slider(min=0.1, max=3.0, value=1.0, step=0.1)
                scale_z = ui.slider(min=0.1, max=3.0, value=1.0, step=0.1)
            with ui.row():
                ui.label('Позиция:')
                pos_x = ui.slider(min=-5, max=5, value=0, step=0.1)
                pos_y = ui.slider(min=-5, max=5, value=0, step=0.1)
                pos_z = ui.slider(min=-5, max=5, value=0, step=0.1)
            with ui.row():
                ui.label('Вращение:')
                rot_x = ui.slider(min=-180, max=180, value=0, step=1)
                rot_y = ui.slider(min=-180, max=180, value=0, step=1)
                rot_z = ui.slider(min=-180, max=180, value=0, step=1)
                rot_w = ui.slider(min=-1, max=1, value=1, step=0.1)
            status = ui.select(['pending', 'approved', 'rejected'], value='pending')
            settings_error = ui.label().classes('text-negative')

            async def do_add():
                work_id = selected_work_id['id']
                if not work_id:
                    settings_error.text = 'Работа не выбрана'
                    return
                display_settings = {
                    'scale': {'x': scale_x.value, 'y': scale_y.value, 'z': scale_z.value},
                    'position': {'x': pos_x.value, 'y': pos_y.value, 'z': pos_z.value},
                    'rotation': {'x': rot_x.value, 'y': rot_y.value, 'z': rot_z.value, 'w': rot_w.value}
                }
                data = {
                    'work_id': work_id,
                    'display_settings': display_settings,
                    'status': status.value,
                    f'{parent_type}_id': parent_id  # передаём event_id или collection_id
                }
                try:
                    if parent_type == 'event':
                        resp = await post(f'events/{parent_id}/works', json=data, headers=headers)
                    else:
                        resp = await post(f'collections/{parent_id}/works', json=data, headers=headers)
                    if resp.status_code == 200:
                        ui.notify('Работа добавлена', type='positive')
                        settings_dialog.close()
                        add_dialog.close()
                        if on_success:
                            await on_success()
                    else:
                        settings_error.text = f'Ошибка: {resp.text}'
                except Exception as e:
                    settings_error.text = f'Ошибка: {e}'

            ui.button('Добавить', on_click=do_add).props('outline')
            ui.button('Отмена', on_click=settings_dialog.close)

        def open_settings_dialog(work_id):
            selected_work_id['id'] = work_id
            settings_error.text = ''
            # Сброс значений (опционально)
            scale_x.value = 1.0
            scale_y.value = 1.0
            scale_z.value = 1.0
            pos_x.value = 0
            pos_y.value = 0
            pos_z.value = 0
            rot_x.value = 0
            rot_y.value = 0
            rot_z.value = 0
            rot_w.value = 1
            status.value = 'pending'
            settings_dialog.open()

        await load_all_works()
        ui.button('Отмена', on_click=add_dialog.close)
    add_dialog.open()


async def edit_work_dialog(parent_id: str, parent_type: str, work_item: dict, headers: dict, on_success=None):
    """
    Открывает диалог редактирования настроек работы.
    :param parent_id: ID события или коллекции
    :param parent_type: 'event' или 'collection'
    :param work_item: объект работы (содержит work_id, display_settings, status)
    :param headers: заголовки с токеном
    :param on_success: callback после успешного обновления
    """
    work_id = work_item['work_id']
    display = work_item.get('display_settings', {})
    scale = display.get('scale', {})
    pos = display.get('position', {})
    rot = display.get('rotation', {})

    with ui.dialog() as dialog, ui.card():
        ui.label('Редактировать настройки работы').classes('text-h6')
        with ui.row():
            ui.label('Масштаб:')
            scale_x = ui.slider(min=0.1, max=3.0, value=scale.get('x', 1.0), step=0.1)
            scale_y = ui.slider(min=0.1, max=3.0, value=scale.get('y', 1.0), step=0.1)
            scale_z = ui.slider(min=0.1, max=3.0, value=scale.get('z', 1.0), step=0.1)
        with ui.row():
            ui.label('Позиция:')
            pos_x = ui.slider(min=-5, max=5, value=pos.get('x', 0), step=0.1)
            pos_y = ui.slider(min=-5, max=5, value=pos.get('y', 0), step=0.1)
            pos_z = ui.slider(min=-5, max=5, value=pos.get('z', 0), step=0.1)
        with ui.row():
            ui.label('Вращение:')
            rot_x = ui.slider(min=-180, max=180, value=rot.get('x', 0), step=1)
            rot_y = ui.slider(min=-180, max=180, value=rot.get('y', 0), step=1)
            rot_z = ui.slider(min=-180, max=180, value=rot.get('z', 0), step=1)
            rot_w = ui.slider(min=-1, max=1, value=rot.get('w', 1), step=0.1)
        status = ui.select(['pending', 'approved', 'rejected'], value=work_item.get('status', 'pending'))
        error = ui.label().classes('text-negative')

        async def do_update():
            display_settings = {
                'scale': {'x': scale_x.value, 'y': scale_y.value, 'z': scale_z.value},
                'position': {'x': pos_x.value, 'y': pos_y.value, 'z': pos_z.value},
                'rotation': {'x': rot_x.value, 'y': rot_y.value, 'z': rot_z.value, 'w': rot_w.value}
            }
            data = {
                'display_settings': display_settings,
                'status': status.value
            }
            try:
                if parent_type == 'event':
                    resp = await put(f'events/{parent_id}/works/{work_id}', json=data, headers=headers)
                else:
                    resp = await put(f'collections/{parent_id}/works/{work_id}', json=data, headers=headers)
                if resp.status_code == 200:
                    ui.notify('Настройки обновлены', type='positive')
                    dialog.close()
                    if on_success:
                        await on_success()
                else:
                    error.text = f'Ошибка: {resp.text}'
            except Exception as e:
                error.text = f'Ошибка: {e}'

        ui.button('Сохранить', on_click=do_update).props('outline')
        ui.button('Отмена', on_click=dialog.close)
    dialog.open()

    # app/ui/dialogs/event_work.py

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