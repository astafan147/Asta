import logging
from typing import Dict, Tuple, Optional
from aiogram import types
from aiogram.dispatcher import FSMContext

logger = logging.getLogger(__name__)

class DialogManager:
    """Менеджер диалогов между менеджерами и пользователями"""
    
    def __init__(self):
        # Словарь активных диалогов: {dialog_id: (user_id, manager_id, group_name)}
        self.active_dialogs: Dict[str, Tuple[int, int, str]] = {}
        # Словарь сообщений диалогов: {dialog_id: [message_ids]}
        self.dialog_messages: Dict[str, list] = {}
    
    def create_dialog(self, user_id: int, manager_id: int, group_name: str, application_number: str) -> str:
        """
        Создает новый диалог
        
        Args:
            user_id: ID пользователя
            manager_id: ID менеджера
            group_name: Название группы
            application_number: Номер заявки
            
        Returns:
            dialog_id: Уникальный ID диалога
        """
        dialog_id = f"dialog_{user_id}_{manager_id}_{application_number}"
        self.active_dialogs[dialog_id] = (user_id, manager_id, group_name)
        self.dialog_messages[dialog_id] = []
        logger.info(f"Создан диалог {dialog_id} между пользователем {user_id} и менеджером {manager_id}")
        return dialog_id
    
    def get_dialog_participants(self, dialog_id: str) -> Optional[Tuple[int, int, str]]:
        """Получает участников диалога"""
        return self.active_dialogs.get(dialog_id)
    
    def is_user_in_dialog(self, user_id: int) -> Optional[str]:
        """Проверяет, участвует ли пользователь в диалоге"""
        for dialog_id, (u_id, m_id, _) in self.active_dialogs.items():
            if u_id == user_id or m_id == user_id:
                return dialog_id
        return None
    
    def add_message_to_dialog(self, dialog_id: str, message_id: int):
        """Добавляет сообщение в историю диалога"""
        if dialog_id in self.dialog_messages:
            self.dialog_messages[dialog_id].append(message_id)
    
    def end_dialog(self, dialog_id: str):
        """Завершает диалог"""
        if dialog_id in self.active_dialogs:
            del self.active_dialogs[dialog_id]
        if dialog_id in self.dialog_messages:
            del self.dialog_messages[dialog_id]
        logger.info(f"Диалог {dialog_id} завершен")
    
    def get_dialog_keyboard(self, is_manager: bool = False) -> types.InlineKeyboardMarkup:
        """Создает клавиатуру для диалога"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        if is_manager:
            keyboard.add(
                types.InlineKeyboardButton("📋 Информация о заявке", callback_data="dialog_info"),
                types.InlineKeyboardButton("✅ Заявка выполнена", callback_data="dialog_done"),
                types.InlineKeyboardButton("🔚 Завершить диалог", callback_data="end_dialog")
            )
        else:
            keyboard.add(
                types.InlineKeyboardButton("🔚 Завершить диалог", callback_data="end_dialog")
            )
        return keyboard

# Глобальный экземпляр менеджера диалогов
dialog_manager = DialogManager() 