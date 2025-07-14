from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Список групп и их ссылок с эмодзи
GROUPS = [
    ("🛒 БАРАХОЛКА САХКОМ", "https://t.me/marketsakhcom_chat"),
    ("🏠 НЕДВИЖИМОСТЬ", "https://t.me/nedvizhka65"),
    ("🚧 СТРОЙПЛОЩАДКА", "https://t.me/sakhstroyka"),
    ("🌸 ЖЕНСКИЙ КЛУБ", "https://t.me/womanclub65"),
    ("🚗 АВТОРЫНОК", "https://t.me/AvtoDvizh65"),
    ("✅ ОБЬЯВЛЕНИЯ", "https://t.me/sakhbaraholka"),
    ("👍 ОТДАМ ДАРОМ", "https://t.me/OtdamDarom65"),
    ("🤝 ПРИМУ В ДАР", "https://t.me/+IwihgG76crU2NTAy"),
    ("🍤 МОРЕПРОДУКТЫ", "https://t.me/fishmarket65"),
    ("🥩 Урожай, улов, ПРОДУКТЫ", "https://t.me/+LzDRMnsXoulkYmQ6"),
    ("✅ БЮРО НАХОДОК", "https://t.me/+9BMJeTyn6qoxOGYy"),
    ("👩‍👦 МАМЫ И ДЕТКИ", "https://t.me/motherbaby65"),
    ("🌳 ДАЧА, САД И ОГОРОД. + БАНЯ", "https://t.me/garden65"),
    ("⛩ МЕБЕЛЬ+ интерьер", "https://t.me/+o23cn12z-MAyNmFi"),
    ("🦆 ОХОТА", "https://t.me/hunting_65"),
    ("🐟 РЫБАЛКА", "https://t.me/fishingsakh"),
    ("❓ ХОЧУ СПРОСИТЬ", "https://t.me/chssakhalin"),
    ("🐈 ДОМАШНИЕ ПИТОМЦЫ", "https://t.me/sakhzoofriend"),
]

# Клавиатура выбора группы (2 столбца)
def get_groups_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    for idx, (name, _) in enumerate(GROUPS):
        kb.insert(InlineKeyboardButton(name, callback_data=f"group_{idx}"))
    return kb

# Клавиатура действий внутри группы
def get_group_actions_keyboard(group_idx):
    group_url = GROUPS[group_idx][1]
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Написать менеджеру", callback_data=f"write_manager_{group_idx}"),
        InlineKeyboardButton("Посмотреть группу", url=group_url),
        InlineKeyboardButton("Назад", callback_data="back_to_groups")
    )
    return kb

# Клавиатура главного меню
def get_main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
        InlineKeyboardButton("📋 Выбрать группу", callback_data="select_group")
    )
    return kb 

# Клавиатура истории заявок менеджера с пагинацией

def get_manager_history_keyboard(page: int, has_prev: bool, has_next: bool):
    kb = InlineKeyboardMarkup(row_width=2)
    if has_prev:
        kb.insert(InlineKeyboardButton('⬅️ Назад', callback_data=f'manager_history_prev_{page-1}'))
    if has_next:
        kb.insert(InlineKeyboardButton('Вперёд ➡️', callback_data=f'manager_history_next_{page+1}'))
    return kb

# Клавиатура истории заявок админа с пагинацией

def get_admin_history_keyboard(page: int, has_prev: bool, has_next: bool):
    kb = InlineKeyboardMarkup(row_width=2)
    if has_prev:
        kb.insert(InlineKeyboardButton('⬅️ Назад', callback_data=f'admin_history_prev_{page-1}'))
    if has_next:
        kb.insert(InlineKeyboardButton('Вперёд ➡️', callback_data=f'admin_history_next_{page+1}'))
    return kb

# Клавиатура меню менеджера

def get_manager_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton('📋 Мои заявки', callback_data='manager_history_page_1'))
    return kb

# Клавиатура меню админа

def get_admin_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton('📋 Все заявки', callback_data='admin_history_page_1'))
    return kb 

def get_admin_manager_list_keyboard(managers):
    kb = InlineKeyboardMarkup(row_width=1)
    for m in managers:
        kb.add(InlineKeyboardButton(m or 'Без имени', callback_data=f'admin_manager_{m}'))
    kb.add(InlineKeyboardButton('📋 Все заявки', callback_data='admin_history_page_1'))
    return kb

def get_admin_back_to_managers_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton('⬅️ Назад к менеджерам', callback_data='admin_back_to_managers'))
    kb.add(InlineKeyboardButton('📋 Все заявки', callback_data='admin_history_page_1'))
    return kb 