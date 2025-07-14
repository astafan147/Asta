#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к NocoDB API v2
"""

import asyncio
import aiohttp
import logging
from config import NOCODB_TOKEN, NOCODB_TABLE

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_nocodb_connection():
    """Тестирует подключение к NocoDB API v2"""
    
    logger.info("=== Тест подключения к NocoDB API v2 ===")
    logger.info(f"Токен: {NOCODB_TOKEN[:10]}...")
    logger.info(f"Таблица: {NOCODB_TABLE}")
    
    # Используем только правильный облачный домен
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records'
    
    headers = {
        'xc-token': NOCODB_TOKEN,
        'Content-Type': 'application/json'
    }
    
    logger.info(f"\n--- Тест URL: {base_url} ---")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Тест GET запроса
            logger.info("Тестируем GET запрос...")
            async with session.get(base_url, headers=headers) as resp:
                logger.info(f"Статус: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    total_rows = data.get('pageInfo', {}).get('totalRows', 0)
                    logger.info(f"✅ УСПЕХ! Найдено записей: {total_rows}")
                    logger.info(f"✅ Рабочий URL: {base_url}")
                    return True, base_url
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ ОШИБКА {resp.status}: {error_text[:200]}")
                    
                    # Диагностика ошибок
                    if resp.status == 404:
                        logger.error("🔍 Диагностика 404:")
                        logger.error("1. Проверьте ID таблицы")
                        logger.error("2. Проверьте токен API")
                        logger.error("3. Убедитесь, что таблица существует")
                    elif resp.status == 401:
                        logger.error("🔍 Диагностика 401:")
                        logger.error("1. Неправильный токен API")
                        logger.error("2. Токен неактивен")
                        logger.error("3. Получите новый токен")
                    elif resp.status == 403:
                        logger.error("🔍 Диагностика 403:")
                        logger.error("1. Нет прав доступа к таблице")
                        logger.error("2. Токен не имеет нужных прав")
                    
    except Exception as e:
        logger.error(f"❌ Исключение: {e}")
    
    logger.error("❌ URL не работает")
    return False, None

async def test_create_record(working_url=None):
    """Тестирует создание записи в NocoDB"""
    
    if not working_url:
        logger.info("Пропускаем тест создания записи - нет рабочего URL")
        return False
    
    logger.info(f"\n=== Тест создания записи ===")
    logger.info(f"Используем URL: {working_url}")
    
    headers = {
        'xc-token': NOCODB_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Тестовые данные с вашими значениями
    test_data = {
        "Номер": "1",
        "Группа": "Сахком", 
        "Менеджер": "@vorobey",
        "Пользователь": "@dimaz"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info("Тестируем POST запрос...")
            async with session.post(working_url, json=test_data, headers=headers) as resp:
                logger.info(f"Статус: {resp.status}")
                
                if resp.status == 200:
                    response_data = await resp.json()
                    logger.info(f"✅ УСПЕХ! Запись создана: {response_data}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ ОШИБКА {resp.status}: {error_text[:300]}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Исключение: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    
    logger.info("🚀 Запуск тестов NocoDB...")
    
    # Тест подключения
    connection_ok, working_url = await test_nocodb_connection()
    
    if connection_ok:
        # Тест создания записи
        await test_create_record(working_url)
    
    logger.info("\n📋 Рекомендации:")
    if not connection_ok:
        logger.info("1. Проверьте токен API в config.py")
        logger.info("2. Проверьте ID таблицы")
        logger.info("3. Убедитесь, что таблица существует")
        logger.info("4. Получите новый токен в NocoDB")
        logger.info("5. Возможно, нужно использовать API v1 вместо v2")
    else:
        logger.info("✅ NocoDB настроен правильно!")
        logger.info("Бот готов к работе с сохранением заявок")

if __name__ == '__main__':
    asyncio.run(main()) 