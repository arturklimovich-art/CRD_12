"""
Backtester v1 для TradLab

Модуль для прогона торговых стратегий на исторических данных
с расчётом метрик и проверкой через Risk Gate.
"""

import pandas as pd
import psycopg2
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

from .strategy_abi import BaseStrategy
from .feature_adapter_v1 import FeatureAdapterV1
from .metrics import MetricsCalculator


class BacktesterV1:
    """
    Бэктестер v1 для прогона торговых стратегий
    
    Основные функции:
    - Загрузка фич из БД через FeatureAdapterV1
    - Прогон стратегии на каждом баре
    - Симуляция исполнения трейдов
    - Расчёт метрик через MetricsCalculator
    - Сохранение трейдов в lab.trades
    - Сохранение результатов в lab.results
    - Проверка Risk Gate
    """
    
    def __init__(
        self,
        db_url: str,
        strategy: BaseStrategy,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.0004,
        slippage_bps: float = 5.0
    ):
        """
        Инициализация бэктестера
        
        Args:
            db_url: PostgreSQL connection string
            strategy: Экземпляр стратегии (наследник BaseStrategy)
            initial_capital: Начальный капитал (USDT)
            commission_rate: Комиссия биржи (в долях, например 0.0004 = 0.04%)
            slippage_bps: Проскальзывание в базисных пунктах (bps)
        """
        self.db_url = db_url
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_bps = slippage_bps
        
        self.feature_adapter = FeatureAdapterV1(db_url)
        
        # Текущее состояние бэктеста
        self.balance = initial_capital
        self.equity_curve: List[float] = [initial_capital]
        self.trades: List[Dict[str, Any]] = []
        self.open_position: Optional[Dict[str, Any]] = None
    
    def run(
        self,
        symbol: str = "ETHUSDT",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Запуск бэктеста
        
        Args:
            symbol: Торговая пара (например, "ETHUSDT")
            start_date: Начальная дата (YYYY-MM-DD)
            end_date: Конечная дата (YYYY-MM-DD)
            run_id: Идентификатор прогона (генерируется автоматически если None)
        
        Returns:
            Dict с результатами бэктеста:
                - run_id: Идентификатор прогона
                - strategy_id: ID стратегии
                - start_ts: Начало периода
                - end_ts: Конец периода
                - pnl_total: Общий PnL
                - sharpe: Коэффициент Шарпа
                - sortino: Коэффициент Сортино
                - max_dd: Максимальная просадка (%)
                - calmar: Коэффициент Калмара
                - win_rate: Процент прибыльных сделок
                - profit_factor: Коэффициент прибыльности
                - pass_risk_gate: Прошла ли стратегия Risk Gate
                - total_trades: Общее количество сделок
        """
        # Генерация run_id
        if run_id is None:
            run_id = f"{self.strategy.strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 1. Загрузка фич из БД
        print(f"[BacktesterV1] Загрузка фич для {symbol}...")
        features_df = self.feature_adapter.fetch_features(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if features_df.empty:
            raise ValueError(f"Нет данных для {symbol} в указанном периоде")
        
        print(f"[BacktesterV1] Загружено {len(features_df)} баров")
        
        # Подготовка фич
        features_df = self.feature_adapter.prepare_features_for_strategy(features_df)
        
        # 2. Прогон стратегии на каждом баре
        print(f"[BacktesterV1] Запуск стратегии {self.strategy.strategy_id}...")
        
        for idx, row in features_df.iterrows():
            # Обновление открытой позиции (проверка на SL/TP)
            if self.open_position:
                self._check_and_close_position(row)
            
            # Генерация сигнала
            if not self.open_position:
                signal = self.strategy.generate_signal(row, self.balance)
                
                if signal:
                    self._open_position(signal, row)
            
            # Обновление equity curve
            current_equity = self._calculate_current_equity(row)
            self.equity_curve.append(current_equity)
        
        # Закрытие открытой позиции в конце периода
        if self.open_position:
            last_row = features_df.iloc[-1]
            self._force_close_position(last_row)
        
        # 3. Расчёт метрик
        print(f"[BacktesterV1] Расчёт метрик...")
        results = self._calculate_metrics(features_df, run_id)
        
        # 4. Проверка Risk Gate
        results['pass_risk_gate'] = self._check_risk_gate(results)
        
        # 5. Сохранение в БД
        print(f"[BacktesterV1] Сохранение результатов в БД...")
        self._save_trades_to_db(run_id)
        self._save_results_to_db(results)
        
        print(f"[BacktesterV1] Бэктест завершён. Run ID: {run_id}")
        print(f"  Total PnL: {results['pnl_total']:.2f} USDT")
        print(f"  Sharpe: {results['sharpe']:.2f}")
        print(f"  Max DD: {results['max_dd']:.2f}%")
        print(f"  Win Rate: {results['win_rate']:.2f}%")
        print(f"  Risk Gate: {'PASS' if results['pass_risk_gate'] else 'FAIL'}")
        
        return results
    
    def _open_position(self, signal, current_bar: pd.Series):
        """Открытие позиции"""
        entry_price = current_bar["close_4h"]
        
        # Применение slippage
        if signal.side == "LONG":
            entry_price *= (1 + self.slippage_bps / 10000)
        else:
            entry_price *= (1 - self.slippage_bps / 10000)
        
        # Комиссия
        commission = signal.size * entry_price * self.commission_rate
        
        self.open_position = {
            "side": signal.side,
            "entry_ts": current_bar["ts_4h"],
            "entry_price": entry_price,
            "qty": signal.size,
            "sl": signal.sl,
            "tp1": signal.tp1,
            "tp2": signal.tp2,
            "commission_entry": commission,
            "meta": signal.meta
        }
        
        # Уменьшаем баланс на комиссию
        self.balance -= commission
    
    def _check_and_close_position(self, current_bar: pd.Series):
        """Проверка и закрытие позиции по SL/TP"""
        if not self.open_position:
            return
        
        current_price = current_bar["close_4h"]
        position = self.open_position
        
        # Проверка SL/TP
        should_close = False
        exit_reason = None
        
        if position["side"] == "LONG":
            if current_price <= position["sl"]:
                should_close = True
                exit_reason = "SL"
            elif current_price >= position["tp1"]:
                should_close = True
                exit_reason = "TP1"
        else:  # SHORT
            if current_price >= position["sl"]:
                should_close = True
                exit_reason = "SL"
            elif current_price <= position["tp1"]:
                should_close = True
                exit_reason = "TP1"
        
        if should_close:
            self._close_position(current_bar, exit_reason)
    
    def _close_position(self, current_bar: pd.Series, exit_reason: str):
        """Закрытие позиции"""
        if not self.open_position:
            return
        
        position = self.open_position
        exit_price = current_bar["close_4h"]
        
        # Применение slippage
        if position["side"] == "LONG":
            exit_price *= (1 - self.slippage_bps / 10000)
        else:
            exit_price *= (1 + self.slippage_bps / 10000)
        
        # Комиссия на выход
        commission_exit = position["qty"] * exit_price * self.commission_rate
        
        # Расчёт PnL
        if position["side"] == "LONG":
            pnl = position["qty"] * (exit_price - position["entry_price"])
        else:  # SHORT
            pnl = position["qty"] * (position["entry_price"] - exit_price)
        
        # Вычитаем комиссии
        pnl -= (position["commission_entry"] + commission_exit)
        
        # Расчёт PnL в процентах
        pnl_pct = (pnl / (position["qty"] * position["entry_price"])) * 100
        
        # Обновление баланса
        self.balance += pnl
        
        # Сохранение трейда
        trade = {
            "strategy_id": self.strategy.strategy_id,
            "mode": "backtest",
            "symbol": current_bar.get("symbol", "ETHUSDT"),
            "side": position["side"],
            "qty": position["qty"],
            "entry_ts": position["entry_ts"],
            "entry_price": position["entry_price"],
            "exit_ts": current_bar["ts_4h"],
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "meta": {
                **position.get("meta", {}),
                "exit_reason": exit_reason,
                "commission_entry": position["commission_entry"],
                "commission_exit": commission_exit
            }
        }
        
        self.trades.append(trade)
        self.open_position = None
    
    def _force_close_position(self, current_bar: pd.Series):
        """Принудительное закрытие позиции в конце периода"""
        self._close_position(current_bar, "EOD")
    
    def _calculate_current_equity(self, current_bar: pd.Series) -> float:
        """Расчёт текущего капитала"""
        equity = self.balance
        
        if self.open_position:
            position = self.open_position
            current_price = current_bar["close_4h"]
            
            # Нереализованный PnL
            if position["side"] == "LONG":
                unrealized_pnl = position["qty"] * (current_price - position["entry_price"])
            else:
                unrealized_pnl = position["qty"] * (position["entry_price"] - current_price)
            
            equity += unrealized_pnl
        
        return equity
    
    def _calculate_metrics(self, features_df: pd.DataFrame, run_id: str) -> Dict[str, Any]:
        """Расчёт метрик бэктеста"""
        # Equity curve
        equity_series = pd.Series(self.equity_curve)
        
        # Дневные доходности
        returns = equity_series.pct_change().dropna()
        
        # Метрики
        pnl_total = self.balance - self.initial_capital
        total_return_pct = (pnl_total / self.initial_capital) * 100
        
        sharpe = MetricsCalculator.calculate_sharpe(returns)
        sortino = MetricsCalculator.calculate_sortino(returns)
        max_dd = MetricsCalculator.calculate_max_drawdown(equity_series)
        calmar = MetricsCalculator.calculate_calmar(total_return_pct, max_dd)
        win_rate = MetricsCalculator.calculate_win_rate(self.trades)
        profit_factor = MetricsCalculator.calculate_profit_factor(self.trades)
        
        results = {
            "run_id": run_id,
            "strategy_id": self.strategy.strategy_id,
            "start_ts": features_df.iloc[0]["ts_4h"],
            "end_ts": features_df.iloc[-1]["ts_4h"],
            "pnl_total": pnl_total,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_dd": max_dd,
            "calmar": calmar,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_trades": len(self.trades),
            "initial_capital": self.initial_capital,
            "final_capital": self.balance
        }
        
        return results
    
    def _check_risk_gate(self, results: Dict[str, Any]) -> bool:
        """
        Проверка Risk Gate
        
        Критерии для L1:
        - Sharpe >= 1.0
        - MaxDD <= 20%
        - Win Rate >= 40%
        """
        sharpe_pass = results["sharpe"] >= 1.0
        max_dd_pass = results["max_dd"] <= 20.0
        win_rate_pass = results["win_rate"] >= 40.0
        
        return sharpe_pass and max_dd_pass and win_rate_pass
    
    def _save_trades_to_db(self, run_id: str):
        """Сохранение трейдов в lab.trades"""
        if not self.trades:
            print("[BacktesterV1] Нет трейдов для сохранения")
            return
        
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        try:
            for trade in self.trades:
                cursor.execute("""
                    INSERT INTO lab.trades (
                        run_id, strategy_id, mode, symbol, side, qty,
                        entry_ts, entry_price, exit_ts, exit_price, pnl, pnl_pct, meta
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    run_id,
                    trade["strategy_id"],
                    trade["mode"],
                    trade["symbol"],
                    trade["side"],
                    trade["qty"],
                    trade["entry_ts"],
                    trade["entry_price"],
                    trade["exit_ts"],
                    trade["exit_price"],
                    trade["pnl"],
                    trade["pnl_pct"],
                    psycopg2.extras.Json(trade.get("meta", {}))
                ))
            
            conn.commit()
            print(f"[BacktesterV1] Сохранено {len(self.trades)} трейдов")
        
        except Exception as e:
            conn.rollback()
            print(f"[BacktesterV1] Ошибка при сохранении трейдов: {e}")
            raise
        
        finally:
            cursor.close()
            conn.close()
    
    def _save_results_to_db(self, results: Dict[str, Any]):
        """Сохранение результатов в lab.results"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO lab.results (
                    run_id, strategy_id, start_ts, end_ts, pnl_total,
                    sharpe, sortino, max_dd, calmar, win_rate, profit_factor,
                    pass_risk_gate, meta
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (run_id) DO UPDATE SET
                    strategy_id = EXCLUDED.strategy_id,
                    start_ts = EXCLUDED.start_ts,
                    end_ts = EXCLUDED.end_ts,
                    pnl_total = EXCLUDED.pnl_total,
                    sharpe = EXCLUDED.sharpe,
                    sortino = EXCLUDED.sortino,
                    max_dd = EXCLUDED.max_dd,
                    calmar = EXCLUDED.calmar,
                    win_rate = EXCLUDED.win_rate,
                    profit_factor = EXCLUDED.profit_factor,
                    pass_risk_gate = EXCLUDED.pass_risk_gate,
                    meta = EXCLUDED.meta
            """, (
                results["run_id"],
                results["strategy_id"],
                results["start_ts"],
                results["end_ts"],
                results["pnl_total"],
                results["sharpe"],
                results["sortino"],
                results["max_dd"],
                results["calmar"],
                results["win_rate"],
                results["profit_factor"],
                results["pass_risk_gate"],
                psycopg2.extras.Json({
                    "initial_capital": results.get("initial_capital"),
                    "final_capital": results.get("final_capital"),
                    "total_trades": results.get("total_trades")
                })
            ))
            
            conn.commit()
            print(f"[BacktesterV1] Результаты сохранены для run_id: {results['run_id']}")
        
        except Exception as e:
            conn.rollback()
            print(f"[BacktesterV1] Ошибка при сохранении результатов: {e}")
            raise
        
        finally:
            cursor.close()
            conn.close()
