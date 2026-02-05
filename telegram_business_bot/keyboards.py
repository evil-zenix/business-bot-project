"""
Клавиатуры для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить сценарий", callback_data="admin_add_scenario"))
    builder.row(InlineKeyboardButton(text="📋 Список сценариев", callback_data="admin_list_scenarios"))
    builder.row(InlineKeyboardButton(text="✏️ Редактировать сценарий", callback_data="admin_edit_scenario"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить сценарий", callback_data="admin_delete_scenario"))
    builder.row(InlineKeyboardButton(text="⚙️ Настройки напоминаний", callback_data="admin_reminder_settings"))
    builder.row(InlineKeyboardButton(text="❌ Выход", callback_data="admin_exit"))
    return builder.as_markup()


def get_trigger_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа триггера"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎯 Точная фраза", callback_data="trigger_exact"))
    builder.row(InlineKeyboardButton(text="🔍 Содержит слово", callback_data="trigger_contains"))
    builder.row(InlineKeyboardButton(text="🔘 Callback кнопки", callback_data="trigger_callback"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))
    return builder.as_markup()


def get_yes_no_keyboard(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    """Клавиатура Да/Нет"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=yes_callback),
        InlineKeyboardButton(text="❌ Нет", callback_data=no_callback)
    )
    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура только с кнопкой Назад"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin_back"))
    return builder.as_markup()


def get_scenarios_list_keyboard(scenarios: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    """
    Клавиатура списка сценариев с пагинацией
    
    Args:
        scenarios: Список сценариев из БД
        page: Номер страницы (начиная с 0)
        page_size: Количество элементов на странице
    """
    builder = InlineKeyboardBuilder()
    
    # Определяем диапазон сценариев для текущей страницы
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_scenarios = scenarios[start_idx:end_idx]
    
    # Добавляем кнопки для каждого сценария
    for scenario in page_scenarios:
        trigger_type = scenario['trigger_type']
        trigger_value = scenario['trigger_value']
        is_active = "✅" if scenario['active'] else "❌"
        
        # Формируем текст кнопки
        button_text = f"{is_active} {trigger_type}: {trigger_value[:20]}..."
        builder.row(InlineKeyboardButton(
            text=button_text,
            callback_data=f"scenario_view_{scenario['id']}"
        ))
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"scenarios_page_{page-1}"))
    if end_idx < len(scenarios):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"scenarios_page_{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back"))
    return builder.as_markup()


def get_scenario_actions_keyboard(scenario_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий со сценарием"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_scenario_{scenario_id}"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_scenario_{scenario_id}"))
    builder.row(InlineKeyboardButton(text="🔄 Вкл/Выкл", callback_data=f"toggle_scenario_{scenario_id}"))
    builder.row(InlineKeyboardButton(text="🔙 К списку", callback_data="admin_list_scenarios"))
    return builder.as_markup()


def get_edit_field_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора поля для редактирования"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Триггер", callback_data="edit_field_trigger"))
    builder.row(InlineKeyboardButton(text="💬 Текст ответа", callback_data="edit_field_response"))
    builder.row(InlineKeyboardButton(text="⌨️ Кнопки", callback_data="edit_field_keyboard"))
    builder.row(InlineKeyboardButton(text="⏰ Напоминание", callback_data="edit_field_reminder"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_scenarios"))
    return builder.as_markup()


def create_inline_keyboard_from_json(keyboard_json: str) -> InlineKeyboardMarkup:
    """
    Создаёт InlineKeyboard из JSON
    
    Args:
        keyboard_json: JSON строка с данными кнопок
        Формат: [{"text": "Кнопка 1", "callback_data": "callback1"}, ...]
    """
    if not keyboard_json:
        return None
    
    try:
        buttons_data = json.loads(keyboard_json)
        builder = InlineKeyboardBuilder()
        
        for button_data in buttons_data:
            builder.row(InlineKeyboardButton(
                text=button_data['text'],
                callback_data=button_data['callback_data']
            ))
        
        return builder.as_markup()
    except (json.JSONDecodeError, KeyError):
        return None


def keyboard_to_json(buttons: list) -> str:
    """
    Конвертирует список кнопок в JSON
    
    Args:
        buttons: Список словарей [{"text": "...", "callback_data": "..."}, ...]
    
    Returns:
        JSON строка
    """
    return json.dumps(buttons, ensure_ascii=False)
