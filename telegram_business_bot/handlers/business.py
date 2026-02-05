"""
Обработчики для Telegram Business сообщений
"""
import logging
from datetime import datetime, timedelta
from aiogram import Router, Bot, F
from aiogram.types import BusinessMessagesDeleted, Message, CallbackQuery, BusinessConnection
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import db
from keyboards import create_inline_keyboard_from_json

logger = logging.getLogger(__name__)
router = Router()

# Глобальный scheduler (будет инициализирован в main.py)
scheduler: AsyncIOScheduler = None


def set_scheduler(sched: AsyncIOScheduler):
    """Установить scheduler для напоминаний"""
    global scheduler
    scheduler = sched


async def send_reminder(
    bot: Bot,
    chat_id: int,
    text: str,
    business_connection_id: str,
    scenario_id: int,
    keyboard_json: str = None
):
    """
    Отправка напоминания клиенту
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата клиента
        text: Текст напоминания
        business_connection_id: ID бизнес-подключения
        scenario_id: ID сценария
        keyboard_json: JSON клавиатуры (опционально)
    """
    try:
        keyboard = create_inline_keyboard_from_json(keyboard_json) if keyboard_json else None
        
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            business_connection_id=business_connection_id,
            reply_markup=keyboard
        )
        
        # Сохраняем в историю
        await db.add_reminder_history(scenario_id, chat_id, business_connection_id)
        
        logger.info(f"Напоминание отправлено: chat_id={chat_id}, scenario_id={scenario_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания: {e}")


@router.business_connection()
async def on_business_connection(event: BusinessConnection):
    """
    Обработка подключения/отключения бизнес-аккаунта
    """
    logger.info(f"Business connection: {event.id}, user_id={event.user.id}, can_reply={event.can_reply}")
    
    # Сохраняем информацию о подключении
    await db.save_business_connection(
        business_connection_id=event.id,
        user_id=event.user.id,
        can_reply=event.can_reply
    )


@router.business_message(F.text)
async def handle_business_message(message: Message, bot: Bot):
    """
    Обработка входящих сообщений от клиентов через Business
    
    Args:
        message: Сообщение от клиента
        bot: Экземпляр бота
    """
    # Проверяем наличие business_connection_id
    if not message.business_connection_id:
        logger.warning("Получено сообщение без business_connection_id")
        return
    
    business_connection_id = message.business_connection_id
    chat_id = message.chat.id
    message_text = message.text
    
    logger.info(f"Бизнес-сообщение от {chat_id}: {message_text}")
    
    # Ищем подходящий сценарий
    scenario = await db.find_matching_scenario(message_text=message_text)
    
    if not scenario:
        logger.info("Подходящий сценарий не найден, пропускаем")
        return
    
    logger.info(f"Найден сценарий ID={scenario['id']}, отправляем ответ")
    
    try:
        # Создаём клавиатуру если есть
        keyboard = create_inline_keyboard_from_json(scenario['keyboard_json']) if scenario['keyboard_json'] else None
        
        # Отправляем ответ от имени бизнес-аккаунта
        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=scenario['response_text'],
            business_connection_id=business_connection_id,
            reply_markup=keyboard,
            parse_mode='HTML'  # Поддержка HTML форматирования
        )
        
        logger.info(f"Ответ отправлен успешно: message_id={sent_message.message_id}")
        
        # Отмечаем сообщение как прочитанное (если возможно)
        try:
            await bot.read_business_message(
                business_connection_id=business_connection_id,
                chat_id=chat_id
            )
        except Exception as e:
            logger.debug(f"Не удалось отметить как прочитанное: {e}")
        
        # Если это сценарий с напоминанием - планируем отправку
        if scenario['is_reminder'] and scenario['reminder_delay_min'] > 0:
            delay_minutes = scenario['reminder_delay_min']
            run_time = datetime.now() + timedelta(minutes=delay_minutes)
            
            if scheduler:
                scheduler.add_job(
                    send_reminder,
                    'date',
                    run_date=run_time,
                    args=[
                        bot,
                        chat_id,
                        scenario['response_text'],
                        business_connection_id,
                        scenario['id'],
                        scenario['keyboard_json']
                    ],
                    id=f"reminder_{scenario['id']}_{chat_id}_{datetime.now().timestamp()}",
                    replace_existing=False
                )
                logger.info(f"Запланировано напоминание через {delay_minutes} мин")
            else:
                logger.warning("Scheduler не инициализирован, напоминание не запланировано")
    
    except Exception as e:
        logger.error(f"Ошибка отправки ответа: {e}", exc_info=True)


@router.callback_query(F.data.startswith("scenario_"))
async def handle_scenario_callback(callback: CallbackQuery, bot: Bot):
    """
    Обработка callback от кнопок в ответах клиентам
    
    Например, клиент нажал кнопку "Расписание" с callback_data="scenario_schedule"
    """
    # Извлекаем callback_data (убираем префикс "scenario_" если он есть для пользовательских кнопок)
    callback_data = callback.data
    
    # Проверяем, есть ли business_connection_id
    if not callback.message or not hasattr(callback.message, 'business_connection_id'):
        await callback.answer("Ошибка: не найден business_connection_id")
        return
    
    business_connection_id = callback.message.business_connection_id
    chat_id = callback.message.chat.id
    
    logger.info(f"Callback от клиента {chat_id}: {callback_data}")
    
    # Ищем сценарий по callback
    scenario = await db.find_matching_scenario(message_text=None, callback_data=callback_data)
    
    if not scenario:
        await callback.answer("Сценарий не найден")
        return
    
    try:
        # Создаём клавиатуру если есть
        keyboard = create_inline_keyboard_from_json(scenario['keyboard_json']) if scenario['keyboard_json'] else None
        
        # Отправляем новое сообщение (или можно отредактировать текущее)
        await bot.send_message(
            chat_id=chat_id,
            text=scenario['response_text'],
            business_connection_id=business_connection_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await callback.answer("✅")
        logger.info(f"Ответ на callback отправлен")
        
        # Если это напоминание - планируем
        if scenario['is_reminder'] and scenario['reminder_delay_min'] > 0:
            delay_minutes = scenario['reminder_delay_min']
            run_time = datetime.now() + timedelta(minutes=delay_minutes)
            
            if scheduler:
                scheduler.add_job(
                    send_reminder,
                    'date',
                    run_date=run_time,
                    args=[
                        bot,
                        chat_id,
                        scenario['response_text'],
                        business_connection_id,
                        scenario['id'],
                        scenario['keyboard_json']
                    ],
                    id=f"reminder_{scenario['id']}_{chat_id}_{datetime.now().timestamp()}",
                    replace_existing=False
                )
                logger.info(f"Запланировано напоминание через {delay_minutes} мин")
    
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}", exc_info=True)
        await callback.answer("Ошибка обработки")


@router.edited_business_message()
async def handle_edited_business_message(message: Message):
    """Обработка отредактированных бизнес-сообщений"""
    logger.info(f"Отредактировано сообщение от {message.chat.id}: {message.text}")
    # Можно добавить логику, если нужно реагировать на редактирование


@router.deleted_business_messages()
async def handle_deleted_business_messages(event: BusinessMessagesDeleted):
    """Обработка удалённых бизнес-сообщений"""
    logger.info(f"Удалены сообщения: {event.message_ids}")
    # Можно добавить логику очистки
