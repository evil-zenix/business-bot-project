"""
Главный файл Telegram Business бота
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, LOG_LEVEL
from db import db
from handlers import admin, business

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup():
    """Действия при запуске бота"""
    logger.info("Инициализация базы данных...")
    await db.init_db()
    logger.info("База данных готова")
    
    # Добавляем дефолтный сценарий если БД пустая
    scenarios = await db.get_all_scenarios()
    if not scenarios:
        logger.info("Добавление примера сценария...")
        await db.add_scenario(
            trigger_type='contains',
            trigger_value='расписание',
            response_text=(
                "📅 <b>Наше расписание:</b>\n\n"
                "Понедельник - Пятница: 9:00 - 18:00\n"
                "Суббота: 10:00 - 16:00\n"
                "Воскресенье: выходной\n\n"
                "Нажмите кнопку ниже для подробной информации:"
            ),
            keyboard_json='[{"text":"📋 Полное расписание","callback_data":"schedule_full"}]',
            is_reminder=False,
            reminder_delay_min=0
        )
        
        await db.add_scenario(
            trigger_type='callback',
            trigger_value='schedule_full',
            response_text=(
                "📋 <b>Подробное расписание:</b>\n\n"
                "<b>Понедельник - Четверг:</b>\n"
                "9:00-13:00 - Консультации\n"
                "14:00-18:00 - Процедуры\n\n"
                "<b>Пятница:</b>\n"
                "9:00-17:00 - Работа с клиентами\n\n"
                "<b>Суббота:</b>\n"
                "10:00-16:00 - По записи\n\n"
                "Для записи свяжитесь с нами!"
            ),
            keyboard_json=None,
            is_reminder=False,
            reminder_delay_min=0
        )
        logger.info("Примеры сценариев добавлены")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Бот остановлен")


async def main():
    """Главная функция"""
    # Создаём бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создаём диспетчер
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(admin.router)
    dp.include_router(business.router)
    
    # Инициализируем scheduler для напоминаний
    scheduler = AsyncIOScheduler()
    scheduler.start()
    logger.info("Scheduler запущен")
    
    # Передаём scheduler в business обработчик
    business.set_scheduler(scheduler)
    
    # Регистрируем startup хук
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запускаем polling
    logger.info("Бот запущен")
    logger.info("Для доступа к админ-панели отправьте /admin")
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "callback_query",
                "business_connection",
                "business_message",
                "edited_business_message",
                "deleted_business_messages"
            ]
        )
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")
