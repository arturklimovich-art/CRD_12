# -*- coding: utf-8 -*-
"""
TradLab Multi-Period Grid Search Optimization
Оптимизация STR-100 на разных рыночных режимах
"""
import sys
from pathlib import Path

# Добавить src в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import psycopg2
import pandas as pd
from datetime import datetime
from itertools import product
from tradlab.engine.backtester_v1 import BacktesterV1
from tradlab.engine.strategies.str_100_chainflow_eth import STR100ChainFlowETH

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'tradlab_db',
    'user': 'tradlab',
    'password': 'crd12'
}

# Тестовые периоды (3 рыночных режима)
TEST_PERIODS = {
    'bull': {
        'name': 'БЫЧИЙ (Feb-Mar 2024)',
        'start': '2024-02-01',
        'end': '2024-03-31',
        'description': 'ETF approval pump: $2257 -> $4065 (+80%)'
    },
    'bear': {
        'name': 'МЕДВЕЖИЙ (Jul-Sep 2024)',
        'start': '2024-07-01',
        'end': '2024-09-30',
        'description': 'Коррекция: $3536 -> $2223 (-37%)'
    },
    'sideways': {
        'name': 'БОКОВИК (Oct 2024)',
        'start': '2024-10-01',
        'end': '2024-10-31',
        'description': 'Консолидация: $2341 -> $2747 (±8%)'
    }
}

# Grid параметров (расширенный)
PARAM_GRID = {
    'master_long_threshold': [5, 10, 15, 20],
    'master_short_threshold': [-25, -20, -15, -10],
    'lookback_z': [6, 12, 18],
    'k_sl_min': [1.5, 2.0, 2.5],
}

# Фиксированные параметры (из PARAMS стратегии)
FIXED_PARAMS = {
    # Risk Management
    'risk_per_trade': 0.01,
    'max_position_pct': 0.20,
    
    # Stop-Loss / Take-Profit (НЕ оптимизируемые)
    'k_sl_max': 3.0,
    'k_tp1': 2.0,
    'k_tp2': 4.0,
    'k_tsl': 1.0,
    
    # Veto Filters
    'atr_expansion_multiplier': 2.0,
    'volume_collapse_multiplier': 0.3,
    
    # Costs
    'commission_rate': 0.0004,
    'slippage_bps': 5,
}

BACKTEST_CONFIG = {
    'initial_capital': 10000,
    # commission_rate и slippage_bps будут взяты из FIXED_PARAMS и переданы в BacktesterV1,
    # но оставляем здесь, чтобы показать базовую конфигурацию бэктестера,
    # хотя в BacktesterV1 они часто переопределяются параметрами стратегии.
    'commission_rate': 0.0004,
    'slippage_bps': 5,
}


def get_db_url(db_config: dict) -> str:
    """Формирует строку подключения к БД из словаря конфигурации."""
    return f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

DB_URL = get_db_url(DB_CONFIG)

def run_optimization_for_period(period_key: str, period_config: dict):
    """
    Запуск оптимизации для одного периода
    """
    print("\n" + "=" * 80)
    print(f"ПЕРИОД: {period_config['name']}")
    print("=" * 80)
    print(f"Даты: {period_config['start']} → {period_config['end']}")
    print(f"Описание: {period_config['description']}")
    print("=" * 80)
    
    # Генерация комбинаций
    param_names = list(PARAM_GRID.keys())
    param_values = list(PARAM_GRID.values())
    combinations = list(product(*param_values))
    total = len(combinations)
    
    print(f"\nВсего комбинаций: {total}")
    
    results = []
    
    for idx, params in enumerate(combinations, 1):
        param_dict = dict(zip(param_names, params))
        
        if idx % 10 == 1 or idx == total:
            print(f"[{idx}/{total}] {param_dict}")
        
        # Создать стратегию 
        # Объединить параметры в один словарь
        all_params = {**param_dict, **FIXED_PARAMS}
        strategy = STR100ChainFlowETH(strategy_id="STR-100", params=all_params)
        
        # Запустить бэктест
        # Используем commission_rate/slippage_bps из all_params, если BacktesterV1 может их принять
        # В BacktesterV1 они передаются через **BACKTEST_CONFIG
        backtester = BacktesterV1(
            db_url=DB_URL,  # Передаем DB_URL, который требует BacktesterV1
            strategy=strategy,
            **BACKTEST_CONFIG
        )
        
        try:
            result = backtester.run(
                symbol='ETHUSDT',
                start_date=period_config['start'],
                end_date=period_config['end']
            )
            
            pnl_total = result.get('pnl_total', 0)
            
            results.append({
                **param_dict,
                'sharpe': result.get('sharpe', 0),
                'pnl_total': pnl_total,
                'pnl_pct': (pnl_total / BACKTEST_CONFIG['initial_capital']) * 100, 
                'max_dd': result.get('max_dd', 0),
                'win_rate': result.get('win_rate', 0),
                'total_trades': result.get('total_trades', 0),
                'profit_factor': result.get('profit_factor', 0)
            })
            
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            continue
    
    # Сохранить результаты
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('sharpe', ascending=False)
        
        filename = f"optimization_{period_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\n✅ Результаты сохранены: {filename}")
        print(f"Успешных бэктестов: {len(results)}/{total}")
        
        # ТОП-3
        print(f"\n🏆 ТОП-3 для {period_config['name']}:\n")
        # .head(3) вернет DataFrame. i+1 для нумерации
        for i, row in df.head(3).iterrows():
            print(f"{i+1}. Sharpe={row['sharpe']:.3f}, PnL={row['pnl_pct']:.2f}%, WR={row['win_rate']:.1f}%")
            print(f"    long_th={row['master_long_threshold']}, short_th={row['master_short_threshold']}, "
                  f"lookback={row['lookback_z']}, sl_min={row['k_sl_min']}")
        
        return df
    else:
        print("❌ Нет успешных результатов!")
        return None


