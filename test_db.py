# test_db.py
import os
import sys
# Добавляем корневую папку в путь для импорта config и database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import engine, Base, Task
    from config import DATABASE_URL
    
    # Пытаемся создать все таблицы
    Base.metadata.create_all(engine)
    
    print(f"✅ Успешно: Подключение к БД {DATABASE_URL} успешно. Файл tasks.db создан или обновлен.")
    
except ImportError as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не найден модуль: {e}. Проверьте структуру папок и `pip install`.")
except Exception as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА БД: {e}. Проверьте `database.py` и `config.py`.")