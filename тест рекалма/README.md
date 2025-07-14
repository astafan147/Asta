# Telegram Bot для работы с группами

Бот для управления заявками пользователей в различные группы Telegram.

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
# Токен бота Telegram
BOT_TOKEN=your_bot_token_here

# ID чата группы менеджеров
MANAGERS_CHAT_ID=-1002764122238

# ID администратора
ADMIN_ID=759408708

# Настройки NocoDB
NOCODB_TOKEN=JsrSO5j3OTcWAd43F8QcCaboCEmV_Zl6J9RrTvEA
NOCODB_TABLE=mcq244phcmkcf2o
```

3. Запустите бота:
```bash
python bot.py
```

## Функциональность

- Выбор группы из списка
- Отправка заявок менеджерам
- Принятие заявок менеджерами
- Сохранение данных в NocoDB
- Обработка ошибок

## Структура проекта

- `bot.py` - основной файл бота
- `config.py` - конфигурация
- `handlers/` - обработчики сообщений
- `keyboards/` - клавиатуры
- `middlewares/` - промежуточное ПО
- `utils/` - утилиты 