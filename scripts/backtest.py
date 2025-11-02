#!/usr/bin/env python3
"""
Backtesting script
Run backtests on historical data to validate strategies
"""
import sys
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

# Add src to path
sys.path.insert(0, '/workspace')

from src.config import settings
from src.data_ingestion.market_data import MarketDataIngestion
from src.storage.feature_store import FeatureStore
from src.backtesting.backtest_engine import BacktestEngine, generate_signals_from_strategy
from src.ml.signal_generator import SignalGenerator


async def fetch_historical_data(symbol: str, days: int = 90):
    """Fetch historical data for backtesting"""
    logger.info(f"Fetching historical data for {symbol} ({days} days)")
    
    market_data = MarketDataIngestion()
    await market_data.initialize()
    
    # Fetch OHLCV data
    ohlcv = await market_data.fetch_ohlcv(symbol, '1h', limit=days*24)
    
    await market_data.close()
    
    if not ohlcv:
        logger.error(f"No data fetched for {symbol}")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(ohlcv)
    df.set_index('datetime', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    logger.info(f"Fetched {len(df)} candles")
    return df


def generate_strategy_signals(df: pd.DataFrame):
    """
    Generate trading signals from strategy
    Returns DataFrame with 'entry' and 'exit' boolean columns
    """
    # Compute technical indicators
    feature_store = FeatureStore()
    feature_store.initialize()
    df = feature_store.compute_technical_features(df)
    
    # Generate signals based on indicators
    entry_signals = pd.Series(False, index=df.index)
    exit_signals = pd.Series(False, index=df.index)
    
    # Example strategy: RSI + MACD crossover
    for i in range(1, len(df)):
        # Entry: RSI oversold + MACD bullish crossover
        if (df['rsi'].iloc[i] < 35 and 
            df['macd'].iloc[i] > df['macd_signal'].iloc[i] and
            df['macd'].iloc[i-1] <= df['macd_signal'].iloc[i-1]):
            entry_signals.iloc[i] = True
        
        # Exit: RSI overbought or MACD bearish crossover
        if (df['rsi'].iloc[i] > 70 or
            (df['macd'].iloc[i] < df['macd_signal'].iloc[i] and
             df['macd'].iloc[i-1] >= df['macd_signal'].iloc[i-1])):
            exit_signals.iloc[i] = True
    
    signals = pd.DataFrame(index=df.index)
    signals['entry'] = entry_signals
    signals['exit'] = exit_signals
    
    return signals


async def run_backtest(symbol: str, days: int = 90):
    """Run backtest for a symbol"""
    logger.info(f"Running backtest for {symbol}")
    
    # Fetch data
    df = await fetch_historical_data(symbol, days)
    
    if df is None or df.empty:
        logger.error("No data available for backtesting")
        return
    
    # Generate signals
    signals = generate_strategy_signals(df)
    
    # Run backtest
    backtest_engine = BacktestEngine(
        initial_capital=100000.0,
        commission=0.001,  # 0.1%
        slippage=0.001
    )
    
    results = backtest_engine.run_backtest(df, signals, symbol)
    
    # Print results
    print("\n" + "="*60)
    print(f"BACKTEST RESULTS: {symbol}")
    print("="*60)
    print(f"Period: {results['start_date']} to {results['end_date']}")
    print(f"Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"Final Value: ${results['final_value']:,.2f}")
    print(f"\nPerformance Metrics:")
    metrics = results['metrics']
    print(f"  Total Return: {metrics['total_return']:.2%}")
    print(f"  Annual Return: {metrics['annualized_return']:.2%}")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"  Win Rate: {metrics['win_rate']:.2%}")
    print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"\nBuy & Hold Return: {metrics['buy_hold_return']:.2%}")
    print(f"Excess Return: {metrics['excess_return']:.2%}")
    print("="*60)
    
    # Show sample trades
    if results['trades']:
        print("\nSample Trades (first 5):")
        for i, trade in enumerate(results['trades'][:5]):
            print(f"  {i+1}. Entry: {trade['entry_price']:.2f} @ {trade['entry_time']} | "
                  f"Exit: {trade['exit_price']:.2f} @ {trade['exit_time']} | "
                  f"PnL: ${trade['pnl']:.2f} ({trade['return']:.2%})")
    
    print("")


async def main():
    """Main entry point"""
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    # Symbols to backtest
    symbols = settings.trading.assets_list
    
    print("\n" + "="*60)
    print("CRYPTO TRADING BOT - BACKTESTING")
    print("="*60)
    
    for symbol in symbols:
        await run_backtest(symbol, days=90)
        print("\n")


if __name__ == "__main__":
    asyncio.run(main())
