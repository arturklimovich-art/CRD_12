#!/usr/bin/env python3
"""
TradLab Data Loader

Loads OHLCV data from Binance using OHLCVCollector.
Usage: python scripts/load_data.py --symbol ETH/USDT --start 2024-01-01
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

from tradlab.collector.ohlcv_collector_v0 import OHLCVCollector


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Load OHLCV data from Binance into PostgreSQL"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="ETH/USDT",
        help="Trading pair (default: ETH/USDT)"
    )
    parser.add_argument(
        "--timeframes",
        type=str,
        default="1h,4h",
        help="Comma-separated timeframes (default: 1h,4h)"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2024-01-01",
        help="Start date YYYY-MM-DD (default: 2024-01-01)"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse arguments first to allow --help
    args = parse_args()

    # Load environment variables
    load_dotenv()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in environment")
        print("   Please set DATABASE_URL in .env file")
        sys.exit(1)

    # Parse timeframes
    timeframes = [tf.strip() for tf in args.timeframes.split(",")]

    # Parse start date
    try:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        start_date = start_date.replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"❌ ERROR: Invalid date format: {args.start}")
        print("   Use format: YYYY-MM-DD")
        sys.exit(1)

    # Display configuration
    print("=" * 60)
    print("TradLab Data Loader")
    print("=" * 60)
    print(f"Symbol: {args.symbol}")
    print(f"Timeframes: {timeframes}")
    print(f"Start date: {start_date.strftime('%Y-%m-%d')}")
    print(f"Database: {db_url.split('@')[-1]}")
    print("=" * 60)

    # Create collector and load data
    try:
        collector = OHLCVCollector(db_url)
        collector.collect(
            symbol=args.symbol,
            timeframes=timeframes,
            start_date=start_date
        )
        print("\n✅ Data loading completed successfully!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
