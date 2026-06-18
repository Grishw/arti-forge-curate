import asyncio
from nicegui import app, ui

def init_theme():
    ui.colors(
        primary='#5898d4',
        secondary='#26a69a',
        accent='#9c27b0',
        positive='#21ba45',
        negative='#c10015'
    )
    ui.add_head_html('''
    <style>
        .nicegui-content { padding: 1rem; }
        .main-menu a {
            text-decoration: none;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: background 0.2s;
        }
        .main-menu a:hover { background: rgba(255,255,255,0.2); }
        .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.2s;
        }
    </style>
    ''')

def frame(title: str = 'ARTi Curate'):
    @ui.contextmanager
    def layout():
        with ui.header(elevated=True).classes('bg-primary text-white'):
            with ui.row().classes('items-center w-full'):
                ui.label(title).classes('text-h5 font-bold')
                ui.space()
                with ui.row().classes('main-menu'):
                    ui.link('Дашборд', '/dashboard')
                    ui.link('Каталог работ', '/works')
                    ui.link('Выйти', '/logout').on('click', logout)
        with ui.column().classes('w-full p-4'):
            yield
        with ui.footer(fixed=False).classes('bg-grey-3'):
            with ui.row().classes('w-full justify-between'):
                ui.label('ARTi Curate v1.0').classes('text-caption')
                ui.label('© 2026 ARTi Forge').classes('text-caption')
    return layout

def logout():
    app.storage.user.pop('token', None)
    ui.navigate.to('/login')

def page(path: str, title: str = 'ARTi Curate'):
    """
    Декоратор, который регистрирует страницу по пути path и оборачивает её в общий layout.
    Поддерживает как синхронные, так и асинхронные функции с любыми параметрами пути.

    Использование:
        @page('/login', 'Вход в систему')
        def login_page():
            ...
    """
    def decorator(func):
        @ui.page(path)
        async def wrapper():
            with frame(title):
                result = func()
                if asyncio.iscoroutine(result):
                    return await result
                return result
        return wrapper
    return decorator