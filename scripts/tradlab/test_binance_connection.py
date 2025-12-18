# -*- coding: utf-8 -*-
"""
Тест подключения к Binance Testnet
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import os
from dotenv import load_dotenv
from tradlab.live.binance_connector import BinanceConnector

# Загрузить переменные из .env
load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
TESTNET = os.getenv('TESTNET', 'true').lower() == 'true'

if not API_KEY or not API_SECRET:
    print("❌ ОШИБКА: API_KEY или API_SECRET не найдены в .env файле!")
    print("   Проверь что .env файл существует и содержит ключи.")
    sys.exit(1)

# Создать подключение
connector = BinanceConnector(
    api_key=API_KEY,
    api_secret=API_SECRET,
    testnet=TESTNET
)

# Тест подключения
if connector.test_connection():
    print("\n✅ Готово к торговле!")
else:
    print("\n❌ Подключение не удалось. Проверь API ключи.")