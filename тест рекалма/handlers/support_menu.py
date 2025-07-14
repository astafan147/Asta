from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.callback_data import CallbackData
from keyboards.user import GROUPS, get_main_menu_keyboard, get_manager_history_keyboard, get_admin_history_keyboard, get_admin_manager_list_keyboard, get_admin_back_to_managers_keyboard
from utils.nocodb import save_application, get_next_application_number
from utils.dialog_manager import dialog_manager
from config import MANAGERS_CHAT_ID, ADMIN_ID, MANAGER_IDS, ADMIN_IDS
import logging
from utils.nocodb import NOCODB_TOKEN, NOCODB_TABLE
import aiohttp

# CallbackData для заявок
application_cb = CallbackData('app', 'user_id', 'group_idx')

# Временное хранилище для message_id заявок в группах
application_group_messages = {}

# Настраиваем логирование
logger = logging.getLogger(__name__)

# Отправка заявки в группу менеджеров
async def send_application_to_managers(bot, user, group_idx):
    group_name = GROUPS[group_idx][0]
    text = (
        'Новая заявка!\n'
        f'Пользователь: {user.full_name} (@{user.username or "без_username"})\n'
        f'Группа: {group_name}'
    )
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            'Принять заявку',
            callback_data=application_cb.new(user_id=user.id, group_idx=group_idx)
        )
    )
    try:
        msg = await bot.send_message(MANAGERS_CHAT_ID, text, reply_markup=keyboard)
        # Сохраняем message_id для последующего редактирования
        application_group_messages[(user.id, group_idx)] = msg.message_id
    except Exception as e:
        # Логируем ошибку, но не прерываем работу
        logger.error(f'Ошибка отправки заявки менеджерам: {e}')

# Обработка принятия заявки менеджером
async def manager_accept_callback(call: types.CallbackQuery, callback_data: dict):
    user_id = int(callback_data['user_id'])
    group_idx = int(callback_data['group_idx'])
    manager = call.from_user
    group_name = GROUPS[group_idx][0]

    # Получаем следующий номер заявки (автоинкремент)
    application_number = await get_next_application_number()

    # Получаем username пользователя
    try:
        user_info = await call.bot.get_chat(user_id)
        user_username = f"@{user_info.username}" if user_info.username else f"@user_{user_id}"
    except Exception as e:
        logger.error(f"Ошибка получения информации о пользователе: {e}")
        user_username = f"@user_{user_id}"

    # Получаем username менеджера
    manager_username = f"@{manager.username}" if manager.username else f"@manager_{manager.id}"

    # Создаем диалог между менеджером и пользователем
    dialog_id = dialog_manager.create_dialog(user_id, manager.id, group_name, application_number)

    # Уведомление админу в нужном формате
    text = (
        f'Номер заявки: {application_number}\n'
        f'Группа: {group_name}\n'
        f'Пользователь: {user_username}\n'
        f'Менеджер: {manager_username}'
    )
    try:
        await call.bot.send_message(ADMIN_ID, text)
    except Exception as e:
        logger.error(f'Ошибка отправки админу: {e}')

    # Уведомление пользователю о начале диалога
    try:
        await call.bot.send_message(
            user_id,
            f"✅ Менеджер принял вашу заявку {application_number} в группу '{group_name}'!\n\n"
            "💬 Можете написать сообщение менеджеру.\n"
            f"Группа: {group_name}\n"
            "🔚 Для завершения диалога нажмите кнопку ниже.",
            reply_markup=dialog_manager.get_dialog_keyboard(is_manager=False)
        )
    except Exception as e:
        logger.error(f'Ошибка отправки пользователю: {e}')

    # Уведомление менеджеру о начале диалога
    try:
        await call.bot.send_message(
            manager.id,
            f"✅ Вы приняли заявку {application_number} от пользователя {user_username}\n"
            f"Группа: {group_name}\n\n"
            "💬 Диалог с пользователем начат. Вы можете отправлять сообщения и файлы.\n"
            "📋 Для просмотра информации о заявке нажмите соответствующую кнопку.",
            reply_markup=dialog_manager.get_dialog_keyboard(is_manager=True)
        )
    except Exception as e:
        logger.error(f'Ошибка отправки менеджеру: {e}')

    # Пытаемся сохранить в NocoDB, но не прерываем работу если не получается
    try:
        data = {
            "Номер": application_number,
            "Менеджер": manager_username,
            "Пользователь": user_username,
            "Группа": group_name,
            "ck2mdpjv0b3hyml": "Принята",
            "Статус": "Принята"
        }
        await save_application(group_name, user_username, manager_username, application_number, data)
        logger.info(f"Заявка {application_number} успешно сохранена в NocoDB")
    except Exception as e:
        logger.warning(f'Не удалось сохранить в NocoDB: {e}. Бот продолжает работать.')

    # Обновляем сообщение в группе: добавляем менеджера, убираем кнопку
    try:
        msg_id = application_group_messages.get((user_id, group_idx))
        if msg_id:
            group_text = (
                'Новая заявка!\n'
                f'Пользователь: {user_info.full_name} ({user_username})\n'
                f'Группа: {group_name}\n'
                f'Менеджер: {manager_username} (принял заявку)'
            )
            await call.bot.edit_message_text(
                group_text,
                chat_id=MANAGERS_CHAT_ID,
                message_id=msg_id
            )
    except Exception as e:
        logger.error(f'Ошибка обновления сообщения в группе: {e}')

    await call.answer('Заявка принята! Диалог создан.')

