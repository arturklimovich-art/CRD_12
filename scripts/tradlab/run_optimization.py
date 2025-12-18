# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Grid Search оптимизация STR-100
Вариант B: 4 параметра, ~81 комбинация
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.tradlab.engine.backtester_v1 import BacktesterV1
from src.tradlab.engine.strategies.str_100_chainflow_eth import STR100ChainFlowETH
import itertools
import pandas as pd
from datetime import datetime

# Database connection
DB_URL = "postgresql://tradlab:crd12@localhost:5434/tradlab_db"

# Параметры grid search (вариант B - упрощенный)
PARAM_GRID = {
    "master_long_threshold": [10, 15, 20],
    "master_short_threshold": [-20, -15, -10],
    "lookback_z": [6, 12, 18],
    "k_sl_min": [1.0, 1.5, 2.0]
}

# Фиксированные параметры
FIXED_PARAMS = {
    "risk_per_trade": 0.01,
    "max_position_pct": 0.20,
    "k_sl_max": 3.0,
    "k_tp1": 2.0,
    "k_tp2": 4.0,
    "k_tsl": 1.0,
    "atr_expansion_multiplier": 2.0,
    "volume_collapse_multiplier": 0.3,
    "commission_rate": 0.0004,
    "slippage_bps": 5
}

# Период тестирования
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"
SYMBOL = "ETHUSDT"
INITIAL_CAPITAL = 10000.0

def run_backtest(params: dict):
    """Запуск одного бэктеста с заданными параметрами"""
    strategy = STR100ChainFlowETH(params=params)
    bt = BacktesterV1(
        db_url=DB_URL,
        strategy=strategy,
        initial_capital=INITIAL_CAPITAL,
        commission_rate=params.get("commission_rate", 0.0004),
        slippage_bps=params.get("slippage_bps", 5.0)
    )
    
    metrics = bt.run(
        symbol=SYMBOL,
        start_date=START_DATE,
        end_date=END_DATE
    )
    
    return metrics

def main():
    print("=" * 60)
    print("TradLab Grid Search Optimization - Variant B")
    print("=" * 60)
    print(f"Symbol: {SYMBOL}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"\nOptimizing parameters:")
    for key, values in PARAM_GRID.items():
        print(f"  {key}: {values}")
    
    # Генерация комбинаций
    keys = list(PARAM_GRID.keys())
    values = list(PARAM_GRID.values())
    combinations = list(itertools.product(*values))
    total = len(combinations)
    
    print(f"\nTotal combinations: {total}")
    print("=" * 60)
    
    results = []
    
    for i, combo in enumerate(combinations, 1):
        params = FIXED_PARAMS.copy()
        for key, value in zip(keys, combo):
            params[key] = value
        
        print(f"\n[{i}/{total}] Testing: long={params['master_long_threshold']}, "
              f"short={params['master_short_threshold']}, "
              f"lookback={params['lookback_z']}, sl_min={params['k_sl_min']}")
        
        try:
            metrics = run_backtest(params)
            
            if metrics is None:
                print(f"  -> ERROR: run_backtest returned None")
                continue
            
            # Преобразуем pnl_total в процент
            pnl_pct = (metrics.get("pnl_total", 0) / INITIAL_CAPITAL) * 100
            
            result = {
                **{k: params[k] for k in keys},
                "sharpe": metrics.get("sharpe", 0),
                "pnl_total": metrics.get("pnl_total", 0),
                "pnl_pct": pnl_pct,
                "max_dd": metrics.get("max_dd", 0),
                "win_rate": metrics.get("win_rate", 0),
                "total_trades": metrics.get("total_trades", 0)
            }
            results.append(result)
            
            print(f"  -> Sharpe: {result['sharpe']:.2f}, "
                  f"PnL: {result['pnl_pct']:.2f}%, "
                  f"DD: {result['max_dd']:.2f}%, "
                  f"WR: {result['win_rate']:.1f}%, "
                  f"Trades: {result['total_trades']}")
            
        except Exception as e:
            print(f"  -> ERROR: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            continue
    
    # Проверка что есть результаты
    if not results:
        print("\n" + "=" * 60)
        print("ERROR: No successful backtests!")
        print("=" * 60)
        return
    
    # Сохранение результатов
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"optimization_results_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    
    print("\n" + "=" * 60)
    print("OPTIMIZATION COMPLETE")
    print("=" * 60)
    print(f"Results saved to: {output_file}")
    print(f"Successful backtests: {len(results)}/{total}")
    
    # Топ-5 по Sharpe
    df_sorted = df.sort_values("sharpe", ascending=False)
    print("\nTop 5 by Sharpe Ratio:")
    print(df_sorted.head(5).to_string(index=False))
    
    # Лучшая комбинация
    best = df_sorted.iloc[0]
    print("\n" + "=" * 60)
    print("BEST CONFIGURATION:")
    print("=" * 60)
    for key in keys:
        print(f"  {key}: {best[key]}")
    print(f"\nMetrics:")
    print(f"  Sharpe: {best['sharpe']:.2f}")
    print(f"  PnL: {best['pnl_pct']:.2f}%")
    print(f"  PnL Total: {best['pnl_total']:.2f} USDT")
    print(f"  Max DD: {best['max_dd']:.2f}%")
    print(f"  Win Rate: {best['win_rate']:.1f}%")
    print(f"  Total Trades: {int(best['total_trades'])}")

if __name__ == "__main__":
    main()