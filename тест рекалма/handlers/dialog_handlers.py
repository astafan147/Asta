from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import any_state
from utils.dialog_manager import dialog_manager
from keyboards.user import get_main_menu_keyboard
import logging
from utils.nocodb import NOCODB_TOKEN, NOCODB_TABLE
import aiohttp
from config import ADMIN_IDS
from keyboards.user import GROUPS

logger = logging.getLogger(__name__)

# Обработчик текстовых сообщений в диалоге
async def handle_dialog_message(message: types.Message, state: FSMContext):
    """Обрабатывает текстовые сообщения в диалоге"""
    user_id = message.from_user.id
    
    # Проверяем, участвует ли пользователь в диалоге
    dialog_id = dialog_manager.is_user_in_dialog(user_id)
    if not dialog_id:
        return
    
    participants = dialog_manager.get_dialog_participants(dialog_id)
    if not participants:
        return
    
    user_id_dialog, manager_id, group_name = participants
    
    # Определяем получателя сообщения
    recipient_id = manager_id if user_id == user_id_dialog else user_id_dialog
    
    # Определяем, кто отправитель и кто получатель
    is_manager_sender = (user_id == manager_id)
    is_user_recipient = (recipient_id == user_id_dialog)

    # Формируем подпись отправителя
    if is_manager_sender and is_user_recipient:
        sender_label = 'менеджера'
    else:
        sender_label = f"{('@' + message.from_user.username) if message.from_user.username else message.from_user.full_name}"

    # Отправляем сообщение получателю
    try:
        sent_message = await message.bot.send_message(
            recipient_id,
            f"💬 Сообщение от {('менеджера' if is_manager_sender and is_user_recipient else sender_label)}:\n\n{message.text}",
            reply_markup=dialog_manager.get_dialog_keyboard(is_manager=(recipient_id == manager_id))
        )
        
        # Добавляем сообщения в историю диалога
        dialog_manager.add_message_to_dialog(dialog_id, message.message_id)
        dialog_manager.add_message_to_dialog(dialog_id, sent_message.message_id)
        
        # Подтверждаем отправку
        await message.answer("✅ Сообщение отправлено!", reply_markup=dialog_manager.get_dialog_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения в диалоге: {e}")
        await message.answer("❌ Ошибка отправки сообщения")

# Обработчик файлов в диалоге
async def handle_dialog_file(message: types.Message, state: FSMContext):
    """Обрабатывает файлы в диалоге"""
    user_id = message.from_user.id
    
    # Проверяем, участвует ли пользователь в диалоге
    dialog_id = dialog_manager.is_user_in_dialog(user_id)
    if not dialog_id:
        return
    
    participants = dialog_manager.get_dialog_participants(dialog_id)
    if not participants:
        return
    
    user_id_dialog, manager_id, group_name = participants
    
    # Определяем получателя сообщения
    recipient_id = manager_id if user_id == user_id_dialog else user_id_dialog
    
    # Определяем, кто отправитель и кто получатель
    is_manager_sender = (user_id == manager_id)
    is_user_recipient = (recipient_id == user_id_dialog)
    
    # Для файлов:
    # Формируем подпись отправителя
    if is_manager_sender and is_user_recipient:
        sender_label = 'менеджера'
    else:
        sender_label = f"{('@' + message.from_user.username) if message.from_user.username else message.from_user.full_name}"

    # Отправляем файл получателю
    try:
        if message.document:
            sent_message = await message.bot.send_document(
                recipient_id,
                message.document.file_id,
                caption=f"📎 Файл от {('менеджера' if is_manager_sender and is_user_recipient else sender_label)}: {message.document.file_name}",
                reply_markup=dialog_manager.get_dialog_keyboard(is_manager=(recipient_id == manager_id))
            )
        elif message.photo:
            sent_message = await message.bot.send_photo(
                recipient_id,
                message.photo[-1].file_id,
                caption=f"🖼 Фото от {('менеджера' if is_manager_sender and is_user_recipient else sender_label)}",
                reply_markup=dialog_manager.get_dialog_keyboard(is_manager=(recipient_id == manager_id))
            )
        elif message.video:
            sent_message = await message.bot.send_video(
                recipient_id,
                message.video.file_id,
                caption=f"🎥 Видео от {('менеджера' if is_manager_sender and is_user_recipient else sender_label)}",
                reply_markup=dialog_manager.get_dialog_keyboard(is_manager=(recipient_id == manager_id))
            )
        else:
            await message.answer("❌ Неподдерживаемый тип файла")
            return
        
        # Добавляем сообщения в историю диалога
        dialog_manager.add_message_to_dialog(dialog_id, message.message_id)
        dialog_manager.add_message_to_dialog(dialog_id, sent_message.message_id)
        
        # Подтверждаем отправку
        await message.answer("✅ Файл отправлен!", reply_markup=dialog_manager.get_dialog_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка отправки файла в диалоге: {e}")
        await message.answer("❌ Ошибка отправки файла")

# Обработчик завершения диалога
async def end_dialog_callback(call: types.CallbackQuery, state: FSMContext):
    """Обрабатывает завершение диалога"""
    user_id = call.from_user.id
    
    # Проверяем, участвует ли пользователь в диалоге
    dialog_id = dialog_manager.is_user_in_dialog(user_id)
    if not dialog_id:
        await call.answer("❌ Диалог не найден")
        return
    
    participants = dialog_manager.get_dialog_participants(dialog_id)
    if not participants:
        await call.answer("❌ Диалог не найден")
        return
    
    user_id_dialog, manager_id, group_name = participants
    
    # Получаем username завершившего диалог
    ender_username = f"@{call.from_user.username}" if call.from_user.username else f"@{call.from_user.full_name}"
    
    # Уведомляем другого участника о завершении диалога
    other_user_id = manager_id if user_id == user_id_dialog else user_id_dialog
    
    try:
        await call.bot.send_message(
            other_user_id,
            f"🔚 Диалог завершен пользователем {ender_username}",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления о завершении диалога: {e}")
    
    # Завершаем диалог
    dialog_manager.end_dialog(dialog_id)

    # Если заявка не выполнена, обновляем поле cuuo5irznu0dyde через удаление и создание новой записи
    try:
        application_number = dialog_id.split('_')[-1]
        base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records?page_size=1000'
        headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    records = data.get('list', [])
                    record = next((r for r in records if str(r.get('Номер')) == str(application_number)), None)
                    if record:
                        record_id = record.get('Id')
                        # Если поле уже 'Работа выполнена', не обновляем
                        if record.get('cuuo5irznu0dyde') != 'Работа выполнена':
                            who = 'менеджер' if user_id == manager_id else 'пользователь'
                            # 1. Удаляем старую запись
                            del_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records/{record_id}'
                            await session.delete(del_url, headers=headers)
                            # 2. Копируем все поля, кроме Id, и обновляем статус
                            new_data = record.copy()
                            new_data.pop('Id', None)
                            new_data['ck2mdpjv0b3hyml'] = f'Завершил диалог {who}'
                            new_data['Статус'] = f'Завершил диалог {who}'
                            # 3. Создаём новую запись
                            post_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records'
                            await session.post(post_url, json=new_data, headers=headers)
    except Exception as e:
        logger.error(f'Ошибка обновления поля завершения заявки: {e}')
    
    # Отправляем сообщение о завершении
    await call.message.edit_text(
        f"🔚 Диалог завершен\n\n"
        f"Группа: {group_name}\n"
        f"Завершил: {ender_username}",
        reply_markup=get_main_menu_keyboard()
    )
    
    await call.answer("Диалог завершен")

# Обработчик информации о заявке (только для менеджеров)
async def dialog_info_callback(call: types.CallbackQuery, state: FSMContext):
    """Показывает информацию о заявке"""
    user_id = call.from_user.id
    
    # Проверяем, участвует ли пользователь в диалоге
    dialog_id = dialog_manager.is_user_in_dialog(user_id)
    if not dialog_id:
        await call.answer("❌ Диалог не найден")
        return
    
    participants = dialog_manager.get_dialog_participants(dialog_id)
    if not participants:
        await call.answer("❌ Диалог не найден")
        return
    
    user_id_dialog, manager_id, group_name = participants
    
    # Проверяем, что это менеджер
    if user_id != manager_id:
        await call.answer("❌ Эта функция доступна только менеджерам")
        return
    
    # Извлекаем номер заявки из dialog_id
    application_number = dialog_id.split('_')[-1]
    
    # Получаем username пользователя
    try:
        user_info = await call.bot.get_chat(user_id_dialog)
        user_username = f"@{user_info.username}" if user_info.username else f"@user_{user_id_dialog}"
    except Exception as e:
        user_username = f"@user_{user_id_dialog}"
    
    # Получаем username менеджера
    manager_username = f"@{call.from_user.username}" if call.from_user.username else f"@manager_{manager_id}"
    
    info_text = (
        f"📋 Информация о заявке\n\n"
        f"Номер заявки: {application_number}\n"
        f"Группа: {group_name}\n"
        f"Пользователь: {user_username}\n"
        f"Менеджер: {manager_username}"
    )
    
    await call.message.edit_text(
        info_text,
        reply_markup=dialog_manager.get_dialog_keyboard(is_manager=True)
    )
    
    await call.answer()

# Обработчик кнопки 'Заявка выполнена'
async def dialog_done_callback(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    dialog_id = dialog_manager.is_user_in_dialog(user_id)
    if not dialog_id:
        await call.answer("❌ Диалог не найден")
        return
    participants = dialog_manager.get_dialog_participants(dialog_id)
    if not participants:
        await call.answer("❌ Диалог не найден")
        return
    user_id_dialog, manager_id, group_name = participants
    if user_id != manager_id:
        await call.answer("❌ Только менеджер может завершить заявку")
        return
    application_number = dialog_id.split('_')[-1]
    # Ищем заявку в NocoDB и меняем статус
    base_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records?page_size=1000'
    headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                records = data.get('list', [])
                record = next((r for r in records if str(r.get('Номер')) == str(application_number)), None)
                if record:
                    record_id = record.get('Id')
                    # 1. Удаляем старую запись
                    del_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records/{record_id}'
                    await session.delete(del_url, headers=headers)
                    # 2. Копируем все поля, кроме Id, и обновляем статус
                    new_data = record.copy()
                    new_data.pop('Id', None)
                    new_data['ck2mdpjv0b3hyml'] = 'Выполнена'
                    new_data['Статус'] = 'Выполнена'
                    # 3. Создаём новую запись
                    post_url = f'https://app.nocodb.com/api/v2/tables/{NOCODB_TABLE}/records'
                    await session.post(post_url, json=new_data, headers=headers)
    # Уведомляем админа
    try:
        for admin_id in ADMIN_IDS:
            await call.bot.send_message(admin_id, f"✅ Заявка {application_number} по группе '{group_name}' выполнена менеджером!")
    except Exception:
        pass
    await call.message.edit_text(f"✅ Заявка {application_number} отмечена как выполненная!", reply_markup=None)
    await call.answer("Заявка отмечена как выполненная!")
    # Оповещение пользователя о выполнении заявки
    try:
        # Получаем user_id пользователя и ссылку на группу
        user_id_dialog, manager_id, group_name = participants
        group_url = None
        for name, url in GROUPS:
            if name == group_name:
                group_url = url
                break
        kb = None
        if group_url:
            kb = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('Посмотреть группу', url=group_url)
            )
        await call.bot.send_message(
            user_id_dialog,
            f'✅ Ваша заявка {application_number} по группе "{group_name}" выполнена!\nПроверьте объявление в группе.',
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f'Ошибка уведомления пользователя о выполнении заявки: {e}')

# Регистрация хендлеров
def register_dialog_handlers(dp: Dispatcher):
    # Обработчики сообщений в диалоге
    dp.register_message_handler(
        handle_dialog_message, 
        content_types=['text'],
        state=any_state
    )
    
    # Обработчики файлов в диалоге
    dp.register_message_handler(
        handle_dialog_file,
        content_types=['document', 'photo', 'video'],
        state=any_state
    )
    
    # Обработчики callback кнопок
    dp.register_callback_query_handler(
        end_dialog_callback,
        lambda c: c.data == "end_dialog"
    )
    
    dp.register_callback_query_handler(
        dialog_info_callback,
        lambda c: c.data == "dialog_info"
    ) 
    dp.register_callback_query_handler(dialog_done_callback, lambda c: c.data == "dialog_done") 