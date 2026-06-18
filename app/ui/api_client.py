# app/ui/api_client.py
import httpx
from nicegui import app

API_BASE_URL = 'http://localhost:8000/api/v1'

async def request(method: str, endpoint: str, **kwargs):
    """Универсальная функция для запросов к API"""
    token = app.storage.user.get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))
    
    async with httpx.AsyncClient() as client:
        url = f'{API_BASE_URL}/{endpoint.lstrip("/")}'
        response = await client.request(method, url, headers=headers, **kwargs)
        return response

# Удобные обёртки
async def get(endpoint: str, **kwargs):
    return await request('GET', endpoint, **kwargs)

async def post(endpoint: str, **kwargs):
    return await request('POST', endpoint, **kwargs)

async def put(endpoint: str, **kwargs):
    return await request('PUT', endpoint, **kwargs)

async def delete(endpoint: str, **kwargs):
    return await request('DELETE', endpoint, **kwargs)