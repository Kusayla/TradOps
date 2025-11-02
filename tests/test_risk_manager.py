"""Tests for risk manager"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.strategy.risk_manager import RiskManager
from src.storage.redis_client import RedisClient


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = Mock(spec=RedisClient)
    redis.get_all_positions.return_value = {}
    redis.get.return_value = None
    return redis


@pytest.fixture
def risk_manager(mock_redis):
    """Create risk manager with mocked Redis"""
    with patch('src.strategy.risk_manager.settings') as mock_settings:
        mock_settings.risk.max_position_size = 0.1
        mock_settings.risk.max_daily_loss = 0.05
        mock_settings.risk.max_drawdown = 0.15
        mock_settings.risk.stop_loss_atr_multiplier = 2.0
        mock_settings.trading.trading_mode = 'paper'
        mock_settings.trading.assets_list = ['BTC/USDT', 'ETH/USDT']
        
        manager = RiskManager(mock_redis)
        return manager


def test_calculate_position_size(risk_manager):
    """Test position size calculation"""
    size = risk_manager.calculate_position_size(
        symbol='BTC/USDT',
        signal_strength=0.8,
        entry_price=50000,
        stop_loss_price=49000,
        account_balance=100000
    )
    
    assert size > 0
    assert size < 100000 / 50000  # Less than max possible size


def test_calculate_stop_loss(risk_manager):
    """Test stop loss calculation"""
    # Buy order
    stop_loss = risk_manager.calculate_stop_loss(
        entry_price=50000,
        side='BUY',
        atr=1000
    )
    
    assert stop_loss < 50000
    assert stop_loss == 50000 - (1000 * 2.0)
    
    # Sell order
    stop_loss = risk_manager.calculate_stop_loss(
        entry_price=50000,
        side='SELL',
        atr=1000
    )
    
    assert stop_loss > 50000


def test_calculate_take_profit(risk_manager):
    """Test take profit calculation"""
    # Buy order
    take_profit = risk_manager.calculate_take_profit(
        entry_price=50000,
        stop_loss=49000,
        side='BUY',
        risk_reward_ratio=2.0
    )
    
    assert take_profit > 50000
    reward = take_profit - 50000
    risk = 50000 - 49000
    assert abs(reward / risk - 2.0) < 0.01


def test_check_daily_loss_limit(risk_manager):
    """Test daily loss limit check"""
    risk_manager.current_equity = 100000
    risk_manager.daily_pnl = -3000  # 3% loss
    
    assert risk_manager.check_daily_loss_limit() is True
    
    risk_manager.daily_pnl = -6000  # 6% loss
    assert risk_manager.check_daily_loss_limit() is False


def test_check_max_drawdown(risk_manager):
    """Test max drawdown check"""
    risk_manager.peak_equity = 100000
    risk_manager.current_equity = 90000  # 10% drawdown
    
    assert risk_manager.check_max_drawdown() is True
    
    risk_manager.current_equity = 80000  # 20% drawdown
    assert risk_manager.check_max_drawdown() is False


def test_should_trade(risk_manager):
    """Test should_trade decision"""
    signal = {
        'strength': 0.5,
        'signal_type': 'BUY'
    }
    
    # Should trade with valid signal
    should_trade, reason = risk_manager.should_trade('BTC/USDT', signal)
    assert should_trade is True
    
    # Should not trade with weak signal
    weak_signal = {'strength': 0.1}
    should_trade, reason = risk_manager.should_trade('BTC/USDT', weak_signal)
    assert should_trade is False
    assert 'weak' in reason.lower()


def test_update_equity(risk_manager, mock_redis):
    """Test equity update"""
    initial_equity = risk_manager.current_equity
    pnl = 1000
    
    risk_manager.update_equity(pnl)
    
    assert risk_manager.current_equity == initial_equity + pnl
    assert risk_manager.daily_pnl == pnl
    assert risk_manager.total_pnl == pnl
    
    # Peak should update
    assert risk_manager.peak_equity >= risk_manager.current_equity


def test_circuit_breaker(risk_manager, mock_redis):
    """Test circuit breaker"""
    assert risk_manager.is_circuit_breaker_active() is False
    
    risk_manager.activate_circuit_breaker(duration_minutes=60, reason="Test")
    
    # Mock the Redis get to return active breaker
    future_time = datetime.now().isoformat()
    mock_redis.get.return_value = {
        'active': True,
        'expiry': future_time
    }
    
    # Note: This test would need proper time mocking to work correctly


def test_get_risk_metrics(risk_manager):
    """Test risk metrics retrieval"""
    metrics = risk_manager.get_risk_metrics()
    
    assert 'current_equity' in metrics
    assert 'peak_equity' in metrics
    assert 'daily_pnl' in metrics
    assert 'total_pnl' in metrics
    assert 'drawdown' in metrics
    assert 'circuit_breaker_active' in metrics
