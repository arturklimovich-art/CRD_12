"""
Unit tests for Binance Connector
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from tradlab.live.binance_connector import BinanceConnector


@pytest.fixture
def mock_client():
    """Create a mock Binance client"""
    client = Mock()
    client.get_account.return_value = {
        'balances': [
            {'asset': 'USDT', 'free': '10000.0', 'locked': '0.0'},
            {'asset': 'ETH', 'free': '5.0', 'locked': '0.0'}
        ]
    }
    client.get_symbol_ticker.return_value = {'price': '2000.0'}
    client.get_system_status.return_value = {'msg': 'normal'}
    client.get_server_time.return_value = {'serverTime': 1234567890}
    return client


class TestBinanceConnectorInitialization:
    """Test Binance connector initialization"""
    
    @patch('tradlab.live.binance_connector.Client')
    def test_initialization_testnet(self, mock_client_class):
        """Test initialization with testnet"""
        connector = BinanceConnector(
            api_key='test_key',
            api_secret='test_secret',
            testnet=True
        )
        
        assert connector.testnet == True
        assert connector.max_retries == 3
        assert connector.retry_delay == 1
        
        # Verify Client was called with correct params
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs['testnet'] == True
        assert call_kwargs['requests_params']['timeout'] == 10
        assert call_kwargs['requests_params']['verify'] == True
    
    @patch('tradlab.live.binance_connector.Client')
    def test_initialization_mainnet(self, mock_client_class):
        """Test initialization with mainnet"""
        connector = BinanceConnector(
            api_key='test_key',
            api_secret='test_secret',
            testnet=False
        )
        
        assert connector.testnet == False
        
        # Verify Client was called with correct params
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert 'testnet' not in call_kwargs or call_kwargs.get('testnet') == False
        assert call_kwargs['requests_params']['timeout'] == 10


class TestBinanceConnectorMethods:
    """Test Binance connector methods"""
    
    @patch('tradlab.live.binance_connector.Client')
    def test_get_account_balance(self, mock_client_class):
        """Test getting account balance"""
        mock_client = Mock()
        mock_client.get_account.return_value = {
            'balances': [
                {'asset': 'USDT', 'free': '10000.0', 'locked': '0.0'},
                {'asset': 'ETH', 'free': '5.0', 'locked': '0.0'}
            ]
        }
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        balance = connector.get_account_balance('USDT')
        
        assert balance == 10000.0
    
    @patch('tradlab.live.binance_connector.Client')
    def test_get_account_balance_missing_asset(self, mock_client_class):
        """Test getting balance for missing asset"""
        mock_client = Mock()
        mock_client.get_account.return_value = {
            'balances': [
                {'asset': 'USDT', 'free': '10000.0', 'locked': '0.0'}
            ]
        }
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        balance = connector.get_account_balance('BTC')
        
        assert balance == 0.0
    
    @patch('tradlab.live.binance_connector.Client')
    def test_get_current_price(self, mock_client_class):
        """Test getting current price"""
        mock_client = Mock()
        mock_client.get_symbol_ticker.return_value = {'price': '2000.50'}
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        price = connector.get_current_price('ETHUSDT')
        
        assert price == 2000.50


class TestBinanceConnectorRetryLogic:
    """Test retry logic for API calls"""
    
    @patch('tradlab.live.binance_connector.Client')
    @patch('tradlab.live.binance_connector.time.sleep')
    def test_place_market_order_timeout_retry(self, mock_sleep, mock_client_class):
        """Test retry logic on timeout"""
        mock_client = Mock()
        
        # First attempt times out, second succeeds
        mock_client.create_order.side_effect = [
            Exception('timeout'),
            {
                'orderId': 12345,
                'status': 'FILLED',
                'symbol': 'ETHUSDT'
            }
        ]
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        order = connector.place_market_order('ETHUSDT', 'BUY', 1.0)
        
        # Should succeed after retry
        assert order is not None
        assert order['orderId'] == 12345
        
        # Should have slept once (for retry)
        mock_sleep.assert_called_once()
    
    @patch('tradlab.live.binance_connector.Client')
    @patch('tradlab.live.binance_connector.time.sleep')
    def test_place_market_order_max_retries(self, mock_sleep, mock_client_class):
        """Test max retries exceeded"""
        mock_client = Mock()
        
        # All attempts time out
        mock_client.create_order.side_effect = Exception('Timeout')
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        
        with pytest.raises(Exception):
            connector.place_market_order('ETHUSDT', 'BUY', 1.0)
        
        # Should have retried max_retries - 1 times
        assert mock_sleep.call_count == connector.max_retries - 1
    
    @patch('tradlab.live.binance_connector.Client')
    @patch('tradlab.live.binance_connector.time.sleep')
    def test_place_market_order_exponential_backoff(self, mock_sleep, mock_client_class):
        """Test exponential backoff in retries"""
        mock_client = Mock()
        
        # First two attempts time out
        mock_client.create_order.side_effect = [
            Exception('timeout'),
            Exception('timeout'),
            {
                'orderId': 12345,
                'status': 'FILLED'
            }
        ]
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        connector.place_market_order('ETHUSDT', 'BUY', 1.0)
        
        # Check that sleep times increase
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert len(sleep_calls) == 2
        assert sleep_calls[1] > sleep_calls[0]  # Second delay should be longer


class TestBinanceConnectorErrorHandling:
    """Test error handling"""
    
    @patch('tradlab.live.binance_connector.Client')
    def test_get_account_balance_api_error(self, mock_client_class):
        """Test handling API error when getting balance"""
        mock_client = Mock()
        mock_client.get_account.side_effect = Exception('API Error')
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        balance = connector.get_account_balance('USDT')
        
        # Should return 0.0 on error
        assert balance == 0.0
    
    @patch('tradlab.live.binance_connector.Client')
    def test_get_current_price_api_error(self, mock_client_class):
        """Test handling API error when getting price"""
        mock_client = Mock()
        mock_client.get_symbol_ticker.side_effect = Exception('API Error')
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        price = connector.get_current_price('ETHUSDT')
        
        # Should return None on error
        assert price is None
    
    @patch('tradlab.live.binance_connector.Client')
    def test_place_market_order_non_timeout_error(self, mock_client_class):
        """Test handling non-timeout error in order placement"""
        mock_client = Mock()
        mock_client.create_order.side_effect = Exception('Insufficient balance')
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        
        # Should raise the exception (not retry for non-timeout errors)
        with pytest.raises(Exception):
            connector.place_market_order('ETHUSDT', 'BUY', 1.0)


class TestBinanceConnectorOtherMethods:
    """Test other Binance connector methods"""
    
    @patch('tradlab.live.binance_connector.Client')
    def test_get_klines(self, mock_client_class):
        """Test getting klines"""
        mock_client = Mock()
        mock_client.get_klines.return_value = [
            [1234567890, '2000', '2010', '1990', '2005', '1000000', 1234571490]
        ]
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        klines = connector.get_klines('ETHUSDT', '4h', 1)
        
        assert len(klines) == 1
        assert klines[0]['open'] == 2000.0
        assert klines[0]['close'] == 2005.0
    
    @patch('tradlab.live.binance_connector.Client')
    def test_place_limit_order(self, mock_client_class):
        """Test placing limit order"""
        mock_client = Mock()
        mock_client.create_order.return_value = {
            'orderId': 12345,
            'status': 'NEW'
        }
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        order = connector.place_limit_order('ETHUSDT', 'BUY', 1.0, 2000.0)
        
        assert order is not None
        assert order['orderId'] == 12345
    
    @patch('tradlab.live.binance_connector.Client')
    def test_get_open_orders(self, mock_client_class):
        """Test getting open orders"""
        mock_client = Mock()
        mock_client.get_open_orders.return_value = [
            {'orderId': 12345, 'status': 'NEW'}
        ]
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        orders = connector.get_open_orders('ETHUSDT')
        
        assert len(orders) == 1
        assert orders[0]['orderId'] == 12345
    
    @patch('tradlab.live.binance_connector.Client')
    def test_cancel_order(self, mock_client_class):
        """Test canceling order"""
        mock_client = Mock()
        mock_client.cancel_order.return_value = {'orderId': 12345}
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        result = connector.cancel_order('ETHUSDT', 12345)
        
        assert result == True
    
    @patch('tradlab.live.binance_connector.Client')
    def test_get_symbol_info(self, mock_client_class):
        """Test getting symbol info"""
        mock_client = Mock()
        mock_client.get_symbol_info.return_value = {
            'symbol': 'ETHUSDT',
            'status': 'TRADING'
        }
        mock_client_class.return_value = mock_client
        
        connector = BinanceConnector('key', 'secret', testnet=True)
        info = connector.get_symbol_info('ETHUSDT')
        
        assert info is not None
        assert info['symbol'] == 'ETHUSDT'


class TestBinanceConnectorTimeout:
    """Test timeout configuration"""
    
    @patch('tradlab.live.binance_connector.Client')
    def test_timeout_configured(self, mock_client_class):
        """Test that timeout is configured in client"""
        connector = BinanceConnector('key', 'secret', testnet=True)
        
        # Verify Client was initialized with timeout
        call_kwargs = mock_client_class.call_args[1]
        assert 'requests_params' in call_kwargs
        assert call_kwargs['requests_params']['timeout'] == 10
        assert call_kwargs['requests_params']['verify'] == True
