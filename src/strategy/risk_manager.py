"""Risk management system"""
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from loguru import logger

from src.config import settings
from src.storage.redis_client import RedisClient


class RiskManager:
    """
    Comprehensive risk management for trading
    - Position sizing
    - Stop loss / Take profit
    - Max drawdown monitoring
    - Circuit breakers
    """
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.config = settings.risk
        self.trading_config = settings.trading
        
        # Risk metrics
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.peak_equity = 100000.0  # Starting capital
        self.current_equity = 100000.0
        
    def calculate_position_size(self, 
                               symbol: str, 
                               signal_strength: float,
                               entry_price: float,
                               stop_loss_price: float,
                               account_balance: float) -> float:
        """
        Calculate optimal position size based on risk parameters
        Uses ATR-based position sizing
        """
        try:
            # Maximum risk per trade
            max_risk_per_trade = account_balance * self.config.max_position_size
            
            # Calculate risk per unit
            risk_per_unit = abs(entry_price - stop_loss_price)
            
            if risk_per_unit == 0:
                logger.warning(f"Invalid risk per unit for {symbol}")
                return 0.0
            
            # Base position size
            position_size = max_risk_per_trade / risk_per_unit
            
            # Adjust by signal strength (0.5 to 1.0 multiplier)
            strength_multiplier = 0.5 + (abs(signal_strength) * 0.5)
            position_size *= strength_multiplier
            
            # Apply maximum position size constraint
            max_position_value = account_balance * self.config.max_position_size
            max_position_units = max_position_value / entry_price
            
            position_size = min(position_size, max_position_units)
            
            logger.info(f"Calculated position size for {symbol}: {position_size:.4f} units")
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def calculate_stop_loss(self, 
                           entry_price: float, 
                           side: str,
                           atr: Optional[float] = None) -> float:
        """
        Calculate stop loss price based on ATR
        """
        if atr is None:
            # Use default percentage
            stop_distance = entry_price * 0.02  # 2% default
        else:
            stop_distance = atr * self.config.stop_loss_atr_multiplier
        
        if side.upper() == 'BUY':
            stop_loss = entry_price - stop_distance
        else:  # SELL
            stop_loss = entry_price + stop_distance
        
        return stop_loss
    
    def calculate_take_profit(self,
                             entry_price: float,
                             stop_loss: float,
                             side: str,
                             risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take profit based on risk/reward ratio
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        if side.upper() == 'BUY':
            take_profit = entry_price + reward
        else:  # SELL
            take_profit = entry_price - reward
        
        return take_profit
    
    def check_position_limits(self, symbol: str, proposed_size: float) -> bool:
        """Check if position is within risk limits"""
        try:
            # Get current positions
            positions = self.redis.get_all_positions()
            
            # Check total exposure
            total_exposure = sum(
                float(pos.get('size', 0)) * float(pos.get('entry_price', 0))
                for pos in positions.values()
            )
            
            # Check if new position would exceed limits
            if total_exposure / self.current_equity > 0.8:  # Max 80% exposure
                logger.warning(f"Total exposure too high: {total_exposure / self.current_equity:.2%}")
                return False
            
            # Check individual position limit
            existing_position = positions.get(symbol, {})
            current_size = float(existing_position.get('size', 0))
            
            if abs(current_size + proposed_size) > self.config.max_position_size * self.current_equity:
                logger.warning(f"Position size too large for {symbol}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking position limits: {e}")
            return False
    
    def check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been reached"""
        max_daily_loss = self.current_equity * self.config.max_daily_loss
        
        if self.daily_pnl < -max_daily_loss:
            logger.warning(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
            return False
        
        return True
    
    def check_max_drawdown(self) -> bool:
        """Check if maximum drawdown has been exceeded"""
        current_drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
        
        if current_drawdown > self.config.max_drawdown:
            logger.error(f"Max drawdown exceeded: {current_drawdown:.2%}")
            return False
        
        return True
    
    def update_equity(self, pnl: float):
        """Update equity after trade"""
        self.current_equity += pnl
        self.daily_pnl += pnl
        self.total_pnl += pnl
        
        # Update peak equity
        if self.current_equity > self.peak_equity:
            self.peak_equity = self.current_equity
        
        # Store in Redis
        self.redis.set('equity', {
            'current': self.current_equity,
            'peak': self.peak_equity,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'timestamp': datetime.now().isoformat()
        })
    
    def should_trade(self, symbol: str, signal: Dict) -> tuple[bool, str]:
        """
        Master check: determine if trade should be executed
        Returns: (should_trade, reason)
        """
        # Check if trading mode is live
        if self.trading_config.trading_mode != 'live':
            if self.trading_config.trading_mode == 'paper':
                return True, "Paper trading mode"
            else:
                return False, "Trading disabled"
        
        # Check asset whitelist
        if symbol not in self.trading_config.assets_list:
            return False, f"{symbol} not in whitelist"
        
        # Check signal strength
        if abs(signal.get('strength', 0)) < 0.3:
            return False, "Signal too weak"
        
        # Check daily loss limit
        if not self.check_daily_loss_limit():
            return False, "Daily loss limit reached"
        
        # Check max drawdown
        if not self.check_max_drawdown():
            return False, "Max drawdown exceeded"
        
        # Check circuit breaker
        if self.is_circuit_breaker_active():
            return False, "Circuit breaker active"
        
        return True, "All risk checks passed"
    
    def is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is active"""
        breaker = self.redis.get('circuit_breaker')
        if breaker:
            expiry = datetime.fromisoformat(breaker.get('expiry', datetime.now().isoformat()))
            if datetime.now() < expiry:
                return True
        return False
    
    def activate_circuit_breaker(self, duration_minutes: int = 60, reason: str = ""):
        """Activate circuit breaker to pause trading"""
        expiry = datetime.now() + timedelta(minutes=duration_minutes)
        self.redis.set('circuit_breaker', {
            'active': True,
            'reason': reason,
            'expiry': expiry.isoformat()
        })
        logger.warning(f"Circuit breaker activated: {reason}")
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
        
        return {
            'current_equity': self.current_equity,
            'peak_equity': self.peak_equity,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'drawdown': drawdown,
            'daily_loss_limit': self.config.max_daily_loss,
            'max_drawdown_limit': self.config.max_drawdown,
            'circuit_breaker_active': self.is_circuit_breaker_active()
        }
