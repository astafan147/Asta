from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
import logging
import traceback

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        try:
            pass  # Не вызываем super()
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}\n{traceback.format_exc()}")
            try:
                await message.reply("Произошла ошибка. Попробуйте позже или обратитесь в поддержку.")
            except Exception:
                pass
            return True

    async def on_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        try:
            pass  # Не вызываем super()
        except Exception as e:
            logger.error(f"Ошибка при обработке callback: {e}\n{traceback.format_exc()}")
            try:
                await callback_query.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
            except Exception:
                pass
            return True 