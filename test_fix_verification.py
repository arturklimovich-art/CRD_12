# test_fix_verification.py
import sys
import os
sys.path.insert(0, '/app')

# Импортируем необходимые функции
from app import _get_target_filepath
import logging

logging.basicConfig(level=logging.INFO)

def test_target_file_none_scenario():
    print("=== ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ target_file = None ===")
    
    # Тест 1: Задача без указания файла
    task1 = "Create a function for data processing"
    target1 = _get_target_filepath(task1)
    print(f"Тест 1 - Задача без файла: '{task1}'")
    print(f"Результат _get_target_filepath: {target1}")
    
    # Тест 2: Задача с указанием файла
    task2 = "Modify app.py to add new feature"
    target2 = _get_target_filepath(task2)
    print(f"Тест 2 - Задача с файлом: '{task2}'")
    print(f"Результат _get_target_filepath: {target2}")
    
    # Тест 3: Задача с русским текстом
    task3 = "Изменить обработчик в controller.py"
    target3 = _get_target_filepath(task3)
    print(f"Тест 3 - Задача на русском: '{task3}'")
    print(f"Результат _get_target_filepath: {target3}")
    
    print("\n=== РЕЗУЛЬТАТЫ ===")
    if target1 is None and target2 is not None:
        print("✅ ИСПРАВЛЕНИЕ РАБОТАЕТ: target_file = None когда файл не указан")
    else:
        print("❌ ПРОБЛЕМА: Логика определения файла работает некорректно")

if __name__ == "__main__":
    test_target_file_none_scenario()
