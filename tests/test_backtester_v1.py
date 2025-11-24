"""
Unit-тесты для MetricsCalculator и BacktesterV1

Этот файл содержит тесты для проверки корректности расчёта метрик
и базовой функциональности бэктестера.
"""

import pytest
import pandas as pd
import numpy as np
from tradlab.engine.metrics import MetricsCalculator


class TestMetricsCalculator:
    """Тесты для класса MetricsCalculator"""
    
    def test_metrics_sharpe_positive(self):
        """Тест расчёта Sharpe для положительных доходностей"""
        # Положительные доходности с небольшой волатильностью
        returns = pd.Series([0.01, 0.02, 0.015, 0.012, 0.018, 0.020, 0.016])
        
        sharpe = MetricsCalculator.calculate_sharpe(returns, risk_free_rate=0.0)
        
        # Sharpe должен быть положительным
        assert sharpe > 0, "Sharpe должен быть положительным для положительных доходностей"
        assert isinstance(sharpe, float), "Sharpe должен быть float"
    
    def test_metrics_sharpe_negative(self):
        """Тест расчёта Sharpe для отрицательных доходностей"""
        # Отрицательные доходности
        returns = pd.Series([-0.01, -0.02, -0.015, -0.012, -0.018])
        
        sharpe = MetricsCalculator.calculate_sharpe(returns, risk_free_rate=0.0)
        
        # Sharpe должен быть отрицательным
        assert sharpe < 0, "Sharpe должен быть отрицательным для отрицательных доходностей"
    
    def test_metrics_sharpe_zero_std(self):
        """Тест расчёта Sharpe при нулевой волатильности"""
        # Нулевая волатильность (все доходности одинаковые)
        returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        
        sharpe = MetricsCalculator.calculate_sharpe(returns)
        
        # При нулевой волатильности Sharpe = 0
        assert sharpe == 0.0, "Sharpe должен быть 0 при нулевой волатильности"
    
    def test_metrics_sharpe_empty(self):
        """Тест расчёта Sharpe для пустой серии"""
        returns = pd.Series([])
        
        sharpe = MetricsCalculator.calculate_sharpe(returns)
        
        assert sharpe == 0.0, "Sharpe должен быть 0 для пустой серии"
    
    def test_metrics_sortino_positive(self):
        """Тест расчёта Sortino для положительных доходностей"""
        # Смешанные доходности с преобладанием положительных
        returns = pd.Series([0.02, 0.01, -0.005, 0.015, 0.02, -0.003, 0.018])
        
        sortino = MetricsCalculator.calculate_sortino(returns, risk_free_rate=0.0)
        
        # Sortino должен быть положительным
        assert sortino > 0, "Sortino должен быть положительным"
        assert isinstance(sortino, float), "Sortino должен быть float"
    
    def test_metrics_sortino_no_downside(self):
        """Тест расчёта Sortino когда нет отрицательных доходностей"""
        # Только положительные доходности
        returns = pd.Series([0.01, 0.02, 0.015, 0.012])
        
        sortino = MetricsCalculator.calculate_sortino(returns)
        
        # Когда нет отрицательных доходностей, Sortino = 0
        assert sortino == 0.0, "Sortino должен быть 0 когда нет downside"
    
    def test_metrics_max_drawdown_simple(self):
        """Тест расчёта MaxDD для простой equity curve"""
        # Equity curve с просадкой
        equity = pd.Series([10000, 10500, 10200, 9800, 10300, 10800])
        
        max_dd = MetricsCalculator.calculate_max_drawdown(equity)
        
        # Максимальная просадка: (10500 - 9800) / 10500 = 6.67%
        expected_dd = ((10500 - 9800) / 10500) * 100
        assert abs(max_dd - expected_dd) < 0.1, f"MaxDD должен быть ~{expected_dd:.2f}%, получено {max_dd:.2f}%"
    
    def test_metrics_max_drawdown_no_drawdown(self):
        """Тест расчёта MaxDD когда нет просадки"""
        # Растущая equity curve (нет просадки)
        equity = pd.Series([10000, 10100, 10200, 10300, 10400])
        
        max_dd = MetricsCalculator.calculate_max_drawdown(equity)
        
        assert max_dd == 0.0, "MaxDD должен быть 0 когда нет просадки"
    
    def test_metrics_max_drawdown_empty(self):
        """Тест расчёта MaxDD для пустой серии"""
        equity = pd.Series([])
        
        max_dd = MetricsCalculator.calculate_max_drawdown(equity)
        
        assert max_dd == 0.0, "MaxDD должен быть 0 для пустой серии"
    
    def test_metrics_calmar(self):
        """Тест расчёта Calmar ratio"""
        total_return = 25.5  # 25.5% годовая доходность
        max_dd = 10.0  # 10% максимальная просадка
        
        calmar = MetricsCalculator.calculate_calmar(total_return, max_dd)
        
        # Calmar = 25.5 / 10 = 2.55
        assert abs(calmar - 2.55) < 0.01, f"Calmar должен быть ~2.55, получено {calmar}"
    
    def test_metrics_calmar_zero_dd(self):
        """Тест расчёта Calmar при нулевой просадке"""
        calmar = MetricsCalculator.calculate_calmar(20.0, 0.0)
        
        assert calmar == 0.0, "Calmar должен быть 0 при нулевой просадке"
    
    def test_metrics_win_rate_all_winning(self):
        """Тест расчёта Win Rate когда все сделки прибыльные"""
        trades = [
            {"pnl": 100},
            {"pnl": 150},
            {"pnl": 80},
            {"pnl": 200}
        ]
        
        win_rate = MetricsCalculator.calculate_win_rate(trades)
        
        assert win_rate == 100.0, "Win Rate должен быть 100% когда все сделки прибыльные"
    
    def test_metrics_win_rate_half_winning(self):
        """Тест расчёта Win Rate когда 50% сделок прибыльные"""
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 80},
            {"pnl": -40}
        ]
        
        win_rate = MetricsCalculator.calculate_win_rate(trades)
        
        assert win_rate == 50.0, f"Win Rate должен быть 50%, получено {win_rate}"
    
    def test_metrics_win_rate_no_trades(self):
        """Тест расчёта Win Rate когда нет сделок"""
        trades = []
        
        win_rate = MetricsCalculator.calculate_win_rate(trades)
        
        assert win_rate == 0.0, "Win Rate должен быть 0 когда нет сделок"
    
    def test_metrics_win_rate_with_open_trades(self):
        """Тест расчёта Win Rate с незакрытыми сделками (pnl=None)"""
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": None},  # открытая сделка
            {"pnl": 80}
        ]
        
        win_rate = MetricsCalculator.calculate_win_rate(trades)
        
        # Учитываются только закрытые сделки: 2 из 3 прибыльные
        assert abs(win_rate - 66.67) < 0.1, f"Win Rate должен быть ~66.67%, получено {win_rate}"
    
    def test_metrics_profit_factor_profitable(self):
        """Тест расчёта Profit Factor для прибыльных стратегий"""
        trades = [
            {"pnl": 200},
            {"pnl": -50},
            {"pnl": 150},
            {"pnl": -80}
        ]
        
        profit_factor = MetricsCalculator.calculate_profit_factor(trades)
        
        # Profit Factor = (200 + 150) / (50 + 80) = 350 / 130 = 2.69
        expected_pf = 350 / 130
        assert abs(profit_factor - expected_pf) < 0.01, f"Profit Factor должен быть ~{expected_pf:.2f}, получено {profit_factor}"
    
    def test_metrics_profit_factor_no_losses(self):
        """Тест расчёта Profit Factor когда нет убыточных сделок"""
        trades = [
            {"pnl": 100},
            {"pnl": 150},
            {"pnl": 80}
        ]
        
        profit_factor = MetricsCalculator.calculate_profit_factor(trades)
        
        # Когда нет убытков, возвращаем inf
        assert profit_factor == float('inf'), "Profit Factor должен быть inf когда нет убытков"
    
    def test_metrics_profit_factor_no_profits(self):
        """Тест расчёта Profit Factor когда нет прибыльных сделок"""
        trades = [
            {"pnl": -100},
            {"pnl": -150},
            {"pnl": -80}
        ]
        
        profit_factor = MetricsCalculator.calculate_profit_factor(trades)
        
        # Когда нет прибыли, Profit Factor = 0
        assert profit_factor == 0.0, "Profit Factor должен быть 0 когда нет прибыли"
    
    def test_metrics_profit_factor_no_trades(self):
        """Тест расчёта Profit Factor когда нет сделок"""
        trades = []
        
        profit_factor = MetricsCalculator.calculate_profit_factor(trades)
        
        assert profit_factor == 0.0, "Profit Factor должен быть 0 когда нет сделок"


class TestBacktesterV1Integration:
    """
    Интеграционные тесты для BacktesterV1
    
    Примечание: Эти тесты требуют подключения к БД и данных в market.ohlcv
    Можно пропустить если БД недоступна.
    """
    
    @pytest.mark.skip(reason="Требуется подключение к БД")
    def test_backtester_basic_run(self):
        """Базовый тест запуска бэктестера"""
        # Этот тест будет реализован когда БД будет доступна
        pass
    
    @pytest.mark.skip(reason="Требуется подключение к БД")
    def test_backtester_risk_gate(self):
        """Тест проверки Risk Gate"""
        # Этот тест будет реализован когда БД будет доступна
        pass


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
