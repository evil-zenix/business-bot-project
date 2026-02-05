"""
Работа с базой данных SQLite
"""
import aiosqlite
import logging
from typing import List, Dict, Optional
from config import DB_PATH

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица сценариев
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger_type TEXT NOT NULL,
                    trigger_value TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    keyboard_json TEXT,
                    is_reminder INTEGER DEFAULT 0,
                    reminder_delay_min INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица для хранения business_connection_id
            await db.execute("""
                CREATE TABLE IF NOT EXISTS business_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_connection_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    can_reply INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица для истории отправленных напоминаний
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reminder_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id INTEGER,
                    chat_id INTEGER,
                    business_connection_id TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
                )
            """)
            
            await db.commit()
            logger.info("База данных инициализирована")
    
    async def add_scenario(
        self,
        trigger_type: str,
        trigger_value: str,
        response_text: str,
        keyboard_json: Optional[str] = None,
        is_reminder: bool = False,
        reminder_delay_min: int = 0
    ) -> int:
        """Добавить новый сценарий"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO scenarios 
                (trigger_type, trigger_value, response_text, keyboard_json, is_reminder, reminder_delay_min)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (trigger_type, trigger_value, response_text, keyboard_json, 
                  1 if is_reminder else 0, reminder_delay_min))
            await db.commit()
            logger.info(f"Добавлен сценарий ID={cursor.lastrowid}, trigger={trigger_value}")
            return cursor.lastrowid
    
    async def get_all_scenarios(self, active_only: bool = False) -> List[Dict]:
        """Получить все сценарии"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM scenarios"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY created_at DESC"
            
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_scenario_by_id(self, scenario_id: int) -> Optional[Dict]:
        """Получить сценарий по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM scenarios WHERE id = ?", (scenario_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_scenario(
        self,
        scenario_id: int,
        trigger_type: Optional[str] = None,
        trigger_value: Optional[str] = None,
        response_text: Optional[str] = None,
        keyboard_json: Optional[str] = None,
        is_reminder: Optional[bool] = None,
        reminder_delay_min: Optional[int] = None
    ) -> bool:
        """Обновить сценарий"""
        # Формируем запрос динамически
        updates = []
        values = []
        
        if trigger_type is not None:
            updates.append("trigger_type = ?")
            values.append(trigger_type)
        if trigger_value is not None:
            updates.append("trigger_value = ?")
            values.append(trigger_value)
        if response_text is not None:
            updates.append("response_text = ?")
            values.append(response_text)
        if keyboard_json is not None:
            updates.append("keyboard_json = ?")
            values.append(keyboard_json)
        if is_reminder is not None:
            updates.append("is_reminder = ?")
            values.append(1 if is_reminder else 0)
        if reminder_delay_min is not None:
            updates.append("reminder_delay_min = ?")
            values.append(reminder_delay_min)
        
        if not updates:
            return False
        
        values.append(scenario_id)
        query = f"UPDATE scenarios SET {', '.join(updates)} WHERE id = ?"
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, values)
            await db.commit()
            logger.info(f"Сценарий ID={scenario_id} обновлён")
            return True
    
    async def delete_scenario(self, scenario_id: int) -> bool:
        """Удалить сценарий"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
            await db.commit()
            logger.info(f"Сценарий ID={scenario_id} удалён")
            return True
    
    async def toggle_scenario_active(self, scenario_id: int) -> bool:
        """Переключить активность сценария"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE scenarios 
                SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END 
                WHERE id = ?
            """, (scenario_id,))
            await db.commit()
            logger.info(f"Переключена активность сценария ID={scenario_id}")
            return True
    
    async def find_matching_scenario(
        self,
        message_text: str,
        callback_data: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Найти подходящий сценарий по тексту сообщения или callback
        
        Args:
            message_text: Текст сообщения от клиента
            callback_data: Callback data от нажатия кнопки
        
        Returns:
            Первый подходящий активный сценарий или None
        """
        scenarios = await self.get_all_scenarios(active_only=True)
        
        for scenario in scenarios:
            trigger_type = scenario['trigger_type']
            trigger_value = scenario['trigger_value'].lower()
            
            # Обработка callback триггеров
            if trigger_type == 'callback' and callback_data:
                if callback_data == trigger_value:
                    return scenario
            
            # Обработка текстовых триггеров
            elif message_text and trigger_type in ['exact', 'contains']:
                message_lower = message_text.lower().strip()
                
                if trigger_type == 'exact':
                    if message_lower == trigger_value:
                        return scenario
                
                elif trigger_type == 'contains':
                    if trigger_value in message_lower:
                        return scenario
        
        return None
    
    async def save_business_connection(
        self,
        business_connection_id: str,
        user_id: Optional[int] = None,
        can_reply: bool = True
    ):
        """Сохранить business connection"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO business_connections 
                (business_connection_id, user_id, can_reply)
                VALUES (?, ?, ?)
            """, (business_connection_id, user_id, 1 if can_reply else 0))
            await db.commit()
            logger.info(f"Business connection сохранён: {business_connection_id}")
    
    async def get_business_connection(self, business_connection_id: str) -> Optional[Dict]:
        """Получить данные business connection"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM business_connections WHERE business_connection_id = ?",
                (business_connection_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def add_reminder_history(
        self,
        scenario_id: int,
        chat_id: int,
        business_connection_id: str
    ):
        """Добавить запись об отправленном напоминании"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO reminder_history (scenario_id, chat_id, business_connection_id)
                VALUES (?, ?, ?)
            """, (scenario_id, chat_id, business_connection_id))
            await db.commit()


# Глобальный экземпляр базы данных
db = Database()
