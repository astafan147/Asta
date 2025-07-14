import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.user_menu import register_user_handlers
from handlers.support_menu import register_support_handlers, register_history_handlers
from handlers.dialog_handlers import register_dialog_handlers
from middlewares.error_handler import ErrorHandlerMiddleware
from utils.nocodb import test_nocodb_connection

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # Инициализируем бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    # Регистрируем middleware для обработки ошибок
    dp.middleware.setup(ErrorHandlerMiddleware())
    
    # Регистрируем хендлеры
    register_user_handlers(dp)
    register_support_handlers(dp)
    register_history_handlers(dp)
    register_dialog_handlers(dp)
    
    # Тестируем подключение к NocoDB
    logger.info("Тестирование подключения к NocoDB...")
    nocodb_ok = await test_nocodb_connection()
    if nocodb_ok:
        logger.info("NocoDB подключение успешно")
    else:
        logger.warning("NocoDB подключение не удалось - функции сохранения заявок будут недоступны")
    
    # Запускаем бота
    try:
        logger.info("Бот запущен")
        await dp.start_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main()) 