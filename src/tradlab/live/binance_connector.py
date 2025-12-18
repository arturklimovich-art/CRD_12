# -*- coding: utf-8 -*-
"""
Binance Connector для Live Trading
"""
import os
import time
from decimal import Decimal
from typing import Optional, Dict, List
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinanceConnector:
    """
    Подключение к Binance Testnet для live торговли
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Args:
            api_key: API ключ
            api_secret: Secret ключ
            testnet: Использовать testnet (True) или mainnet (False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Создать клиент с timeout
        if testnet:
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret,
                testnet=True,
                requests_params={
                    'timeout': 10,
                    'verify': True
                }
            )
            logger.info("✅ Подключено к Binance TESTNET")
        else:
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret,
                requests_params={
                    'timeout': 10,
                    'verify': True
                }
            )
            logger.info("⚠️ Подключено к Binance MAINNET (РЕАЛЬНЫЕ ДЕНЬГИ!)")
    
    def get_account_balance(self, asset: str = 'USDT') -> float:
        """
        Получить баланс счета
        
        Args:
            asset: Актив (например, USDT)
        
        Returns:
            Доступный баланс
        """
        try:
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except Exception as e:
            logger.error(f"❌ Ошибка получения баланса: {e}")
            return 0.0
    
    def get_current_price(self, symbol: str = 'ETHUSDT') -> Optional[float]:
        """
        Получить текущую цену
        
        Args:
            symbol: Торговая пара
        
        Returns:
            Текущая цена или None
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"❌ Ошибка получения цены: {e}")
            return None
    
    def get_klines(self, symbol: str = 'ETHUSDT', interval: str = '4h', limit: int = 100) -> List[Dict]:
        """
        Получить исторические свечи
        
        Args:
            symbol: Торговая пара
            interval: Таймфрейм (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Количество свечей
        
        Returns:
            Список свечей
        """
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            result = []
            for k in klines:
                result.append({
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            
            return result
        except BinanceAPIException as e:
            logger.error(f"❌ Ошибка получения свечей: {e}")
            return []
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict]:
        """
        Разместить рыночный ордер с retry логикой
        
        Args:
            symbol: Торговая пара (ETHUSDT)
            side: BUY или SELL
            quantity: Количество (в ETH)
        
        Returns:
            Информация о сделке или None
        """
        for attempt in range(self.max_retries):
            try:
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity
                )
                
                logger.info(f"✅ Ордер размещен: {side} {quantity} {symbol}")
                logger.info(f"   Order ID: {order['orderId']}")
                logger.info(f"   Status: {order['status']}")
                
                return order
                
            except Exception as e:
                # Check if timeout
                if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)
                        logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Max retries exceeded for order placement")
                        raise
                else:
                    logger.error(f"❌ Ошибка размещения ордера: {e}")
                    raise
        
        return None
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Optional[Dict]:
        """
        Разместить лимитный ордер
        
        Args:
            symbol: Торговая пара
            side: BUY или SELL
            quantity: Количество
            price: Цена
        
        Returns:
            Информация о сделке или None
        """
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            
            logger.info(f"✅ Лимитный ордер размещен: {side} {quantity} @ {price}")
            return order
        except BinanceAPIException as e:
            logger.error(f"❌ Ошибка размещения лимитного ордера: {e}")
            return None
    
    def get_open_orders(self, symbol: str = 'ETHUSDT') -> List[Dict]:
        """
        Получить список открытых ордеров
        
        Args:
            symbol: Торговая пара
        
        Returns:
            Список открытых ордеров
        """
        try:
            orders = self.client.get_open_orders(symbol=symbol)
            return orders
        except BinanceAPIException as e:
            logger.error(f"❌ Ошибка получения открытых ордеров: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Отменить ордер
        
        Args:
            symbol: Торговая пара
            order_id: ID ордера
        
        Returns:
            True если успешно
        """
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"✅ Ордер {order_id} отменен")
            return True
        except BinanceAPIException as e:
            logger.error(f"❌ Ошибка отмены ордера: {e}")
            return False
    
    def get_symbol_info(self, symbol: str = 'ETHUSDT') -> Optional[Dict]:
        """
        Получить информацию о символе (минимальный размер позиции и т.д.)
        
        Args:
            symbol: Торговая пара
        
        Returns:
            Информация о символе
        """
        try:
            info = self.client.get_symbol_info(symbol)
            return info
        except BinanceAPIException as e:
            logger.error(f"❌ Ошибка получения информации о символе: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Проверить подключение к API
        
        Returns:
            True если подключение работает
        """
        try:
            status = self.client.get_system_status()
            server_time = self.client.get_server_time()
            
            logger.info("=" * 60)
            logger.info("ТЕСТ ПОДКЛЮЧЕНИЯ К BINANCE")
            logger.info("=" * 60)
            logger.info(f"Статус: {status['msg']}")
            logger.info(f"Серверное время: {server_time['serverTime']}")
            
            # Баланс
            balance = self.get_account_balance('USDT')
            logger.info(f"Баланс USDT: ${balance:,.2f}")
            
            # Текущая цена
            price = self.get_current_price('ETHUSDT')
            logger.info(f"Цена ETH: ${price:,.2f}")
            
            logger.info("=" * 60)
            logger.info("✅ ПОДКЛЮЧЕНИЕ УСПЕШНО!")
            logger.info("=" * 60)
            
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return False