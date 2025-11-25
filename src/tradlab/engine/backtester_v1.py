"""
Backtester v1 Ð´Ð»Ñ TradLab

ÐœÐ¾Ð´ÑƒÐ»ÑŒ Ð´Ð»Ñ Ð¿Ñ€Ð¾Ð³Ð¾Ð½Ð° Ñ‚Ð¾Ñ€Ð³Ð¾Ð²Ñ‹Ñ… ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¹ Ð½Ð° Ð¸ÑÑ‚Ð¾Ñ€Ð¸Ñ‡ÐµÑÐºÐ¸Ñ… Ð´Ð°Ð½Ð½Ñ‹Ñ…
Ñ Ñ€Ð°ÑÑ‡Ñ‘Ñ‚Ð¾Ð¼ Ð¼ÐµÑ‚Ñ€Ð¸Ðº Ð¸ Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ¾Ð¹ Ñ‡ÐµÑ€ÐµÐ· Risk Gate.
"""

import pandas as pd
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

from .strategy_abi import BaseStrategy
from .feature_adapter_v1 import FeatureAdapterV1
from .metrics import MetricsCalculator


class BacktesterV1:
    """
    Ð‘ÑÐºÑ‚ÐµÑÑ‚ÐµÑ€ v1 Ð´Ð»Ñ Ð¿Ñ€Ð¾Ð³Ð¾Ð½Ð° Ñ‚Ð¾Ñ€Ð³Ð¾Ð²Ñ‹Ñ… ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¹
    
    ÐžÑÐ½Ð¾Ð²Ð½Ñ‹Ðµ Ñ„ÑƒÐ½ÐºÑ†Ð¸Ð¸:
    - Ð—Ð°Ð³Ñ€ÑƒÐ·ÐºÐ° Ñ„Ð¸Ñ‡ Ð¸Ð· Ð‘Ð” Ñ‡ÐµÑ€ÐµÐ· FeatureAdapterV1
    - ÐŸÑ€Ð¾Ð³Ð¾Ð½ ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¸ Ð½Ð° ÐºÐ°Ð¶Ð´Ð¾Ð¼ Ð±Ð°Ñ€Ðµ
    - Ð¡Ð¸Ð¼ÑƒÐ»ÑÑ†Ð¸Ñ Ð¸ÑÐ¿Ð¾Ð»Ð½ÐµÐ½Ð¸Ñ Ñ‚Ñ€ÐµÐ¹Ð´Ð¾Ð²
    - Ð Ð°ÑÑ‡Ñ‘Ñ‚ Ð¼ÐµÑ‚Ñ€Ð¸Ðº Ñ‡ÐµÑ€ÐµÐ· MetricsCalculator
    - Ð¡Ð¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ðµ Ñ‚Ñ€ÐµÐ¹Ð´Ð¾Ð² Ð² lab.trades
    - Ð¡Ð¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ðµ Ñ€ÐµÐ·ÑƒÐ»ÑŒÑ‚Ð°Ñ‚Ð¾Ð² Ð² lab.results
    - ÐŸÑ€Ð¾Ð²ÐµÑ€ÐºÐ° Risk Gate
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
        Ð˜Ð½Ð¸Ñ†Ð¸Ð°Ð»Ð¸Ð·Ð°Ñ†Ð¸Ñ Ð±ÑÐºÑ‚ÐµÑÑ‚ÐµÑ€Ð°
        
        Args:
            db_url: PostgreSQL connection string
            strategy: Ð­ÐºÐ·ÐµÐ¼Ð¿Ð»ÑÑ€ ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¸ (Ð½Ð°ÑÐ»ÐµÐ´Ð½Ð¸Ðº BaseStrategy)
            initial_capital: ÐÐ°Ñ‡Ð°Ð»ÑŒÐ½Ñ‹Ð¹ ÐºÐ°Ð¿Ð¸Ñ‚Ð°Ð» (USDT)
            commission_rate: ÐšÐ¾Ð¼Ð¸ÑÑÐ¸Ñ Ð±Ð¸Ñ€Ð¶Ð¸ (Ð² Ð´Ð¾Ð»ÑÑ…, Ð½Ð°Ð¿Ñ€Ð¸Ð¼ÐµÑ€ 0.0004 = 0.04%)
            slippage_bps: ÐŸÑ€Ð¾ÑÐºÐ°Ð»ÑŒÐ·Ñ‹Ð²Ð°Ð½Ð¸Ðµ Ð² Ð±Ð°Ð·Ð¸ÑÐ½Ñ‹Ñ… Ð¿ÑƒÐ½ÐºÑ‚Ð°Ñ… (bps)
        """
        self.db_url = db_url
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_bps = slippage_bps
        
        self.feature_adapter = FeatureAdapterV1(db_url)
        
        # Ð¢ÐµÐºÑƒÑ‰ÐµÐµ ÑÐ¾ÑÑ‚Ð¾ÑÐ½Ð¸Ðµ Ð±ÑÐºÑ‚ÐµÑÑ‚Ð°
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
        Ð—Ð°Ð¿ÑƒÑÐº Ð±ÑÐºÑ‚ÐµÑÑ‚Ð°
        
        Args:
            symbol: Ð¢Ð¾Ñ€Ð³Ð¾Ð²Ð°Ñ Ð¿Ð°Ñ€Ð° (Ð½Ð°Ð¿Ñ€Ð¸Ð¼ÐµÑ€, "ETHUSDT")
            start_date: ÐÐ°Ñ‡Ð°Ð»ÑŒÐ½Ð°Ñ Ð´Ð°Ñ‚Ð° (YYYY-MM-DD)
            end_date: ÐšÐ¾Ð½ÐµÑ‡Ð½Ð°Ñ Ð´Ð°Ñ‚Ð° (YYYY-MM-DD)
            run_id: Ð˜Ð´ÐµÐ½Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ‚Ð¾Ñ€ Ð¿Ñ€Ð¾Ð³Ð¾Ð½Ð° (Ð³ÐµÐ½ÐµÑ€Ð¸Ñ€ÑƒÐµÑ‚ÑÑ Ð°Ð²Ñ‚Ð¾Ð¼Ð°Ñ‚Ð¸Ñ‡ÐµÑÐºÐ¸ ÐµÑÐ»Ð¸ None)
        
        Returns:
            Dict Ñ Ñ€ÐµÐ·ÑƒÐ»ÑŒÑ‚Ð°Ñ‚Ð°Ð¼Ð¸ Ð±ÑÐºÑ‚ÐµÑÑ‚Ð°:
                - run_id: Ð˜Ð´ÐµÐ½Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ‚Ð¾Ñ€ Ð¿Ñ€Ð¾Ð³Ð¾Ð½Ð°
                - strategy_id: ID ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¸
                - start_ts: ÐÐ°Ñ‡Ð°Ð»Ð¾ Ð¿ÐµÑ€Ð¸Ð¾Ð´Ð°
                - end_ts: ÐšÐ¾Ð½ÐµÑ† Ð¿ÐµÑ€Ð¸Ð¾Ð´Ð°
                - pnl_total: ÐžÐ±Ñ‰Ð¸Ð¹ PnL
                - sharpe: ÐšÐ¾ÑÑ„Ñ„Ð¸Ñ†Ð¸ÐµÐ½Ñ‚ Ð¨Ð°Ñ€Ð¿Ð°
                - sortino: ÐšÐ¾ÑÑ„Ñ„Ð¸Ñ†Ð¸ÐµÐ½Ñ‚ Ð¡Ð¾Ñ€Ñ‚Ð¸Ð½Ð¾
                - max_dd: ÐœÐ°ÐºÑÐ¸Ð¼Ð°Ð»ÑŒÐ½Ð°Ñ Ð¿Ñ€Ð¾ÑÐ°Ð´ÐºÐ° (%)
                - calmar: ÐšÐ¾ÑÑ„Ñ„Ð¸Ñ†Ð¸ÐµÐ½Ñ‚ ÐšÐ°Ð»Ð¼Ð°Ñ€Ð°
                - win_rate: ÐŸÑ€Ð¾Ñ†ÐµÐ½Ñ‚ Ð¿Ñ€Ð¸Ð±Ñ‹Ð»ÑŒÐ½Ñ‹Ñ… ÑÐ´ÐµÐ»Ð¾Ðº
                - profit_factor: ÐšÐ¾ÑÑ„Ñ„Ð¸Ñ†Ð¸ÐµÐ½Ñ‚ Ð¿Ñ€Ð¸Ð±Ñ‹Ð»ÑŒÐ½Ð¾ÑÑ‚Ð¸
                - pass_risk_gate: ÐŸÑ€Ð¾ÑˆÐ»Ð° Ð»Ð¸ ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ñ Risk Gate
                - total_trades: ÐžÐ±Ñ‰ÐµÐµ ÐºÐ¾Ð»Ð¸Ñ‡ÐµÑÑ‚Ð²Ð¾ ÑÐ´ÐµÐ»Ð¾Ðº
        """
        # Ð“ÐµÐ½ÐµÑ€Ð°Ñ†Ð¸Ñ run_id
        if run_id is None:
            run_id = f"{self.strategy.strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 1. Ð—Ð°Ð³Ñ€ÑƒÐ·ÐºÐ° Ñ„Ð¸Ñ‡ Ð¸Ð· Ð‘Ð”
        print(f"[BacktesterV1] Ð—Ð°Ð³Ñ€ÑƒÐ·ÐºÐ° Ñ„Ð¸Ñ‡ Ð´Ð»Ñ {symbol}...")
        features_df = self.feature_adapter.fetch_features(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if features_df.empty:
            raise ValueError(f"ÐÐµÑ‚ Ð´Ð°Ð½Ð½Ñ‹Ñ… Ð´Ð»Ñ {symbol} Ð² ÑƒÐºÐ°Ð·Ð°Ð½Ð½Ð¾Ð¼ Ð¿ÐµÑ€Ð¸Ð¾Ð´Ðµ")
        
        print(f"[BacktesterV1] Ð—Ð°Ð³Ñ€ÑƒÐ¶ÐµÐ½Ð¾ {len(features_df)} Ð±Ð°Ñ€Ð¾Ð²")
        
        # ÐŸÐ¾Ð´Ð³Ð¾Ñ‚Ð¾Ð²ÐºÐ° Ñ„Ð¸Ñ‡
        features_df = self.feature_adapter.prepare_features_for_strategy(features_df)
        
        # 2. ÐŸÑ€Ð¾Ð³Ð¾Ð½ ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¸ Ð½Ð° ÐºÐ°Ð¶Ð´Ð¾Ð¼ Ð±Ð°Ñ€Ðµ
        print(f"[BacktesterV1] Ð—Ð°Ð¿ÑƒÑÐº ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¸ {self.strategy.strategy_id}...")
        
        for idx, row in features_df.iterrows():
            # ÐžÐ±Ð½Ð¾Ð²Ð»ÐµÐ½Ð¸Ðµ Ð¾Ñ‚ÐºÑ€Ñ‹Ñ‚Ð¾Ð¹ Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸ (Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ° Ð½Ð° SL/TP)
            if self.open_position:
                self._check_and_close_position(row)
            
            # Ð“ÐµÐ½ÐµÑ€Ð°Ñ†Ð¸Ñ ÑÐ¸Ð³Ð½Ð°Ð»Ð°
            if not self.open_position:
                signal = self.strategy.generate_signal(row, self.balance)
                
                if signal:
                    self._open_position(signal, row)
            
            # ÐžÐ±Ð½Ð¾Ð²Ð»ÐµÐ½Ð¸Ðµ equity curve
            current_equity = self._calculate_current_equity(row)
            self.equity_curve.append(current_equity)
        
        # Ð—Ð°ÐºÑ€Ñ‹Ñ‚Ð¸Ðµ Ð¾Ñ‚ÐºÑ€Ñ‹Ñ‚Ð¾Ð¹ Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸ Ð² ÐºÐ¾Ð½Ñ†Ðµ Ð¿ÐµÑ€Ð¸Ð¾Ð´Ð°
        if self.open_position:
            last_row = features_df.iloc[-1]
            self._force_close_position(last_row)
        
        # 3. Ð Ð°ÑÑ‡Ñ‘Ñ‚ Ð¼ÐµÑ‚Ñ€Ð¸Ðº
        print(f"[BacktesterV1] Ð Ð°ÑÑ‡Ñ‘Ñ‚ Ð¼ÐµÑ‚Ñ€Ð¸Ðº...")
        results = self._calculate_metrics(features_df, run_id)
        
        # 4. ÐŸÑ€Ð¾Ð²ÐµÑ€ÐºÐ° Risk Gate
        results['pass_risk_gate'] = self._check_risk_gate(results)
        
        # 5. Ð¡Ð¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ðµ Ð² Ð‘Ð”
        print(f"[BacktesterV1] Ð¡Ð¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ðµ Ñ€ÐµÐ·ÑƒÐ»ÑŒÑ‚Ð°Ñ‚Ð¾Ð² Ð² Ð‘Ð”...")
        self._save_trades_to_db(run_id)
        self._save_results_to_db(results)
        
        print(f"[BacktesterV1] Ð‘ÑÐºÑ‚ÐµÑÑ‚ Ð·Ð°Ð²ÐµÑ€ÑˆÑ‘Ð½. Run ID: {run_id}")
        print(f"  Total PnL: {results['pnl_total']:.2f} USDT")
        print(f"  Sharpe: {results['sharpe']:.2f}")
        print(f"  Max DD: {results['max_dd']:.2f}%")
        print(f"  Win Rate: {results['win_rate']:.2f}%")
        print(f"  Risk Gate: {'PASS' if results['pass_risk_gate'] else 'FAIL'}")
        
        return results
    
    def _open_position(self, signal, current_bar: pd.Series):
        """ÐžÑ‚ÐºÑ€Ñ‹Ñ‚Ð¸Ðµ Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸"""
        entry_price = current_bar["close_4h"]
        
        # ÐŸÑ€Ð¸Ð¼ÐµÐ½ÐµÐ½Ð¸Ðµ slippage
        if signal.side == "LONG":
            entry_price *= (1 + self.slippage_bps / 10000)
        else:
            entry_price *= (1 - self.slippage_bps / 10000)
        
        # ÐšÐ¾Ð¼Ð¸ÑÑÐ¸Ñ
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
        
        # Ð£Ð¼ÐµÐ½ÑŒÑˆÐ°ÐµÐ¼ Ð±Ð°Ð»Ð°Ð½Ñ Ð½Ð° ÐºÐ¾Ð¼Ð¸ÑÑÐ¸ÑŽ
        self.balance -= commission
    
    def _check_and_close_position(self, current_bar: pd.Series):
        """ÐŸÑ€Ð¾Ð²ÐµÑ€ÐºÐ° Ð¸ Ð·Ð°ÐºÑ€Ñ‹Ñ‚Ð¸Ðµ Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸ Ð¿Ð¾ SL/TP"""
        if not self.open_position:
            return
        
        current_price = current_bar["close_4h"]
        position = self.open_position
        
        # ÐŸÑ€Ð¾Ð²ÐµÑ€ÐºÐ° SL/TP
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
        """Ð—Ð°ÐºÑ€Ñ‹Ñ‚Ð¸Ðµ Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸"""
        if not self.open_position:
            return
        
        position = self.open_position
        exit_price = current_bar["close_4h"]
        
        # ÐŸÑ€Ð¸Ð¼ÐµÐ½ÐµÐ½Ð¸Ðµ slippage
        if position["side"] == "LONG":
            exit_price *= (1 - self.slippage_bps / 10000)
        else:
            exit_price *= (1 + self.slippage_bps / 10000)
        
        # ÐšÐ¾Ð¼Ð¸ÑÑÐ¸Ñ Ð½Ð° Ð²Ñ‹Ñ…Ð¾Ð´
        commission_exit = position["qty"] * exit_price * self.commission_rate
        
        # Ð Ð°ÑÑ‡Ñ‘Ñ‚ PnL
        if position["side"] == "LONG":
            pnl = position["qty"] * (exit_price - position["entry_price"])
        else:  # SHORT
            pnl = position["qty"] * (position["entry_price"] - exit_price)
        
        # Ð’Ñ‹Ñ‡Ð¸Ñ‚Ð°ÐµÐ¼ ÐºÐ¾Ð¼Ð¸ÑÑÐ¸Ð¸
        pnl -= (position["commission_entry"] + commission_exit)
        
        # Ð Ð°ÑÑ‡Ñ‘Ñ‚ PnL Ð² Ð¿Ñ€Ð¾Ñ†ÐµÐ½Ñ‚Ð°Ñ…
        pnl_pct = (pnl / (position["qty"] * position["entry_price"])) * 100
        
        # ÐžÐ±Ð½Ð¾Ð²Ð»ÐµÐ½Ð¸Ðµ Ð±Ð°Ð»Ð°Ð½ÑÐ°
        self.balance += pnl
        
        # Ð¡Ð¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ðµ Ñ‚Ñ€ÐµÐ¹Ð´Ð°
        trade = {
            "strategy_id": self.strategy.strategy_id,
            "mode": "backtest",
            "symbol": str(current_bar.get("symbol", "ETHUSDT")),
            "side": str(position["side"]),
            "qty": float(position["qty"]),
            "entry_ts": position["entry_ts"],
            "entry_price": float(position["entry_price"]),
            "exit_ts": current_bar["ts_4h"],
            "exit_price": float(exit_price),
            "pnl": float(pnl),
            "pnl_pct": float(pnl_pct),
            "meta": {
                **position.get("meta", {}),
                "exit_reason": exit_reason,
                "commission_entry": float(position["commission_entry"]),
                "commission_exit": float(commission_exit)
            }
        }
        
        self.trades.append(trade)
        self.open_position = None
    
    def _force_close_position(self, current_bar: pd.Series):
        """ÐŸÑ€Ð¸Ð½ÑƒÐ´Ð¸Ñ‚ÐµÐ»ÑŒÐ½Ð¾Ðµ Ð·Ð°ÐºÑ€Ñ‹Ñ‚Ð¸Ðµ Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸ Ð² ÐºÐ¾Ð½Ñ†Ðµ Ð¿ÐµÑ€Ð¸Ð¾Ð´Ð°"""
        self._close_position(current_bar, "EOD")
    
    def _calculate_current_equity(self, current_bar: pd.Series) -> float:
        """Ð Ð°ÑÑ‡Ñ‘Ñ‚ Ñ‚ÐµÐºÑƒÑ‰ÐµÐ³Ð¾ ÐºÐ°Ð¿Ð¸Ñ‚Ð°Ð»Ð°"""
        equity = self.balance
        
        if self.open_position:
            position = self.open_position
            current_price = current_bar["close_4h"]
            
            # ÐÐµÑ€ÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ð°Ð½Ð½Ñ‹Ð¹ PnL
            if position["side"] == "LONG":
                unrealized_pnl = position["qty"] * (current_price - position["entry_price"])
            else:
                unrealized_pnl = position["qty"] * (position["entry_price"] - current_price)
            
            equity += unrealized_pnl
        
        return equity
    
    def _calculate_metrics(self, features_df: pd.DataFrame, run_id: str) -> Dict[str, Any]:
        """Ð Ð°ÑÑ‡Ñ‘Ñ‚ Ð¼ÐµÑ‚Ñ€Ð¸Ðº Ð±ÑÐºÑ‚ÐµÑÑ‚Ð°"""
        # Equity curve
        equity_series = pd.Series(self.equity_curve)
        
        # Ð”Ð½ÐµÐ²Ð½Ñ‹Ðµ Ð´Ð¾Ñ…Ð¾Ð´Ð½Ð¾ÑÑ‚Ð¸
        returns = equity_series.pct_change().dropna()
        
        # ÐœÐµÑ‚Ñ€Ð¸ÐºÐ¸
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
        ÐŸÑ€Ð¾Ð²ÐµÑ€ÐºÐ° Risk Gate
        
        ÐšÑ€Ð¸Ñ‚ÐµÑ€Ð¸Ð¸ Ð´Ð»Ñ L1:
        - Sharpe >= 1.0
        - MaxDD <= 20%
        - Win Rate >= 40%
        """
        sharpe_pass = results["sharpe"] >= 1.0
        max_dd_pass = results["max_dd"] <= 20.0
        win_rate_pass = results["win_rate"] >= 40.0
        
        return sharpe_pass and max_dd_pass and win_rate_pass
    
    def _save_trades_to_db(self, run_id: str):
        """Ð¡Ð¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ðµ Ñ‚Ñ€ÐµÐ¹Ð´Ð¾Ð² Ð² lab.trades"""
        if not self.trades:
            print("[BacktesterV1] ÐÐµÑ‚ Ñ‚Ñ€ÐµÐ¹Ð´Ð¾Ð² Ð´Ð»Ñ ÑÐ¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ñ")
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
            print(f"[BacktesterV1] Ð¡Ð¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¾ {len(self.trades)} Ñ‚Ñ€ÐµÐ¹Ð´Ð¾Ð²")
        
        except Exception as e:
            conn.rollback()
            print(f"[BacktesterV1] ÐžÑˆÐ¸Ð±ÐºÐ° Ð¿Ñ€Ð¸ ÑÐ¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ð¸ Ñ‚Ñ€ÐµÐ¹Ð´Ð¾Ð²: {e}")
            raise
        
        finally:
            cursor.close()
            conn.close()
    
    def _save_results_to_db(self, results: Dict[str, Any]):
        """Ð¡Ð¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ðµ Ñ€ÐµÐ·ÑƒÐ»ÑŒÑ‚Ð°Ñ‚Ð¾Ð² Ð² lab.results"""
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
                float(results["pnl_total"]),
                float(results["sharpe"]),
                float(results["sortino"]),
                float(results["max_dd"]),
                float(results["calmar"]),
                float(results["win_rate"]),
                float(results["profit_factor"]),
                bool(results["pass_risk_gate"]),
                psycopg2.extras.Json({
                    "initial_capital": float(results.get("initial_capital", 0)),
                    "final_capital": float(results.get("final_capital", 0)),
                    "total_trades": int(results.get("total_trades", 0))
                })
            ))
            
            conn.commit()
            print(f"[BacktesterV1] Ð ÐµÐ·ÑƒÐ»ÑŒÑ‚Ð°Ñ‚Ñ‹ ÑÐ¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ñ‹ Ð´Ð»Ñ run_id: {results['run_id']}")
        
        except Exception as e:
            conn.rollback()
            print(f"[BacktesterV1] ÐžÑˆÐ¸Ð±ÐºÐ° Ð¿Ñ€Ð¸ ÑÐ¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ð¸ Ñ€ÐµÐ·ÑƒÐ»ÑŒÑ‚Ð°Ñ‚Ð¾Ð²: {e}")
            raise
        
        finally:
            cursor.close()
            conn.close()


