# -*- coding: utf-8 -*-
"""
TradLab Live Trading Bot
Автоматическая торговля с использованием STR-100
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import os
import time
import logging
from datetime import datetime
from typing import Optional
import pandas as pd
import psycopg2
from dotenv import load_dotenv

from tradlab.live.binance_connector import BinanceConnector
from tradlab.engine.strategies.str_100_chainflow_eth import STR100ChainFlowETH

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class LiveTradingBot:
    """
    Live Trading Bot для Binance Testnet
    """
    
    def __init__(self):
        """Инициализация бота"""
        # Загрузить конфигурацию
        load_dotenv()
        
        self.symbol = os.getenv('SYMBOL', 'ETHUSDT')
        self.timeframe = os.getenv('TIMEFRAME', '4h')
        self.initial_capital = float(os.getenv('INITIAL_CAPITAL', 10000))
        
        # Параметры стратегии
        self.strategy_params = {
            'master_long_threshold': float(os.getenv('MASTER_LONG_THRESHOLD', 12.0)),
            'master_short_threshold': float(os.getenv('MASTER_SHORT_THRESHOLD', -17.0)),
            'lookback_z': int(os.getenv('LOOKBACK_Z', 8)),
            'k_sl_min': float(os.getenv('K_SL_MIN', 2.2)),
            'k_sl_max': float(os.getenv('K_SL_MAX', 3.0)),
            'k_tp1': float(os.getenv('K_TP1', 2.0)),
            'k_tp2': float(os.getenv('K_TP2', 4.0)),
            'k_tsl': 1.0,
            'risk_per_trade': float(os.getenv('RISK_PER_TRADE', 0.01)),
            'max_position_pct': float(os.getenv('MAX_POSITION_PCT', 0.20)),
            'atr_expansion_multiplier': float(os.getenv('ATR_EXPANSION_MULTIPLIER', 2.0)),
            'volume_collapse_multiplier': float(os.getenv('VOLUME_COLLAPSE_MULTIPLIER', 0.3)),
            'commission_rate': float(os.getenv('COMMISSION_RATE', 0.0004)),
            'slippage_bps': int(os.getenv('SLIPPAGE_BPS', 5))
        }
        
        # Создать подключение к бирже
        self.exchange = BinanceConnector(
            api_key=os.getenv('API_KEY'),
            api_secret=os.getenv('API_SECRET'),
            testnet=os.getenv('TESTNET', 'true').lower() == 'true'
        )
        
        # Создать стратегию
        self.strategy = STR100ChainFlowETH(
            strategy_id="STR-100-LIVE",
            params=self.strategy_params
        )
        
        # Подключение к БД напрямую
        self.db_conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='tradlab_db',
            user='tradlab',
            password='crd12'
        )
        
        # Текущая позиция
        self.current_position = None
        
        logger.info("=" * 70)
        logger.info("LIVE TRADING BOT ИНИЦИАЛИЗИРОВАН")
        logger.info("=" * 70)
        logger.info(f"Символ: {self.symbol}")
        logger.info(f"Таймфрейм: {self.timeframe}")
        logger.info(f"Начальный капитал: ${self.initial_capital:,.2f}")
        logger.info(f"Параметры стратегии:")
        logger.info(f"  Long Threshold: {self.strategy_params['master_long_threshold']}")
        logger.info(f"  Short Threshold: {self.strategy_params['master_short_threshold']}")
        logger.info(f"  Lookback Z: {self.strategy_params['lookback_z']}")
        logger.info(f"  SL Min: {self.strategy_params['k_sl_min']}")
        logger.info("=" * 70)
    
    def get_latest_features(self) -> Optional[pd.Series]:
        """
        Получить последние фичи из БД
        
        Returns:
            Pandas Series с фичами или None
        """
        try:
            # Получить последнюю свечу из lab.features_v1
            query = f"""
            SELECT 
                symbol, ts_4h, open_4h, high_4h, low_4h, close_4h, volume_4h,
                close_1h, atr_14_1h, sma_50_4h, avg_volume_20
            FROM lab.features_v1
            WHERE symbol = '{self.symbol}'
            ORDER BY ts_4h DESC
            LIMIT 1
            """
            
            df = pd.read_sql(query, self.db_conn)
            
            if df.empty:
                logger.warning("⚠️ Нет данных в lab.features_v1")
                return None
            
            logger.info(f"✅ Загружены фичи: ts={df.iloc[0]['ts_4h']}, close={df.iloc[0]['close_4h']:.2f}")
            return df.iloc[0]
        
        except Exception as e:
            logger.error(f"❌ Ошибка получения фичей: {e}")
            return None
    
    def check_signal(self) -> Optional[dict]:
        """
        Проверить сигнал стратегии
        
        Returns:
            Словарь с сигналом или None
        """
        # Получить фичи
        features = self.get_latest_features()
        if features is None:
            return None
        
        # Получить текущий баланс
        balance = self.exchange.get_account_balance('USDT')
        
        # Генерация сигнала
        signal = self.strategy.generate_signal(features, balance)
        
        if signal:
            logger.info(f"🔔 СИГНАЛ: {signal.side} @ {signal.entry_price:.2f}")
            logger.info(f"   SL: {signal.stop_loss:.2f}, TP1: {signal.take_profit_1:.2f}")
            logger.info(f"   Размер позиции: {signal.position_size:.4f} ETH")
        else:
            logger.info("⏸️ Нет сигнала (условия не выполнены)")
        
        return signal
    
    def execute_trade(self, signal: dict):
        """
        Исполнить трейд на бирже
        
        Args:
            signal: Сигнал от стратегии
        """
        try:
            side = 'BUY' if signal.side == 'LONG' else 'SELL'
            quantity = round(signal.position_size, 3)  # Binance требует округление
            
            # Разместить рыночный ордер
            order = self.exchange.place_market_order(
                symbol=self.symbol,
                side=side,
                quantity=quantity
            )
            
            if order:
                self.current_position = {
                    'side': signal.side,
                    'entry_price': signal.entry_price,
                    'quantity': quantity,
                    'stop_loss': signal.stop_loss,
                    'take_profit_1': signal.take_profit_1,
                    'take_profit_2': signal.take_profit_2,
                    'order_id': order['orderId'],
                    'timestamp': datetime.now()
                }
                
                logger.info(f"✅ Позиция открыта: {signal.side} {quantity} {self.symbol}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка исполнения трейда: {e}")
    
    def check_position_management(self):
        """
        Управление открытой позицией (SL/TP)
        """
        if not self.current_position:
            return
        
        # Получить текущую цену
        current_price = self.exchange.get_current_price(self.symbol)
        if not current_price:
            return
        
        side = self.current_position['side']
        entry = self.current_position['entry_price']
        sl = self.current_position['stop_loss']
        tp1 = self.current_position['take_profit_1']
        
        # Проверка SL
        if side == 'LONG' and current_price <= sl:
            logger.warning(f"⚠️ STOP LOSS HIT! Цена: {current_price:.2f}, SL: {sl:.2f}")
            self.close_position("STOP LOSS")
            return
        
        if side == 'SHORT' and current_price >= sl:
            logger.warning(f"⚠️ STOP LOSS HIT! Цена: {current_price:.2f}, SL: {sl:.2f}")
            self.close_position("STOP LOSS")
            return
        
        # Проверка TP1
        if side == 'LONG' and current_price >= tp1:
            logger.info(f"🎯 TAKE PROFIT 1! Цена: {current_price:.2f}, TP1: {tp1:.2f}")
            self.close_position("TAKE PROFIT 1", partial=0.5)
            return
        
        if side == 'SHORT' and current_price <= tp1:
            logger.info(f"🎯 TAKE PROFIT 1! Цена: {current_price:.2f}, TP1: {tp1:.2f}")
            self.close_position("TAKE PROFIT 1", partial=0.5)
            return
    
    def close_position(self, reason: str, partial: float = 1.0):
        """
        Закрыть позицию
        
        Args:
            reason: Причина закрытия
            partial: Доля закрытия (1.0 = полностью, 0.5 = половина)
        """
        if not self.current_position:
            return
        
        try:
            side = 'SELL' if self.current_position['side'] == 'LONG' else 'BUY'
            quantity = round(self.current_position['quantity'] * partial, 3)
            
            order = self.exchange.place_market_order(
                symbol=self.symbol,
                side=side,
                quantity=quantity
            )
            
            if order:
                logger.info(f"✅ Позиция закрыта ({reason}): {side} {quantity} {self.symbol}")
                
                if partial >= 1.0:
                    self.current_position = None
                else:
                    self.current_position['quantity'] *= (1.0 - partial)
        
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия позиции: {e}")
    
    def run(self, check_interval: int = 300):
        """
        Запустить бота
        
        Args:
            check_interval: Интервал проверки в секундах (300 = 5 минут)
        """
        logger.info("🚀 БОТ ЗАПУЩЕН!")
        logger.info(f"Проверка сигналов каждые {check_interval} секунд")
        logger.info("Нажми Ctrl+C для остановки")
        logger.info("=" * 70)
        
        try:
            while True:
                # Проверка текущей позиции
                self.check_position_management()
                
                # Если нет открытой позиции - проверить сигнал
                if not self.current_position:
                    signal = self.check_signal()
                    if signal:
                        # РЕЖИМ ТЕСТИРОВАНИЯ: только логирование
                        logger.info("📋 [ТЕСТ] Сигнал получен, но не исполнен (тестовый режим)")
                        # Раскомментируй для реальной торговли:
                        # self.execute_trade(signal)
                
                # Статус
                balance = self.exchange.get_account_balance('USDT')
                price = self.exchange.get_current_price(self.symbol)
                position_status = f"ПОЗИЦИЯ: {self.current_position['side']}" if self.current_position else "НЕТ ПОЗИЦИИ"
                
                logger.info(f"💰 Баланс: ${balance:,.2f} | Цена ETH: ${price:,.2f} | {position_status}")
                logger.info(f"⏳ Следующая проверка через {check_interval} сек...")
                
                # Ожидание
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Остановка бота...")
            if self.current_position:
                logger.warning("⚠️ Есть открытая позиция! Закрой её вручную на бирже.")
            logger.info("Бот остановлен.")
        
        finally:
            # Закрыть подключение к БД
            if hasattr(self, 'db_conn'):
                self.db_conn.close()


def main():
    """Точка входа"""
    bot = LiveTradingBot()
    bot.run(check_interval=300)  # Проверка каждые 5 минут


if __name__ == "__main__":
    main()