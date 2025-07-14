import aiohttp
import os
import logging
from config import NOCODB_TOKEN, NOCODB_TABLE

# Настраиваем логирование
logger = logging.getLogger(__name__)

# Тестовая функция для проверки подключения к NocoDB
async def test_nocodb_connection():
    """
    Тестирует подключение к NocoDB API v2
    """
    logger.info(f'Тестирование NocoDB API v2 с токеном: {NOCODB_TOKEN[:10]}... и таблицей: {NOCODB_TABLE}')
    
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records'
    headers = {
        'xc-token': NOCODB_TOKEN,
        'Content-Type': 'application/json'
    }
    try:
        logger.info(f'Пробуем URL: {base_url}')
        logger.info(f'Заголовки: xc-token={NOCODB_TOKEN[:10]}...')
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, headers=headers) as resp:
                logger.info(f'NocoDB connection test - Status: {resp.status}')
                if resp.status == 200:
                    data = await resp.json()
                    total_rows = data.get('pageInfo', {}).get('totalRows', 0)
                    logger.info(f'NocoDB connection successful. Found {total_rows} records')
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f'NocoDB connection failed: {resp.status} {error_text[:200]}')
                    if resp.status == 404:
                        logger.error('Ошибка 404 - возможные причины:')
                        logger.error('1. Неправильный ID таблицы')
                        logger.error('2. Неправильный токен API')
                        logger.error('3. Таблица не существует или недоступна')
                    elif resp.status == 401:
                        logger.error('Ошибка 401 - неправильный токен API')
                    elif resp.status == 403:
                        logger.error('Ошибка 403 - нет прав доступа к таблице')
                    return False
    except Exception as e:
        logger.error(f'Ошибка при тестировании NocoDB: {e}')
        return False

# Сохраняем заявку в NocoDB
async def save_application(group_name: str, user_username: str, manager_username: str, application_number: str, data=None):
    """
    Сохраняет заявку в NocoDB используя API v2
    Args:
        group_name: Название группы (например, "РАБОТА САХКОМ")
        user_username: Username пользователя (например, "@user123")
        manager_username: Username менеджера (например, "@manager456")
        application_number: Номер заявки (например, "#123456")
        data: словарь для отправки (если None — формируется стандартно)
    """
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records'
    headers = {
        'xc-token': NOCODB_TOKEN,
        'Content-Type': 'application/json'
    }
    if data is None:
        data = {
            "Номер": application_number,
            "Менеджер": manager_username,
            "Пользователь": user_username,
            "Группа": group_name,
            "ck2mdpjv0b3hyml": "В работе"
        }
    logger.info(f'Попытка сохранения в NocoDB API v2: {data}')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(base_url, json=data, headers=headers) as resp:
                if resp.status == 200:
                    response_data = await resp.json()
                    logger.info(f'Заявка успешно сохранена в NocoDB: {response_data}')
                else:
                    error_text = await resp.text()
                    logger.error(f'NocoDB error: {resp.status} {error_text}')
    except Exception as e:
        logger.error(f'Ошибка при сохранении в NocoDB: {e}')

# Получить следующий номер заявки (автоинкремент)
async def get_next_application_number():
    """
    Получает следующий номер заявки из NocoDB (максимальный + 1)
    """
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records?page_size=1000'
    headers = {
        'xc-token': NOCODB_TOKEN,
        'Content-Type': 'application/json'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    records = data.get('list', [])
                    max_num = 0
                    for rec in records:
                        num = rec.get('Номер')
                        try:
                            num_int = int(str(num).replace('#',''))
                            if num_int > max_num:
                                max_num = num_int
                        except Exception:
                            continue
                    return str(max_num + 1)
                else:
                    return '1'
    except Exception:
        return '1' 