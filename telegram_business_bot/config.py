"""
Конфигурация бота
"""
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# ID администраторов (через запятую в .env)
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id_.strip()) for id_ in ADMIN_IDS_STR.split(',') if id_.strip()]

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS не найден в .env файле!")

# Путь к базе данных
DB_PATH = 'scenarios.db'

# Настройки логирования
LOG_LEVEL = 'INFO'
