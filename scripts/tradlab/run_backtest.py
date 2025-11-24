#!/usr/bin/env python3
"""
TradLab Backtest Runner

Runs STR-100 backtest using BacktesterV1.
Usage: python scripts/tradlab/run_backtest.py --start 2024-01-01 --end 2024-12-31
"""
import argparse
import os
import re
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv

from tradlab.engine.backtester_v1 import BacktesterV1
from tradlab.engine.strategies.str_100_chainflow_eth import STR100ChainFlowETH


def mask_db_url(db_url: str) -> str:
    """Mask password in database URL for safe logging."""
    return re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', db_url)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run STR-100 backtest on historical data"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="ETHUSDT",
        help="Trading pair (default: ETHUSDT)"
    )
    parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="Start date YYYY-MM-DD"
    )
    parser.add_argument(
        "--end",
        type=str,
        required=True,
        help="End date YYYY-MM-DD"
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=None,
        help="Initial capital (default: from .env.tradlab or 10000)"
    )
    return parser.parse_args()


def display_results(results: dict):
    """Display backtest results in a formatted way."""
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)

    print(f"\n📊 Strategy: {results['strategy_id']}")
    print(f"📅 Period: {results['start_ts']} to {results['end_ts']}")
    print(f"💰 Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"💵 Final Capital: ${results['final_capital']:,.2f}")

    print("\n" + "-" * 40)
    print("PERFORMANCE METRICS")
    print("-" * 40)

    pnl = results["pnl_total"]
    pnl_pct = (pnl / results["initial_capital"]) * 100
    print(f"📈 Total PnL: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
    print(f"📊 Sharpe Ratio: {results['sharpe']:.2f}")
    print(f"📊 Sortino Ratio: {results['sortino']:.2f}")
    print(f"📉 Max Drawdown: {results['max_dd']:.2f}%")
    print(f"📊 Calmar Ratio: {results['calmar']:.2f}")

    print("\n" + "-" * 40)
    print("TRADE STATISTICS")
    print("-" * 40)

    print(f"🔢 Total Trades: {results['total_trades']}")
    print(f"🎯 Win Rate: {results['win_rate']:.2f}%")
    print(f"⚖️  Profit Factor: {results['profit_factor']:.2f}")

    print("\n" + "-" * 40)
    print("RISK GATE STATUS")
    print("-" * 40)

    if results["pass_risk_gate"]:
        print("✅ PASS - Strategy meets risk criteria")
        print("   • Sharpe >= 1.0: ✅")
        print("   • MaxDD <= 20%: ✅")
        print("   • Win Rate >= 40%: ✅")
    else:
        print("❌ FAIL - Strategy does not meet risk criteria")
        if results["sharpe"] < 1.0:
            print(f"   • Sharpe >= 1.0: ❌ (got {results['sharpe']:.2f})")
        else:
            print("   • Sharpe >= 1.0: ✅")
        if results["max_dd"] > 20.0:
            print(f"   • MaxDD <= 20%: ❌ (got {results['max_dd']:.2f}%)")
        else:
            print("   • MaxDD <= 20%: ✅")
        if results["win_rate"] < 40.0:
            print(f"   • Win Rate >= 40%: ❌ (got {results['win_rate']:.2f}%)")
        else:
            print("   • Win Rate >= 40%: ✅")

    print("\n" + "=" * 60)
    print(f"Run ID: {results['run_id']}")
    print("=" * 60)


def main():
    """Main entry point."""
    # Parse arguments first to allow --help
    args = parse_args()

    # Load environment variables
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env.tradlab")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in environment")
        print("   Please set DATABASE_URL in .env.tradlab file")
        sys.exit(1)

    # Get capital from args or environment
    if args.capital is not None:
        initial_capital = args.capital
    else:
        initial_capital = float(os.getenv("TRADLAB_INITIAL_CAPITAL", "10000"))

    commission_rate = float(os.getenv("TRADLAB_COMMISSION_RATE", "0.0004"))
    slippage_bps = float(os.getenv("TRADLAB_SLIPPAGE_BPS", "5"))

    # Display configuration
    print("=" * 60)
    print("TradLab Backtest Runner")
    print("=" * 60)
    print(f"Symbol: {args.symbol}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Commission Rate: {commission_rate * 100:.4f}%")
    print(f"Slippage: {slippage_bps} bps")
    print(f"Database: {mask_db_url(db_url)}")
    print("=" * 60)

    # Create strategy and backtester
    try:
        strategy = STR100ChainFlowETH()

        backtester = BacktesterV1(
            db_url=db_url,
            strategy=strategy,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_bps=slippage_bps
        )

        # Run backtest
        results = backtester.run(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end
        )

        # Display results
        display_results(results)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
