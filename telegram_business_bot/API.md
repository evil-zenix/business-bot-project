# 📡 API Документация

## 🗄️ Database (db.py)

### Класс `Database`

Основной класс для работы с SQLite базой данных.

#### Методы

##### `init_db()`
Инициализация базы данных, создание таблиц.

```python
await db.init_db()
```

##### `add_scenario()`
Добавление нового сценария.

```python
scenario_id = await db.add_scenario(
    trigger_type='contains',      # 'exact', 'contains', 'callback'
    trigger_value='привет',       # Текст триггера
    response_text='Здравствуйте!', # Текст ответа
    keyboard_json='[...]',        # JSON клавиатуры (опционально)
    is_reminder=False,            # Это напоминание?
    reminder_delay_min=0          # Задержка в минутах
)
```

##### `get_all_scenarios()`
Получение всех сценариев.

```python
scenarios = await db.get_all_scenarios(active_only=True)
# Возвращает: List[Dict]
```

##### `get_scenario_by_id()`
Получение сценария по ID.

```python
scenario = await db.get_scenario_by_id(scenario_id=1)
# Возвращает: Dict или None
```

##### `update_scenario()`
Обновление сценария.

```python
await db.update_scenario(
    scenario_id=1,
    trigger_value='новый триггер',  # Опционально
    response_text='новый ответ',    # Опционально
    # и другие поля...
)
```

##### `delete_scenario()`
Удаление сценария.

```python
await db.delete_scenario(scenario_id=1)
```

##### `toggle_scenario_active()`
Переключение активности сценария.

```python
await db.toggle_scenario_active(scenario_id=1)
```

##### `find_matching_scenario()`
Поиск подходящего сценария.

```python
scenario = await db.find_matching_scenario(
    message_text='привет',           # Текст сообщения
    callback_data='button_callback'  # Или callback (опционально)
)
# Возвращает: Dict или None
```

##### `save_business_connection()`
Сохранение информации о подключении.

```python
await db.save_business_connection(
    business_connection_id='abc123',
    user_id=123456789,
    can_reply=True
)
```

---

## ⌨️ Keyboards (keyboards.py)

### Функции создания клавиатур

##### `get_admin_menu_keyboard()`
Главное меню админ-панели.

```python
keyboard = get_admin_menu_keyboard()
```

##### `get_trigger_type_keyboard()`
Выбор типа триггера.

```python
keyboard = get_trigger_type_keyboard()
```

##### `get_yes_no_keyboard()`
Клавиатура Да/Нет.

```python
keyboard = get_yes_no_keyboard(
    yes_callback='yes_action',
    no_callback='no_action'
)
```

##### `get_scenarios_list_keyboard()`
Список сценариев с пагинацией.

```python
keyboard = get_scenarios_list_keyboard(
    scenarios=scenarios_list,
    page=0,
    page_size=5
)
```

##### `create_inline_keyboard_from_json()`
Создание клавиатуры из JSON.

```python
keyboard = create_inline_keyboard_from_json(
    keyboard_json='[{"text":"Кнопка","callback_data":"callback1"}]'
)
```

##### `keyboard_to_json()`
Конвертация кнопок в JSON.

```python
json_string = keyboard_to_json([
    {'text': 'Кнопка 1', 'callback_data': 'cb1'},
    {'text': 'Кнопка 2', 'callback_data': 'cb2'}
])
```

---

## 🔄 States (states.py)

### FSM Состояния

#### `AddScenarioStates`
Состояния для добавления сценария.

```python
class AddScenarioStates(StatesGroup):
    choosing_trigger_type = State()
    entering_trigger_value = State()
    entering_response_text = State()
    asking_for_buttons = State()
    entering_button_text = State()
    entering_button_callback = State()
    asking_for_more_buttons = State()
    asking_for_reminder = State()
    entering_reminder_delay = State()
    confirming_scenario = State()
```

#### `EditScenarioStates`
Состояния для редактирования.

```python
class EditScenarioStates(StatesGroup):
    selecting_scenario = State()
    choosing_field = State()
    entering_new_value = State()
```

#### `DeleteScenarioStates`
Состояния для удаления.

