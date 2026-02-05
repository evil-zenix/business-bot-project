"""
Админ-панель для управления сценариями
"""
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from db import db
from states import AddScenarioStates, EditScenarioStates, DeleteScenarioStates
from keyboards import (
    get_admin_menu_keyboard,
    get_trigger_type_keyboard,
    get_yes_no_keyboard,
    get_back_keyboard,
    get_scenarios_list_keyboard,
    get_scenario_actions_keyboard,
    get_edit_field_keyboard,
    keyboard_to_json
)

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id in ADMIN_IDS


# ============================================================================
# ГЛАВНОЕ МЕНЮ АДМИН-ПАНЕЛИ
# ============================================================================

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда /admin - открыть админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode='HTML'
    )


@router.callback_query(F.data == "admin_back")
async def admin_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню админки"""
    await state.clear()  # Очищаем состояние FSM
    await callback.message.edit_text(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == "admin_exit")
async def admin_exit(callback: CallbackQuery, state: FSMContext):
    """Выход из админ-панели"""
    await state.clear()
    await callback.message.edit_text("👋 До свидания!")
    await callback.answer()


# ============================================================================
# ДОБАВЛЕНИЕ СЦЕНАРИЯ
# ============================================================================

@router.callback_query(F.data == "admin_add_scenario")
async def start_add_scenario(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления сценария"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.set_state(AddScenarioStates.choosing_trigger_type)
    await callback.message.edit_text(
        "📝 <b>Добавление нового сценария</b>\n\n"
        "Шаг 1/5: Выберите тип триггера:",
        reply_markup=get_trigger_type_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(AddScenarioStates.choosing_trigger_type, F.data.startswith("trigger_"))
async def process_trigger_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа триггера"""
    trigger_type = callback.data.replace("trigger_", "")
    
    # Сохраняем тип триггера
    await state.update_data(trigger_type=trigger_type)
    
    # Переводим в человеческий вид
    type_names = {
        'exact': 'Точная фраза',
        'contains': 'Содержит слово',
        'callback': 'Callback кнопки'
    }
    type_name = type_names.get(trigger_type, trigger_type)
    
    await state.set_state(AddScenarioStates.entering_trigger_value)
    await callback.message.edit_text(
        f"📝 <b>Добавление сценария</b>\n\n"
        f"Тип триггера: <code>{type_name}</code>\n\n"
        f"Шаг 2/5: Введите триггер:\n"
        f"{'(Например: привет, расписание, цена)' if trigger_type != 'callback' else '(Например: schedule_full, price_info)'}",
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(AddScenarioStates.entering_trigger_value)
async def process_trigger_value(message: Message, state: FSMContext):
    """Обработка ввода триггера"""
    trigger_value = message.text.strip()
    
    if not trigger_value:
        await message.answer("❌ Триггер не может быть пустым. Попробуйте снова:")
        return
    
    # Сохраняем триггер
    await state.update_data(trigger_value=trigger_value)
    
    await state.set_state(AddScenarioStates.entering_response_text)
    await message.answer(
        f"📝 <b>Добавление сценария</b>\n\n"
        f"Триггер: <code>{trigger_value}</code>\n\n"
        f"Шаг 3/5: Введите текст ответа клиенту:\n"
        f"(Поддерживается HTML форматирование: <b>жирный</b>, <i>курсив</i>, <code>код</code>)",
        parse_mode='HTML'
    )


@router.message(AddScenarioStates.entering_response_text)
async def process_response_text(message: Message, state: FSMContext):
    """Обработка ввода текста ответа"""
    response_text = message.text
    
    if not response_text:
        await message.answer("❌ Текст ответа не может быть пустым. Попробуйте снова:")
        return
    
    # Сохраняем текст ответа
    await state.update_data(response_text=response_text, buttons=[])
    
    await state.set_state(AddScenarioStates.asking_for_buttons)
    await message.answer(
        f"📝 <b>Добавление сценария</b>\n\n"
        f"Шаг 4/5: Добавить inline-кнопки к ответу?",
        reply_markup=get_yes_no_keyboard("add_buttons_yes", "add_buttons_no"),
        parse_mode='HTML'
    )


@router.callback_query(AddScenarioStates.asking_for_buttons, F.data == "add_buttons_yes")
async def start_adding_buttons(callback: CallbackQuery, state: FSMContext):
    """Начало добавления кнопок"""
    await state.set_state(AddScenarioStates.entering_button_text)
    await callback.message.edit_text(
        "⌨️ <b>Добавление кнопки</b>\n\n"
        "Введите текст кнопки:",
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(AddScenarioStates.entering_button_text)
async def process_button_text(message: Message, state: FSMContext):
    """Обработка текста кнопки"""
    button_text = message.text.strip()
    
    if not button_text:
        await message.answer("❌ Текст кнопки не может быть пустым. Попробуйте снова:")
        return
    
    await state.update_data(current_button_text=button_text)
    await state.set_state(AddScenarioStates.entering_button_callback)
    await message.answer(
        f"⌨️ <b>Добавление кнопки</b>\n\n"
        f"Текст кнопки: <code>{button_text}</code>\n\n"
        f"Введите callback_data для кнопки:\n"
        f"(Например: schedule_full, price_info)",
        parse_mode='HTML'
    )


@router.message(AddScenarioStates.entering_button_callback)
async def process_button_callback(message: Message, state: FSMContext):
    """Обработка callback кнопки"""
    callback_data = message.text.strip()
    
    if not callback_data:
        await message.answer("❌ Callback не может быть пустым. Попробуйте снова:")
        return
    
    # Получаем текущие данные
    data = await state.get_data()
    button_text = data['current_button_text']
    buttons = data.get('buttons', [])
    
    # Добавляем кнопку
    buttons.append({
        'text': button_text,
        'callback_data': callback_data
    })
    
    await state.update_data(buttons=buttons)
    await state.set_state(AddScenarioStates.asking_for_more_buttons)
    
    # Показываем список добавленных кнопок
    buttons_list = "\n".join([f"• {b['text']} → {b['callback_data']}" for b in buttons])
    
    await message.answer(
        f"✅ Кнопка добавлена!\n\n"
        f"<b>Список кнопок:</b>\n{buttons_list}\n\n"
        f"Добавить ещё одну кнопку?",
        reply_markup=get_yes_no_keyboard("add_more_buttons_yes", "add_more_buttons_no"),
        parse_mode='HTML'
    )


@router.callback_query(AddScenarioStates.asking_for_more_buttons, F.data == "add_more_buttons_yes")
async def add_more_buttons(callback: CallbackQuery, state: FSMContext):
    """Добавить ещё кнопку"""
    await state.set_state(AddScenarioStates.entering_button_text)
    await callback.message.edit_text(
        "⌨️ <b>Добавление кнопки</b>\n\n"
        "Введите текст кнопки:",
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(
    AddScenarioStates.asking_for_buttons,
    F.data.in_(["add_buttons_no", "add_more_buttons_no"])
)
async def finish_buttons_ask_reminder(callback: CallbackQuery, state: FSMContext):
    """Закончили с кнопками, спрашиваем про напоминание"""
    await state.set_state(AddScenarioStates.asking_for_reminder)
    await callback.message.edit_text(
        f"📝 <b>Добавление сценария</b>\n\n"
        f"Шаг 5/5: Это сценарий с напоминанием?\n"
        f"(Если да, бот отправит повторное сообщение через заданное время)",
        reply_markup=get_yes_no_keyboard("reminder_yes", "reminder_no"),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(AddScenarioStates.asking_for_reminder, F.data == "reminder_yes")
async def ask_reminder_delay(callback: CallbackQuery, state: FSMContext):
    """Спросить задержку напоминания"""
    await state.set_state(AddScenarioStates.entering_reminder_delay)
    await callback.message.edit_text(
        "⏰ <b>Настройка напоминания</b>\n\n"
        "Введите задержку в минутах:\n"
        "(Например: 60 для 1 часа, 1440 для суток)",
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(AddScenarioStates.entering_reminder_delay)
async def process_reminder_delay(message: Message, state: FSMContext):
    """Обработка задержки напоминания"""
    try:
        delay_minutes = int(message.text.strip())
        if delay_minutes <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное число (минуты). Попробуйте снова:")
        return
    
    await state.update_data(
        is_reminder=True,
        reminder_delay_min=delay_minutes
    )
    
    await confirm_and_save_scenario(message, state)


@router.callback_query(AddScenarioStates.asking_for_reminder, F.data == "reminder_no")
async def no_reminder(callback: CallbackQuery, state: FSMContext):
    """Без напоминания"""
    await state.update_data(
        is_reminder=False,
        reminder_delay_min=0
    )
    
    await confirm_and_save_scenario(callback.message, state)
    await callback.answer()


async def confirm_and_save_scenario(message: Message, state: FSMContext):
    """Подтверждение и сохранение сценария"""
    data = await state.get_data()
    
    # Формируем JSON кнопок
    keyboard_json = None
    if data.get('buttons'):
        keyboard_json = keyboard_to_json(data['buttons'])
    
    # Сохраняем в БД
    scenario_id = await db.add_scenario(
        trigger_type=data['trigger_type'],
        trigger_value=data['trigger_value'],
        response_text=data['response_text'],
        keyboard_json=keyboard_json,
        is_reminder=data.get('is_reminder', False),
        reminder_delay_min=data.get('reminder_delay_min', 0)
    )
    
    # Формируем сообщение с подтверждением
    type_names = {
        'exact': 'Точная фраза',
        'contains': 'Содержит слово',
        'callback': 'Callback'
    }
    
    confirmation = (
        f"✅ <b>Сценарий успешно создан!</b>\n\n"
        f"ID: <code>{scenario_id}</code>\n"
        f"Тип: {type_names.get(data['trigger_type'])}\n"
        f"Триггер: <code>{data['trigger_value']}</code>\n"
        f"Ответ: {data['response_text'][:100]}{'...' if len(data['response_text']) > 100 else ''}\n"
    )
    
    if data.get('buttons'):
        confirmation += f"Кнопок: {len(data['buttons'])}\n"
    
    if data.get('is_reminder'):
        confirmation += f"⏰ Напоминание через: {data['reminder_delay_min']} мин\n"
    
    await message.answer(
        confirmation,
        reply_markup=get_back_keyboard(),
        parse_mode='HTML'
    )
    
    await state.clear()


# ============================================================================
# СПИСОК СЦЕНАРИЕВ
# ============================================================================

@router.callback_query(F.data == "admin_list_scenarios")
async def list_scenarios(callback: CallbackQuery, state: FSMContext):
    """Показать список сценариев"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.clear()
    scenarios = await db.get_all_scenarios()
    
    if not scenarios:
        await callback.message.edit_text(
            "📋 <b>Список сценариев</b>\n\n"
            "Сценариев пока нет. Добавьте первый!",
            reply_markup=get_back_keyboard(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"📋 <b>Список сценариев</b>\n\n"
        f"Всего: {len(scenarios)}",
        reply_markup=get_scenarios_list_keyboard(scenarios, page=0),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("scenarios_page_"))
async def scenarios_pagination(callback: CallbackQuery):
    """Пагинация списка сценариев"""
    page = int(callback.data.split("_")[-1])
    scenarios = await db.get_all_scenarios()
    
    await callback.message.edit_reply_markup(
        reply_markup=get_scenarios_list_keyboard(scenarios, page=page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("scenario_view_"))
async def view_scenario(callback: CallbackQuery):
    """Просмотр детальной информации о сценарии"""
    scenario_id = int(callback.data.split("_")[-1])
    scenario = await db.get_scenario_by_id(scenario_id)
    
    if not scenario:
        await callback.answer("❌ Сценарий не найден", show_alert=True)
        return
    
    # Формируем детальную информацию
    type_names = {
        'exact': 'Точная фраза',
        'contains': 'Содержит слово',
        'callback': 'Callback'
    }
    
    status = "✅ Активен" if scenario['active'] else "❌ Неактивен"
    
    info = (
        f"📝 <b>Сценарий #{scenario['id']}</b>\n\n"
        f"Статус: {status}\n"
        f"Тип: {type_names.get(scenario['trigger_type'])}\n"
        f"Триггер: <code>{scenario['trigger_value']}</code>\n\n"
        f"<b>Ответ:</b>\n{scenario['response_text']}\n"
    )
    
    if scenario['keyboard_json']:
        import json
        try:
            buttons = json.loads(scenario['keyboard_json'])
            info += f"\n<b>Кнопки:</b>\n"
            for btn in buttons:
                info += f"• {btn['text']} → {btn['callback_data']}\n"
        except:
            pass
    
    if scenario['is_reminder']:
        info += f"\n⏰ <b>Напоминание через:</b> {scenario['reminder_delay_min']} мин"
    
    await callback.message.edit_text(
        info,
        reply_markup=get_scenario_actions_keyboard(scenario_id),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_scenario_"))
async def toggle_scenario(callback: CallbackQuery):
    """Переключить активность сценария"""
    scenario_id = int(callback.data.split("_")[-1])
    await db.toggle_scenario_active(scenario_id)
    
    # Обновляем отображение
    await view_scenario(callback)
    await callback.answer("✅ Статус изменён")


# ============================================================================
# РЕДАКТИРОВАНИЕ СЦЕНАРИЯ
# ============================================================================

@router.callback_query(F.data == "admin_edit_scenario")
async def start_edit_scenario(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования - выбор сценария"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    scenarios = await db.get_all_scenarios()
    
    if not scenarios:
        await callback.message.edit_text(
            "❌ Нет сценариев для редактирования",
            reply_markup=get_back_keyboard(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    
    await state.set_state(EditScenarioStates.selecting_scenario)
    await callback.message.edit_text(
        "✏️ <b>Редактирование сценария</b>\n\n"
        "Выберите сценарий:",
        reply_markup=get_scenarios_list_keyboard(scenarios, page=0),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_scenario_"))
async def edit_scenario_choose_field(callback: CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования"""
    scenario_id = int(callback.data.split("_")[-1])
    
    # Сохраняем ID в состояние
    await state.update_data(editing_scenario_id=scenario_id)
    await state.set_state(EditScenarioStates.choosing_field)
    
    scenario = await db.get_scenario_by_id(scenario_id)
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование сценария #{scenario_id}</b>\n\n"
        f"Триггер: <code>{scenario['trigger_value']}</code>\n\n"
        f"Что хотите изменить?",
        reply_markup=get_edit_field_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(EditScenarioStates.choosing_field, F.data.startswith("edit_field_"))
async def edit_field_prompt(callback: CallbackQuery, state: FSMContext):
    """Запрос нового значения для поля"""
    field = callback.data.replace("edit_field_", "")
    
    await state.update_data(editing_field=field)
    await state.set_state(EditScenarioStates.entering_new_value)
    
    prompts = {
        'trigger': "Введите новый триггер:",
        'response': "Введите новый текст ответа:",
        'keyboard': "Введите кнопки в формате JSON или отправьте 'none' для удаления:\n[{\"text\":\"Кнопка\",\"callback_data\":\"callback\"}]",
        'reminder': "Введите новую задержку в минутах (или 0 для отключения напоминания):"
    }
    
    prompt = prompts.get(field, "Введите новое значение:")
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование</b>\n\n{prompt}",
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(EditScenarioStates.entering_new_value)
async def save_edited_value(message: Message, state: FSMContext):
    """Сохранение отредактированного значения"""
    data = await state.get_data()
    scenario_id = data['editing_scenario_id']
    field = data['editing_field']
    new_value = message.text.strip()
    
    try:
        if field == 'trigger':
            await db.update_scenario(scenario_id, trigger_value=new_value)
        elif field == 'response':
            await db.update_scenario(scenario_id, response_text=new_value)
        elif field == 'keyboard':
            if new_value.lower() == 'none':
                await db.update_scenario(scenario_id, keyboard_json=None)
            else:
                import json
                # Проверяем валидность JSON
                json.loads(new_value)
                await db.update_scenario(scenario_id, keyboard_json=new_value)
        elif field == 'reminder':
            delay = int(new_value)
            await db.update_scenario(
                scenario_id,
                is_reminder=(delay > 0),
                reminder_delay_min=delay
            )
        
        await message.answer(
            "✅ Сценарий обновлён!",
            reply_markup=get_back_keyboard()
        )
        await state.clear()
    
    except Exception as e:
        logger.error(f"Ошибка обновления сценария: {e}")
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
        )


# ============================================================================
# УДАЛЕНИЕ СЦЕНАРИЯ
# ============================================================================

@router.callback_query(F.data == "admin_delete_scenario")
async def start_delete_scenario(callback: CallbackQuery, state: FSMContext):
    """Начало удаления - выбор сценария"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    scenarios = await db.get_all_scenarios()
    
    if not scenarios:
        await callback.message.edit_text(
            "❌ Нет сценариев для удаления",
            reply_markup=get_back_keyboard(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    
    await state.set_state(DeleteScenarioStates.selecting_scenario)
    await callback.message.edit_text(
        "🗑 <b>Удаление сценария</b>\n\n"
        "Выберите сценарий для удаления:",
        reply_markup=get_scenarios_list_keyboard(scenarios, page=0),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_scenario_"))
async def confirm_delete_scenario(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления"""
    scenario_id = int(callback.data.split("_")[-1])
    scenario = await db.get_scenario_by_id(scenario_id)
    
    if not scenario:
        await callback.answer("❌ Сценарий не найден", show_alert=True)
        return
    
    await state.update_data(deleting_scenario_id=scenario_id)
    await state.set_state(DeleteScenarioStates.confirming_deletion)
    
    await callback.message.edit_text(
        f"🗑 <b>Удаление сценария</b>\n\n"
        f"ID: {scenario_id}\n"
        f"Триггер: <code>{scenario['trigger_value']}</code>\n\n"
        f"⚠️ Вы уверены? Это действие нельзя отменить!",
        reply_markup=get_yes_no_keyboard(
            f"confirm_delete_{scenario_id}",
            "cancel_delete"
        ),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(DeleteScenarioStates.confirming_deletion, F.data.startswith("confirm_delete_"))
async def execute_delete_scenario(callback: CallbackQuery, state: FSMContext):
    """Выполнение удаления"""
    scenario_id = int(callback.data.split("_")[-1])
    
    await db.delete_scenario(scenario_id)
    
    await callback.message.edit_text(
        f"✅ Сценарий #{scenario_id} удалён!",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()
    await state.clear()


@router.callback_query(DeleteScenarioStates.confirming_deletion, F.data == "cancel_delete")
async def cancel_delete_scenario(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Удаление отменено",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


# ============================================================================
# НАСТРОЙКИ НАПОМИНАНИЙ
# ============================================================================

@router.callback_query(F.data == "admin_reminder_settings")
async def reminder_settings(callback: CallbackQuery):
    """Настройки напоминаний (заглушка для будущего функционала)"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки напоминаний</b>\n\n"
        "Здесь можно будет настроить:\n"
        "• Глобальное время напоминаний\n"
        "• Часовой пояс\n"
        "• Максимальное количество напоминаний\n\n"
        "🚧 В разработке...",
        reply_markup=get_back_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()
