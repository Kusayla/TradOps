"""Backtesting engine for strategy validation"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

import vectorbt as vbt


class BacktestEngine:
    """
    Backtest trading strategies using vectorbt
    Features:
    - Vectorized backtesting for speed
    - Multiple metrics (Sharpe, Sortino, Drawdown, etc.)
    - Walk-forward analysis
    - Transaction costs and slippage
    """
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 commission: float = 0.001,  # 0.1%
                 slippage: float = 0.001):  # 0.1%
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
    
    def run_backtest(self,
                    price_data: pd.DataFrame,
                    signals: pd.DataFrame,
                    symbol: str) -> Dict:
        """
        Run backtest on price data with signals
        
        Args:
            price_data: DataFrame with OHLCV data
            signals: DataFrame with entry/exit signals
            symbol: Trading pair symbol
        
        Returns:
            Dictionary with backtest results
        """
        try:
            logger.info(f"Running backtest for {symbol}")
            
            # Align signals with price data
            if not signals.index.equals(price_data.index):
                signals = signals.reindex(price_data.index, fill_value=0)
            
            # Create portfolio
            portfolio = vbt.Portfolio.from_signals(
                close=price_data['close'],
                entries=signals['entry'],
                exits=signals['exit'],
                init_cash=self.initial_capital,
                fees=self.commission,
                slippage=self.slippage,
                freq='1h'
            )
            
            # Calculate metrics
            metrics = self._calculate_metrics(portfolio, price_data)
            
            # Get trades
            trades = self._extract_trades(portfolio)
            
            results = {
                'symbol': symbol,
                'start_date': price_data.index[0].isoformat(),
                'end_date': price_data.index[-1].isoformat(),
                'initial_capital': self.initial_capital,
                'final_value': portfolio.final_value(),
                'total_return': portfolio.total_return(),
                'metrics': metrics,
                'trades': trades,
                'equity_curve': portfolio.value().to_dict()
            }
            
            logger.info(f"Backtest complete. Total return: {metrics['total_return']:.2%}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {}
    
    def _calculate_metrics(self, portfolio, price_data: pd.DataFrame) -> Dict:
        """Calculate performance metrics"""
        try:
            stats = portfolio.stats()
            
            metrics = {
                'total_return': portfolio.total_return(),
                'annualized_return': portfolio.annualized_return(),
                'sharpe_ratio': portfolio.sharpe_ratio(),
                'sortino_ratio': portfolio.sortino_ratio(),
                'max_drawdown': portfolio.max_drawdown(),
                'calmar_ratio': portfolio.calmar_ratio(),
                'win_rate': portfolio.trades.win_rate(),
                'profit_factor': portfolio.trades.profit_factor(),
                'total_trades': portfolio.trades.count(),
                'avg_trade_duration': str(portfolio.trades.duration.mean()),
                'avg_win': portfolio.trades.winning.pnl.mean(),
                'avg_loss': portfolio.trades.losing.pnl.mean(),
            }
            
            # Buy and hold comparison
            buy_hold_return = (price_data['close'].iloc[-1] / price_data['close'].iloc[0]) - 1
            metrics['buy_hold_return'] = buy_hold_return
            metrics['excess_return'] = metrics['total_return'] - buy_hold_return
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {}
    
    def _extract_trades(self, portfolio) -> List[Dict]:
        """Extract individual trades"""
        try:
            trades_df = portfolio.trades.records_readable
            
            if trades_df.empty:
                return []
            
            trades = []
            for _, trade in trades_df.iterrows():
                trades.append({
                    'entry_time': trade['Entry Time'].isoformat(),
                    'exit_time': trade['Exit Time'].isoformat(),
                    'entry_price': float(trade['Entry Price']),
                    'exit_price': float(trade['Exit Price']),
                    'size': float(trade['Size']),
                    'pnl': float(trade['PnL']),
                    'return': float(trade['Return']),
                    'duration': str(trade['Duration'])
                })
            
            return trades
            
        except Exception as e:
            logger.error(f"Error extracting trades: {e}")
            return []
    
    def run_walk_forward(self,
                        price_data: pd.DataFrame,
                        signals: pd.DataFrame,
                        train_period: int = 90,  # days
                        test_period: int = 30,  # days
                        symbol: str = "") -> Dict:
        """
        Run walk-forward analysis
        Train on train_period, test on test_period, then roll forward
        """
        try:
            logger.info(f"Running walk-forward analysis for {symbol}")
            
            results = []
            current_date = price_data.index[0]
            end_date = price_data.index[-1]
            
            while current_date < end_date:
                # Define train and test windows
                train_end = current_date + timedelta(days=train_period)
                test_end = train_end + timedelta(days=test_period)
                
                if test_end > end_date:
                    break
                
                # Get train and test data
                train_data = price_data[current_date:train_end]
                test_data = price_data[train_end:test_end]
                test_signals = signals[train_end:test_end]
                
                if len(test_data) < 10:
                    break
                
                # Run backtest on test period
                test_result = self.run_backtest(test_data, test_signals, symbol)
                
                results.append({
                    'period_start': train_end.isoformat(),
                    'period_end': test_end.isoformat(),
                    'return': test_result['metrics'].get('total_return', 0),
                    'sharpe': test_result['metrics'].get('sharpe_ratio', 0),
                    'max_dd': test_result['metrics'].get('max_drawdown', 0),
                })
                
                # Roll forward
                current_date = test_end
            
            # Aggregate results
            if results:
                avg_return = np.mean([r['return'] for r in results])
                avg_sharpe = np.mean([r['sharpe'] for r in results if r['sharpe']])
                worst_dd = min([r['max_dd'] for r in results])
                
                summary = {
                    'symbol': symbol,
                    'num_periods': len(results),
                    'avg_return_per_period': avg_return,
                    'avg_sharpe': avg_sharpe,
                    'worst_drawdown': worst_dd,
                    'periods': results
                }
                
                logger.info(f"Walk-forward complete: {len(results)} periods, "
                          f"avg return: {avg_return:.2%}")
                
                return summary
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in walk-forward analysis: {e}")
            return {}
    
    def optimize_parameters(self,
                           price_data: pd.DataFrame,
                           param_grid: Dict,
                           signal_generator_func,
                           symbol: str) -> Dict:
        """
        Optimize strategy parameters using grid search
        
        Args:
            price_data: OHLCV data
            param_grid: Dictionary of parameters to test
            signal_generator_func: Function that generates signals given parameters
            symbol: Trading pair
        
        Returns:
            Best parameters and results
        """
        try:
            logger.info(f"Optimizing parameters for {symbol}")
            
            best_result = None
            best_params = None
            best_sharpe = -np.inf
            
            # Generate parameter combinations
            import itertools
            keys = param_grid.keys()
            values = param_grid.values()
            
            for combination in itertools.product(*values):
                params = dict(zip(keys, combination))
                
                # Generate signals with these parameters
                signals = signal_generator_func(price_data, params)
                
                # Run backtest
                result = self.run_backtest(price_data, signals, symbol)
                
                sharpe = result['metrics'].get('sharpe_ratio', -np.inf)
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = params
                    best_result = result
            
            logger.info(f"Optimization complete. Best Sharpe: {best_sharpe:.2f}")
            logger.info(f"Best params: {best_params}")
            
            return {
                'best_params': best_params,
                'best_sharpe': best_sharpe,
                'best_result': best_result
            }
            
        except Exception as e:
            logger.error(f"Error optimizing parameters: {e}")
            return {}


def generate_signals_from_strategy(df: pd.DataFrame, strategy_func) -> pd.DataFrame:
    """
    Helper function to generate entry/exit signals from a strategy
    
    Args:
        df: DataFrame with OHLCV and indicators
        strategy_func: Function that returns (entry_signals, exit_signals)
    
    Returns:
        DataFrame with 'entry' and 'exit' columns
    """
    entry_signals, exit_signals = strategy_func(df)
    
    signals = pd.DataFrame(index=df.index)
    signals['entry'] = entry_signals
    signals['exit'] = exit_signals
    
    return signals
