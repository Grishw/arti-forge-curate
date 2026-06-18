# app/ui/pages/works.py
from nicegui import app, ui

from app.ui.components import work_card
from ..api_client import get, delete
from ..dialogs import confirm_dialog

def register():
    @ui.page('/works')
    async def works_page():
        if not app.storage.user.get('token'):
            ui.navigate.to('/login')
            return

        ui.label('Каталог работ').classes('text-h4')
        # Фильтр по автору (заглушка)
        resp = await get('works/')
        if resp.status_code == 200:
            works = resp.json()
            if works:
                for w in works:
                    work_card(w, on_click=lambda w: ui.navigate.to(f'/works/{w["id"]}'))
            else:
                ui.label('Нет работ.')
        else:
            ui.notify('Ошибка загрузки', type='negative')

        ui.button('Назад', on_click=lambda: ui.navigate.to('/dashboard'))

    @ui.page('/works/{work_id}')
    async def work_detail(work_id: str):
        if not app.storage.user.get('token'):
            ui.navigate.to('/login')
            return

        resp = await get(f'works/{work_id}')
        if resp.status_code != 200:
            ui.notify('Работа не найдена', type='negative')
            ui.navigate.to('/works')
            return
        work = resp.json()

        work_detail(work)
        with ui.row():
            ui.button('Назад', on_click=lambda: ui.navigate.to('/works'))
            ui.button('Удалить', on_click=lambda: delete_work())

        async def delete_work():
            async def do_delete():
                resp = await delete(f'works/{work_id}')
                if resp.status_code == 200:
                    ui.notify('Работа удалена', type='positive')
                    ui.navigate.to('/works')
                else:
                    ui.notify(f'Ошибка: {resp.text}', type='negative')
            confirm_dialog(
                title='Удалить работу?',
                message='Это действие необратимо. Убедитесь, что работа не используется в событиях или коллекциях.',
                on_confirm=do_delete
            )