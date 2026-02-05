#!/usr/bin/env python3
"""
Скрипт проверки окружения для Telegram Business бота
Проверяет: Python, зависимости, .env файл, права доступа
"""

import sys
import os
from pathlib import Path

def print_status(message: str, status: bool):
    """Вывод статуса проверки"""
    icon = "✅" if status else "❌"
    print(f"{icon} {message}")
    return status

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    required = (3, 9)
    
    if version >= required:
        print_status(
            f"Python {version.major}.{version.minor}.{version.micro} (требуется >= {required[0]}.{required[1]})",
            True
        )
        return True
    else:
        print_status(
            f"Python {version.major}.{version.minor} - УСТАРЕЛ! Требуется >= {required[0]}.{required[1]}",
            False
        )
        return False

def check_dependencies():
    """Проверка установленных зависимостей"""
    dependencies = {
        'aiogram': 'aiogram',
        'apscheduler': 'APScheduler',
        'aiosqlite': 'aiosqlite',
        'dotenv': 'python-dotenv'
    }
    
    all_installed = True
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print_status(f"{name} установлен", True)
        except ImportError:
            print_status(f"{name} НЕ установлен", False)
            all_installed = False
    
    return all_installed

def check_env_file():
    """Проверка .env файла"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print_status(".env файл НЕ найден", False)
        print("   💡 Создайте .env файл: cp .env.example .env")
        return False
    
    print_status(".env файл найден", True)
    
    # Проверка содержимого
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        has_token = 'BOT_TOKEN=' in content and 'your_bot_token' not in content
        has_admins = 'ADMIN_IDS=' in content and content.count('ADMIN_IDS=') > 0
        
        if has_token:
            print_status("  BOT_TOKEN настроен", True)
        else:
            print_status("  BOT_TOKEN НЕ настроен", False)
            return False
        
        if has_admins:
            # Проверяем, что ID не пустой
            admin_line = [line for line in content.split('\n') if 'ADMIN_IDS=' in line][0]
            admin_value = admin_line.split('=', 1)[1].strip()
            if admin_value:
                print_status("  ADMIN_IDS настроен", True)
            else:
                print_status("  ADMIN_IDS пустой", False)
                return False
        else:
            print_status("  ADMIN_IDS НЕ настроен", False)
            return False
        
        return has_token and has_admins
    
    except Exception as e:
        print_status(f"Ошибка чтения .env: {e}", False)
        return False

def check_file_structure():
    """Проверка структуры файлов"""
    required_files = [
        'main.py',
        'config.py',
        'db.py',
        'states.py',
        'keyboards.py',
        'handlers/__init__.py',
        'handlers/admin.py',
        'handlers/business.py'
    ]
    
    all_exist = True
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print_status(f"  {file_path}", True)
        else:
            print_status(f"  {file_path} НЕ найден", False)
            all_exist = False
    
    return all_exist

def check_database():
    """Проверка базы данных"""
    db_path = Path('scenarios.db')
    
    if db_path.exists():
        size = db_path.stat().st_size
        print_status(f"База данных найдена ({size} байт)", True)
        return True
    else:
        print_status("База данных будет создана при первом запуске", True)
        return True

def main():
    """Основная функция"""
    print("🔍 Проверка окружения Telegram Business бота\n")
    
    print("=" * 50)
    print("1. Проверка Python")
    print("=" * 50)
    python_ok = check_python_version()
    print()
    
    print("=" * 50)
    print("2. Проверка зависимостей")
    print("=" * 50)
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n💡 Установите зависимости: pip install -r requirements.txt")
    print()
    
    print("=" * 50)
    print("3. Проверка конфигурации")
    print("=" * 50)
    env_ok = check_env_file()
    print()
    
    print("=" * 50)
    print("4. Проверка файлов проекта")
    print("=" * 50)
    files_ok = check_file_structure()
    print()
    
    print("=" * 50)
    print("5. Проверка базы данных")
    print("=" * 50)
    db_ok = check_database()
    print()
    
    # Итоговый результат
    print("=" * 50)
    print("📊 ИТОГО")
    print("=" * 50)
    
    all_checks = [python_ok, deps_ok, env_ok, files_ok, db_ok]
    passed = sum(all_checks)
    total = len(all_checks)
    
    if all(all_checks):
        print(f"\n✅ Всё отлично! ({passed}/{total} проверок пройдено)")
        print("\n🚀 Можно запускать бота: python main.py")
        return 0
    else:
        print(f"\n⚠️  Есть проблемы ({passed}/{total} проверок пройдено)")
        print("\n📚 Смотрите:")
        print("   - SETUP.md - Подробная инструкция")
        print("   - QUICKSTART.md - Быстрый старт")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
