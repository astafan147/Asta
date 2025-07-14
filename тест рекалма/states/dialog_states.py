from aiogram.dispatcher.filters.state import State, StatesGroup

class DialogStates(StatesGroup):
    """Состояния для диалога между менеджером и пользователем"""
    waiting_for_message = State()  # Ожидание сообщения от участника диалога 