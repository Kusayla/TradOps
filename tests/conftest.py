"""Pytest configuration and shared fixtures"""
import pytest
import os
from unittest.mock import Mock

# Set test environment variables
os.environ['TRADING_MODE'] = 'paper'
os.environ['TIMESCALEDB_HOST'] = 'localhost'
os.environ['REDIS_HOST'] = 'localhost'


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = Mock()
    settings.trading.trading_mode = 'paper'
    settings.trading.assets_list = ['BTC/USDT', 'ETH/USDT']
    settings.risk.max_position_size = 0.1
    settings.risk.max_daily_loss = 0.05
    settings.risk.max_drawdown = 0.15
    return settings


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing"""
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    df = pd.DataFrame({
        'open': np.random.uniform(40000, 42000, 100),
        'high': np.random.uniform(41000, 43000, 100),
        'low': np.random.uniform(39000, 41000, 100),
        'close': np.random.uniform(40000, 42000, 100),
        'volume': np.random.uniform(100, 1000, 100)
    }, index=dates)
    
    return df


@pytest.fixture
def sample_news():
    """Sample news data for testing"""
    return [
        {
            'source': 'test',
            'title': 'Bitcoin reaches new high',
            'description': 'BTC price surges past $50k',
            'published_at': '2024-01-01T12:00:00Z'
        },
        {
            'source': 'test',
            'title': 'Market correction expected',
            'description': 'Analysts predict short-term pullback',
            'published_at': '2024-01-01T13:00:00Z'
        }
    ]


@pytest.fixture
def sample_signal():
    """Sample trading signal for testing"""
    return {
        'symbol': 'BTC/USDT',
        'signal_type': 'BUY',
        'strength': 0.7,
        'confidence': 0.8,
        'price': 50000,
        'reasons': ['RSI oversold', 'MACD bullish'],
        'strategy': 'combined'
    }