def compare_periods(results_dict: dict):
    """
    Сравнение результатов по периодам
    """
    print("\n" + "=" * 80)
    print("СРАВНЕНИЕ ПЕРИОДОВ")
    print("=" * 80)
    
    summary = []
    
    for period_key, df in results_dict.items():
        if df is not None and not df.empty:
            best = df.iloc[0]
            period_name = TEST_PERIODS[period_key]['name']
            
            summary.append({
                'period': period_name,
                'best_sharpe': best['sharpe'],
                'best_pnl_pct': best['pnl_pct'],
                'best_win_rate': best['win_rate'],
                'master_long_threshold': best['master_long_threshold'],
                'master_short_threshold': best['master_short_threshold'],
                'lookback_z': best['lookback_z'],
                'k_sl_min': best['k_sl_min']
            })
    
    if summary:
        summary_df = pd.DataFrame(summary)
        print("\n")
        print(summary_df.to_string(index=False))
        
        # Сохранить сводку
        summary_df.to_csv(f"optimization_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
        
        # Найти универсальные параметры (средние метрики)
        print("\n" + "=" * 80)
        print("РЕКОМЕНДАЦИЯ: Универсальные параметры")
        print("=" * 80)
        
        avg_long = summary_df['master_long_threshold'].mean()
        avg_short = summary_df['master_short_threshold'].mean()
        avg_lookback = summary_df['lookback_z'].mean()
        avg_sl = summary_df['k_sl_min'].mean()
        
        print(f"master_long_threshold: {avg_long:.1f}")
        print(f"master_short_threshold: {avg_short:.1f}")
        print(f"lookback_z: {avg_lookback:.1f}")
        print(f"k_sl_min: {avg_sl:.2f}")
        
        print(f"\nСредний Sharpe: {summary_df['best_sharpe'].mean():.3f}")
        print(f"Средний PnL: {summary_df['best_pnl_pct'].mean():.2f}%")


def main():
    """
    Основная функция
    """
    print("=" * 80)
    print("МУЛЬТИПЕРИОДНАЯ ОПТИМИЗАЦИЯ STR-100")
    print("=" * 80)
    # Вычисляем общее количество комбинаций
    total_combinations = len(list(product(*PARAM_GRID.values())))
    print(f"Периодов для тестирования: {len(TEST_PERIODS)}")
    print(f"Комбинаций параметров: {total_combinations}")
    print("=" * 80)
    
    results_dict = {}
    
    # Запустить оптимизацию для каждого периода
    for period_key, period_config in TEST_PERIODS.items():
        df = run_optimization_for_period(period_key, period_config)
        results_dict[period_key] = df
    
    # Сравнить результаты
    compare_periods(results_dict)
    
    print("\n" + "=" * 80)
    print("✅ МУЛЬТИПЕРИОДНАЯ ОПТИМИЗАЦИЯ ЗАВЕРШЕНА")
    print("=" * 80)


if __name__ == "__main__":
    main()