```python
class DeleteScenarioStates(StatesGroup):
    selecting_scenario = State()
    confirming_deletion = State()
```

---

## 👤 Admin Handlers (handlers/admin.py)

### Команды

##### `/admin`
Открытие админ-панели.

```python
@router.message(Command("admin"))
async def cmd_admin(message: Message)
```

### Callback обработчики

##### Добавление сценария
```python
@router.callback_query(F.data == "admin_add_scenario")
async def start_add_scenario(callback: CallbackQuery, state: FSMContext)
```

##### Список сценариев
```python
@router.callback_query(F.data == "admin_list_scenarios")
async def list_scenarios(callback: CallbackQuery, state: FSMContext)
```

##### Редактирование
```python
@router.callback_query(F.data.startswith("edit_scenario_"))
async def edit_scenario_choose_field(callback: CallbackQuery, state: FSMContext)
```

##### Удаление
```python
@router.callback_query(F.data.startswith("delete_scenario_"))
async def confirm_delete_scenario(callback: CallbackQuery, state: FSMContext)
```

---

## 💼 Business Handlers (handlers/business.py)

### Обработчики

##### Подключение бизнес-аккаунта
```python
@router.business_connection()
async def on_business_connection(event: BusinessConnection)
```

##### Входящие сообщения от клиентов
```python
@router.business_message(F.text)
async def handle_business_message(message: Message, bot: Bot)
```

Логика:
1. Проверка `business_connection_id`
2. Поиск подходящего сценария
3. Отправка ответа
4. Планирование напоминания (если нужно)

##### Callback от кнопок
```python
@router.callback_query(F.data.startswith("scenario_"))
async def handle_scenario_callback(callback: CallbackQuery, bot: Bot)
```

##### Отправка напоминания
```python
async def send_reminder(
    bot: Bot,
    chat_id: int,
    text: str,
    business_connection_id: str,
    scenario_id: int,
    keyboard_json: str = None
)
```

---

## 🔧 Config (config.py)

### Переменные конфигурации

```python
BOT_TOKEN       # Токен бота
ADMIN_IDS       # Список ID администраторов
DB_PATH         # Путь к базе данных
LOG_LEVEL       # Уровень логирования
```

---

## 📊 Структура данных

### Таблица `scenarios`

```sql
CREATE TABLE scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_type TEXT NOT NULL,           -- 'exact', 'contains', 'callback'
    trigger_value TEXT NOT NULL,          -- Значение триггера
    response_text TEXT NOT NULL,          -- Текст ответа
    keyboard_json TEXT,                   -- JSON кнопок (nullable)
    is_reminder INTEGER DEFAULT 0,        -- 0 или 1
    reminder_delay_min INTEGER DEFAULT 0, -- Минуты
    active INTEGER DEFAULT 1,             -- 0 или 1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Таблица `business_connections`

```sql
CREATE TABLE business_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_connection_id TEXT UNIQUE NOT NULL,
    user_id INTEGER,
    can_reply INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Таблица `reminder_history`

```sql
CREATE TABLE reminder_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER,
    chat_id INTEGER,
    business_connection_id TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
)
```

---

## 🔄 Типы триггеров

### `exact` - Точная фраза
Срабатывает при точном совпадении (регистр не важен).

```python
trigger_value = 'привет'
# Сработает: "привет", "Привет", "ПРИВЕТ"
# НЕ сработает: "приветик", "привет как дела"
```

### `contains` - Содержит слово
Срабатывает если в сообщении есть слово.

```python
trigger_value = 'цена'
# Сработает: "какая цена?", "узнать цены", "прайс лист"
```

### `callback` - Callback кнопки
Срабатывает при нажатии кнопки.

```python
trigger_value = 'schedule_full'
# Кнопка с callback_data='schedule_full'
```

---

## 📱 Формат JSON клавиатуры

```json
[
  {
    "text": "Текст кнопки 1",
    "callback_data": "callback_1"
  },
  {
    "text": "Текст кнопки 2",
    "callback_data": "callback_2"
  }
]
```

---

## 🎯 Примеры использования API

### Добавление сценария программно

