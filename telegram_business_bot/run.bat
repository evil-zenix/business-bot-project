@echo off
chcp 65001 >nul
echo 🚀 Запуск Telegram Business бота...
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден. Установите Python 3.9 или выше.
    pause
    exit /b 1
)

REM Проверка наличия .env файла
if not exist .env (
    echo ⚠️  Файл .env не найден!
    echo Создайте файл .env на основе .env.example
    echo.
    echo Пример:
    echo   copy .env.example .env
    echo   notepad .env
    pause
    exit /b 1
)

REM Проверка зависимостей
echo 📦 Проверка зависимостей...
python -c "import aiogram" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Зависимости не установлены!
    echo Устанавливаем зависимости...
    pip install -r requirements.txt
)

REM Запуск бота
echo ✅ Всё готово! Запускаем бота...
echo.
python main.py
pause