# Получить заявки менеджера с пагинацией
async def get_manager_applications(manager_username, page=1, page_size=5):
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records?page_size=1000'
    headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                records = [r for r in data.get('list', []) if r.get('Менеджер') == manager_username]
                total = len(records)
                start = (page-1)*page_size
                end = start+page_size
                return records[start:end], total
            return [], 0

# Получить все заявки для админа с пагинацией
async def get_admin_applications(page=1, page_size=5):
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records?page_size=1000'
    headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                records = data.get('list', [])
                total = len(records)
                start = (page-1)*page_size
                end = start+page_size
                return records[start:end], total
            return [], 0

# Хендлер истории менеджера
async def manager_history_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    manager_username = f"@{call.from_user.username}" if call.from_user.username else f"@manager_{user_id}"
    page = 1
    if call.data.startswith('manager_history_page_') or call.data.startswith('manager_history_next_') or call.data.startswith('manager_history_prev_'):
        page = int(call.data.split('_')[-1])
    records, total = await get_manager_applications(manager_username, page)
    has_prev = page > 1
    has_next = total > page*5
    if not records:
        await call.message.edit_text("Заявок не найдено.", reply_markup=get_manager_history_keyboard(page, has_prev, has_next))
        return
    text = '📋 <b>Мои заявки</b>\n\n'
    for r in records:
        status = r.get('Статус') or r.get('ck2mdpjv0b3hyml', '—')
        text += f"Номер: {r.get('Номер')}\nГруппа: {r.get('Группа')}\nСтатус: {status}\n---\n"
    await call.message.edit_text(text, reply_markup=get_manager_history_keyboard(page, has_prev, has_next), parse_mode='HTML')

# Хендлер истории админа
async def admin_history_callback(call: types.CallbackQuery):
    page = 1
    if call.data.startswith('admin_history_page_') or call.data.startswith('admin_history_next_') or call.data.startswith('admin_history_prev_'):
        page = int(call.data.split('_')[-1])
    records, total = await get_admin_applications(page)
    has_prev = page > 1
    has_next = total > page*5
    if not records:
        await call.message.edit_text("Заявок не найдено.", reply_markup=get_admin_history_keyboard(page, has_prev, has_next))
        return
    text = '📋 <b>Все заявки</b>\n\n'
    for r in records:
        status = r.get('Статус') or r.get('ck2mdpjv0b3hyml', '—')
        text += f"Номер: {r.get('Номер')}\nМенеджер: {r.get('Менеджер')}\nПользователь: {r.get('Пользователь')}\nГруппа: {r.get('Группа')}\nСтатус: {status}\n---\n"
    await call.message.edit_text(text, reply_markup=get_admin_history_keyboard(page, has_prev, has_next), parse_mode='HTML')

# Хендлер: показать список менеджеров для админа
async def admin_manager_list_callback(call: types.CallbackQuery):
    # Получаем всех менеджеров из заявок
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records?page_size=1000'
    headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                records = data.get('list', [])
                managers = sorted(set(r.get('Менеджер') for r in records if r.get('Менеджер')))
                if not managers:
                    await call.message.edit_text('Менеджеры не найдены.')
                    return
                await call.message.edit_text('Выберите менеджера:', reply_markup=get_admin_manager_list_keyboard(managers))

# Хендлер: показать заявки выбранного менеджера
async def admin_manager_applications_callback(call: types.CallbackQuery):
    parts = call.data.split('_', 2)
    if len(parts) < 3:
        await call.answer('Ошибка данных!')
        return
    manager = parts[2]
    page = 1
    if 'page_' in manager:
        manager, page = manager.rsplit('page_', 1)
        page = int(page)
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records?page_size=1000'
    headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                records = [r for r in data.get('list', []) if r.get('Менеджер') == manager]
                total = len(records)
                start = (page-1)*5
                end = start+5
                page_records = records[start:end]
                has_prev = page > 1
                has_next = total > page*5
                if not page_records:
                    await call.message.edit_text('Заявок не найдено.', reply_markup=get_admin_back_to_managers_keyboard())
                    return
                text = f'📋 <b>Заявки менеджера {manager}</b>\n\n'
                for r in page_records:
                    status = r.get('Статус') or r.get('ck2mdpjv0b3hyml', '—')
                    text += f"Номер: {r.get('Номер')}\nПользователь: {r.get('Пользователь')}\nГруппа: {r.get('Группа')}\nСтатус: {status}\n---\n"
                kb = get_admin_back_to_managers_keyboard()
                if has_prev:
                    kb.insert(types.InlineKeyboardButton('⬅️ Назад', callback_data=f'admin_manager_{manager}page_{page-1}'))
                if has_next:
                    kb.insert(types.InlineKeyboardButton('Вперёд ➡️', callback_data=f'admin_manager_{manager}page_{page+1}'))
                await call.message.edit_text(text, reply_markup=kb, parse_mode='HTML')

# Хендлер: возврат к списку менеджеров
async def admin_back_to_managers_callback(call: types.CallbackQuery):
    await admin_manager_list_callback(call)

# Регистрация хендлеров
def register_support_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(manager_accept_callback, application_cb.filter())

# Регистрация хендлеров истории

def register_history_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(manager_history_callback, lambda c: c.data.startswith('manager_history_'))
    dp.register_callback_query_handler(admin_history_callback, lambda c: c.data.startswith('admin_history_'))
    dp.register_callback_query_handler(admin_manager_list_callback, lambda c: c.data == 'admin_history_page_1')
    dp.register_callback_query_handler(admin_manager_list_callback, lambda c: c.data == 'admin_back_to_managers')
    dp.register_callback_query_handler(admin_manager_applications_callback, lambda c: c.data.startswith('admin_manager_')) 