```python
from db import db

# Инициализация БД
await db.init_db()

# Добавление сценария
scenario_id = await db.add_scenario(
    trigger_type='contains',
    trigger_value='расписание',
    response_text='<b>Наше расписание:</b>\nПн-Пт: 9:00-18:00',
    keyboard_json='[{"text":"Полное расписание","callback_data":"schedule_full"}]',
    is_reminder=False,
    reminder_delay_min=0
)

print(f"Создан сценарий ID: {scenario_id}")
```

### Поиск сценария

```python
# По тексту
scenario = await db.find_matching_scenario(
    message_text='какое расписание?'
)

# По callback
scenario = await db.find_matching_scenario(
    message_text=None,
    callback_data='schedule_full'
)

if scenario:
    print(f"Найден: {scenario['response_text']}")
else:
    print("Сценарий не найден")
```

### Обновление сценария

```python
# Изменить только текст ответа
await db.update_scenario(
    scenario_id=1,
    response_text='Новый текст ответа'
)

# Изменить несколько полей
await db.update_scenario(
    scenario_id=1,
    trigger_value='новый триггер',
    response_text='новый ответ',
    is_reminder=True,
    reminder_delay_min=60
)
```

---

## 🔌 Работа с Telegram Business API

### Отправка сообщения от имени бизнес-аккаунта

```python
await bot.send_message(
    chat_id=client_chat_id,
    text="Ваше сообщение",
    business_connection_id=business_connection_id,
    reply_markup=keyboard,  # Опционально
    parse_mode='HTML'       # Опционально
)
```

### Отметка сообщения как прочитанного

```python
await bot.read_business_message(
    business_connection_id=business_connection_id,
    chat_id=client_chat_id
)
```

---

## ⏰ Работа с напоминаниями

### Планирование напоминания

```python
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.start()

# Запланировать отправку через 60 минут
run_time = datetime.now() + timedelta(minutes=60)

scheduler.add_job(
    send_reminder,
    'date',
    run_date=run_time,
    args=[bot, chat_id, text, business_connection_id, scenario_id],
    id=f"reminder_{scenario_id}_{chat_id}_{datetime.now().timestamp()}"
)
```

---

## 🛡️ Проверка прав администратора

```python
from config import ADMIN_IDS

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Использование
if not is_admin(message.from_user.id):
    await message.answer("❌ Нет доступа")
    return
```

---

## 📝 Логирование

```python
import logging

logger = logging.getLogger(__name__)

# Примеры
logger.info("Сценарий добавлен")
logger.warning("Сценарий не найден")
logger.error("Ошибка БД", exc_info=True)
logger.debug("Отладочная информация")
```

---

## 🔍 Фильтры aiogram

### Используемые фильтры

```python
# Команды
@router.message(Command("admin"))

# Callback query
@router.callback_query(F.data == "admin_back")
@router.callback_query(F.data.startswith("scenario_"))

# Business сообщения
@router.business_message(F.text)
@router.business_connection()

# FSM состояния
@router.message(AddScenarioStates.entering_trigger_value)
@router.callback_query(AddScenarioStates.asking_for_buttons)
```

---

## 🚀 Расширение функционала

### Добавление нового типа триггера

1. Обновите `find_matching_scenario()` в `db.py`:

```python
elif trigger_type == 'custom_type':
    # Ваша логика
    if custom_condition:
        return scenario
```

2. Добавьте кнопку в `keyboards.py`:

```python
builder.row(InlineKeyboardButton(
    text="🆕 Новый тип",
    callback_data="trigger_custom_type"
))
```

3. Обработайте в `admin.py`:

```python
@router.callback_query(
    AddScenarioStates.choosing_trigger_type,
    F.data == "trigger_custom_type"
)
async def process_custom_trigger_type(callback, state):
    # Ваша логика
    pass
```

---

## 📚 Полезные ссылки

- [aiogram документация](https://docs.aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [APScheduler документация](https://apscheduler.readthedocs.io/)
- [aiosqlite документация](https://aiosqlite.omnilib.dev/)

---

Это базовая API документация. Для более подробной информации смотрите комментарии в коде.
