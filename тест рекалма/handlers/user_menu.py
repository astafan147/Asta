from aiogram import types, Dispatcher
from keyboards.user import get_groups_keyboard, get_group_actions_keyboard, get_main_menu_keyboard, GROUPS, get_manager_menu_keyboard, get_admin_menu_keyboard
from config import MANAGER_IDS, ADMIN_IDS

# Обработчик команды /start
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id in MANAGER_IDS:
        await message.answer("Добро пожаловать, менеджер!", reply_markup=get_manager_menu_keyboard())
        return
    if user_id in ADMIN_IDS:
        await message.answer("Добро пожаловать, админ!", reply_markup=get_admin_menu_keyboard())
        return
    await message.answer(
        "Привет! Я бот для работы с группами. Выберите группу из списка:",
        reply_markup=get_groups_keyboard()
    )

# Обработчик выбора группы
async def group_callback(call: types.CallbackQuery):
    group_idx = int(call.data.split('_')[1])
    group_name = GROUPS[group_idx][0]
    
    await call.message.edit_text(
        f"Вы выбрали группу: {group_name}\nЧто хотите сделать?",
        reply_markup=get_group_actions_keyboard(group_idx)
    )

# Обработчик действий в группе
async def group_action_callback(call: types.CallbackQuery):
    parts = call.data.split('_')
    action = parts[0]
    if action == "back":
        await call.message.edit_text(
            "Выберите группу из списка:",
            reply_markup=get_groups_keyboard()
        )
        return
    if len(parts) < 3 or not parts[2].isdigit():
        await call.answer("Некорректные данные!")
        return
    group_idx = int(parts[2])
    group_name = GROUPS[group_idx][0]
    
    if action == "write":
        # Отправляем заявку менеджерам
        from handlers.support_menu import send_application_to_managers
        await send_application_to_managers(call.bot, call.from_user, group_idx)
        await call.answer("Заявка отправлена менеджеру!")
        
        # Показываем сообщение об успешной отправке с кнопками для возврата
        await call.message.edit_text(
            f"✅ Заявка в группу '{group_name}' отправлена менеджеру!\n\n"
            "Ожидайте ответа от менеджера. Вы можете вернуться в главное меню.",
            reply_markup=get_main_menu_keyboard()
        )
    elif action == "back":
        await call.message.edit_text(
            "Выберите группу из списка:",
            reply_markup=get_groups_keyboard()
        )

# Обработчик главного меню
async def main_menu_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id in MANAGER_IDS:
        await call.message.edit_text("Меню менеджера:", reply_markup=get_manager_menu_keyboard())
        return
    if user_id in ADMIN_IDS:
        await call.message.edit_text("Меню админа:", reply_markup=get_admin_menu_keyboard())
        return
    await call.message.edit_text(
        "Привет! Я бот для работы с группами. Выберите группу из списка:",
        reply_markup=get_groups_keyboard()
    )

# Обработчик выбора группы из главного меню
async def select_group_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id in MANAGER_IDS:
        await call.message.edit_text("Меню менеджера:", reply_markup=get_manager_menu_keyboard())
        return
    if user_id in ADMIN_IDS:
        await call.message.edit_text("Меню админа:", reply_markup=get_admin_menu_keyboard())
        return
    await call.message.edit_text(
        "Выберите группу из списка:",
        reply_markup=get_groups_keyboard()
    )

# Регистрация хендлера
def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_callback_query_handler(group_callback, lambda c: c.data.startswith('group_'))
    dp.register_callback_query_handler(group_action_callback, lambda c: c.data.startswith(('write_manager_', 'back_')))
    dp.register_callback_query_handler(main_menu_callback, lambda c: c.data == "main_menu")
    dp.register_callback_query_handler(select_group_callback, lambda c: c.data == "select_group") 