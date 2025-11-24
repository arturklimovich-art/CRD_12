"""
Модуль для расчёта метрик торговых стратегий

Этот модуль содержит класс MetricsCalculator с статическими методами
для расчёта различных метрик эффективности торговых стратегий.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any


class MetricsCalculator:
    """
    Класс для расчёта метрик торговых стратегий
    
    Все методы статические, класс используется как namespace
    для группировки связанных функций расчёта метрик.
    """
    
    @staticmethod
    def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        Расчёт коэффициента Шарпа
        
        Sharpe Ratio = (среднее значение доходности - безрисковая ставка) / std доходности
        
        Args:
            returns: Pandas Series с доходностями (например, ежедневными)
            risk_free_rate: Безрисковая ставка (годовая, в долях единицы)
        
        Returns:
            float: Коэффициент Шарпа (аннуализированный)
        
        Note:
            - Если std доходности = 0, возвращается 0
            - Аннуализация: умножаем на sqrt(252) для дневных данных
        """
        if len(returns) == 0:
            return 0.0
        
        # Среднее значение доходности
        mean_return = returns.mean()
        
        # Стандартное отклонение доходности
        std_return = returns.std()
        
        if std_return == 0 or np.isnan(std_return):
            return 0.0
        
        # Расчёт Sharpe (аннуализация sqrt(252) для дневных данных)
        # Предполагаем, что returns - это дневные доходности
        sharpe = (mean_return - risk_free_rate / 252) / std_return * np.sqrt(252)
        
        return float(sharpe)
    
    @staticmethod
    def calculate_sortino(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        Расчёт коэффициента Сортино
        
        Sortino Ratio = (среднее значение доходности - безрисковая ставка) / downside deviation
        
        Args:
            returns: Pandas Series с доходностями
            risk_free_rate: Безрисковая ставка (годовая, в долях единицы)
        
        Returns:
            float: Коэффициент Сортино (аннуализированный)
        
        Note:
            - Учитывается только downside risk (отрицательные доходности)
            - Если downside deviation = 0, возвращается 0
        """
        if len(returns) == 0:
            return 0.0
        
        mean_return = returns.mean()
        
        # Downside returns (только отрицательные доходности)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            # Нет отрицательных доходностей
            return 0.0
        
        # Downside deviation
        downside_std = downside_returns.std()
        
        if downside_std == 0 or np.isnan(downside_std):
            return 0.0
        
        # Расчёт Sortino (аннуализация sqrt(252))
        sortino = (mean_return - risk_free_rate / 252) / downside_std * np.sqrt(252)
        
        return float(sortino)
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """
        Расчёт максимальной просадки (Max Drawdown)
        
        MaxDD = max((peak - valley) / peak)
        
        Args:
            equity_curve: Pandas Series с кривой капитала (equity curve)
        
        Returns:
            float: Максимальная просадка в процентах (положительное число, например 15.5 для 15.5%)
        
        Note:
            - Возвращается значение в процентах (не в долях единицы)
            - Если нет просадки, возвращается 0.0
        """
        if len(equity_curve) == 0:
            return 0.0
        
        # Кумулятивный максимум
        cumulative_max = equity_curve.expanding().max()
        
        # Просадка на каждом шаге
        drawdown = (cumulative_max - equity_curve) / cumulative_max
        
        # Максимальная просадка
        max_dd = drawdown.max()
        
        if np.isnan(max_dd):
            return 0.0
        
        # Возвращаем в процентах
        return float(max_dd * 100)
    
    @staticmethod
    def calculate_calmar(total_return: float, max_dd: float) -> float:
        """
        Расчёт коэффициента Калмара (Calmar Ratio)
        
        Calmar = Годовая доходность / Max Drawdown
        
        Args:
            total_return: Общая доходность (в процентах, например 25.5 для 25.5%)
            max_dd: Максимальная просадка (в процентах, например 15.5 для 15.5%)
        
        Returns:
            float: Коэффициент Калмара
        
        Note:
            - Если max_dd = 0, возвращается 0
            - total_return ожидается в процентах
        """
        if max_dd == 0 or np.isnan(max_dd):
            return 0.0
        
        calmar = total_return / max_dd
        
        return float(calmar)
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
        """
        Расчёт процента прибыльных сделок (Win Rate)
        
        Win Rate = (количество прибыльных сделок / общее количество сделок) * 100
        
        Args:
            trades: Список словарей с информацией о сделках.
                    Каждый словарь должен содержать ключ 'pnl' (прибыль/убыток)
        
        Returns:
            float: Процент прибыльных сделок (0-100)
        
        Note:
            - Сделка считается прибыльной, если pnl > 0
            - Если нет закрытых сделок, возвращается 0.0
        """
        if not trades:
            return 0.0
        
        # Фильтруем только закрытые сделки (с pnl)
        closed_trades = [t for t in trades if t.get('pnl') is not None]
        
        if not closed_trades:
            return 0.0
        
        # Количество прибыльных сделок
        winning_trades = sum(1 for t in closed_trades if t['pnl'] > 0)
        
        # Win Rate в процентах
        win_rate = (winning_trades / len(closed_trades)) * 100
        
        return float(win_rate)
    
    @staticmethod
    def calculate_profit_factor(trades: List[Dict[str, Any]]) -> float:
        """
        Расчёт коэффициента прибыльности (Profit Factor)
        
        Profit Factor = Сумма прибыльных сделок / Абс(Сумма убыточных сделок)
        
        Args:
            trades: Список словарей с информацией о сделках.
                    Каждый словарь должен содержать ключ 'pnl'
        
        Returns:
            float: Коэффициент прибыльности (>1 хорошо, <1 плохо)
        
        Note:
            - Если нет убыточных сделок, возвращается 0.0
            - Если нет закрытых сделок, возвращается 0.0
        """
        if not trades:
            return 0.0
        
        # Фильтруем только закрытые сделки
        closed_trades = [t for t in trades if t.get('pnl') is not None]
        
        if not closed_trades:
            return 0.0
        
        # Сумма прибыльных сделок
        gross_profit = sum(t['pnl'] for t in closed_trades if t['pnl'] > 0)
        
        # Сумма убыточных сделок (абсолютное значение)
        gross_loss = abs(sum(t['pnl'] for t in closed_trades if t['pnl'] < 0))
        
        if gross_loss == 0:
            # Нет убыточных сделок
            return 0.0 if gross_profit == 0 else float('inf')
        
        profit_factor = gross_profit / gross_loss
        
        return float(profit_factor)
