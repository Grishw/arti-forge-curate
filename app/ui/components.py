from nicegui import app, ui

def require_auth():
    token = app.storage.user.get('token')
    if not token:
        ui.navigate.to('/login')   # исправлено
        return False
    return True

def get_headers():
    token = app.storage.user.get('token')
    return {'Authorization': f'Bearer {token}'} if token else {}