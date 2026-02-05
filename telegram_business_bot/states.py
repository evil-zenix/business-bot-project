"""
FSM состояния для управления сценариями
"""
from aiogram.fsm.state import State, StatesGroup


class AddScenarioStates(StatesGroup):
    """Состояния для добавления сценария"""
    choosing_trigger_type = State()      # Выбор типа триггера
    entering_trigger_value = State()     # Ввод триггера
    entering_response_text = State()     # Ввод текста ответа
    asking_for_buttons = State()         # Нужны ли кнопки?
    entering_button_text = State()       # Ввод текста кнопки
    entering_button_callback = State()   # Ввод callback кнопки
    asking_for_more_buttons = State()    # Ещё кнопки?
    asking_for_reminder = State()        # Это напоминание?
    entering_reminder_delay = State()    # Ввод задержки напоминания
    confirming_scenario = State()        # Подтверждение сохранения


class EditScenarioStates(StatesGroup):
    """Состояния для редактирования сценария"""
    selecting_scenario = State()         # Выбор сценария для редактирования
    choosing_field = State()             # Выбор поля для редактирования
    entering_new_value = State()         # Ввод нового значения


class DeleteScenarioStates(StatesGroup):
    """Состояния для удаления сценария"""
    selecting_scenario = State()         # Выбор сценария для удаления
    confirming_deletion = State()        # Подтверждение удаления
