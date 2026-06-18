# app/ui/pages/auth.py
from nicegui import app, ui
from ..theme import page
from ..api_client import post

@ui.page('/login')
def login_page():
    ui.label('Вход в систему').classes('text-h4')
    email = ui.input('Email').props('outlined')
    password = ui.input('Пароль', password=True).props('outlined')
    error = ui.label().classes('text-negative')

    async def do_login():
        resp = await post('auth/login', params={'email': email.value, 'password': password.value})
        if resp.status_code == 200:
            app.storage.user['token'] = resp.json()['access_token']
            ui.notify('Вход выполнен', type='positive')
            ui.navigate.to('/dashboard')
        else:
            error.text = 'Неверный email или пароль'

    ui.button('Войти', on_click=do_login).props('outline')
    ui.link('Нет аккаунта? Зарегистрируйтесь', '/register')

@ui.page('/register')
def register_page():
    ui.label('Регистрация').classes('text-h4')
    email = ui.input('Email').props('outlined')
    full_name = ui.input('Полное имя').props('outlined')
    password = ui.input('Пароль', password=True).props('outlined')
    role = ui.select(['curator', 'admin'], value='curator').props('outlined')
    error = ui.label().classes('text-negative')

    async def do_register():
        resp = await post('auth/register', json={
            'email': email.value,
            'full_name': full_name.value,
            'password': password.value,
            'role': role.value
        })
        if resp.status_code == 200:
            ui.notify('Регистрация успешна, войдите', type='positive')
            ui.navigate.to('/login')
        else:
            error.text = resp.json().get('detail', 'Ошибка регистрации')

    ui.button('Зарегистрироваться', on_click=do_register).props('outline')
    ui.link('Уже есть аккаунт? Войти', '/login')