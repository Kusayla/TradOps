"""Strategy execution engine"""
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from src.ml.signal_generator import SignalGenerator
from src.strategy.risk_manager import RiskManager
from src.storage.feature_store import FeatureStore
from src.storage.redis_client import RedisClient


class StrategyEngine:
    """
    Main strategy engine that combines:
    - Signal generation
    - Risk management
    - Position management
    """
    
    def __init__(self, 
                 feature_store: FeatureStore,
                 redis_client: RedisClient):
        self.feature_store = feature_store
        self.redis = redis_client
        self.signal_generator = SignalGenerator(feature_store)
        self.risk_manager = RiskManager(redis_client)
        
        self.active_positions = {}
    
    def evaluate_symbol(self, 
                       symbol: str, 
                       sentiment_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Evaluate a symbol and generate trading decision
        Returns: trading_decision dict or None
        """
        try:
            # Generate signal
            signal = self.signal_generator.generate_combined_signal(symbol, sentiment_data)
            
            logger.info(f"Signal for {symbol}: {signal['signal_type']} "
                       f"(strength: {signal['strength']:.2f})")
            
            # Check if we should trade
            should_trade, reason = self.risk_manager.should_trade(symbol, signal)
            
            if not should_trade:
                logger.info(f"Not trading {symbol}: {reason}")
                return None
            
            # Get current position
            position = self.redis.get_position(symbol)
            
            # Determine action
            action = self._determine_action(signal, position)
            
            if action == 'NONE':
                return None
            
            # Calculate position sizing and risk parameters
            decision = self._create_trading_decision(symbol, signal, action, position)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error evaluating {symbol}: {e}")
            return None
    
    def _determine_action(self, signal: Dict, position: Dict) -> str:
        """
        Determine what action to take based on signal and current position
        Returns: 'BUY', 'SELL', 'CLOSE', 'NONE'
        """
        signal_type = signal['signal_type']
        has_position = bool(position.get('size', 0))
        
        if not has_position:
            # No position - consider opening
            if signal_type == 'BUY' and signal['strength'] > 0.3:
                return 'BUY'
            elif signal_type == 'SELL' and signal['strength'] < -0.3:
                return 'SELL'
            else:
                return 'NONE'
        else:
            # Have position - consider closing or holding
            position_side = position.get('side', 'BUY')
            
            if position_side == 'BUY':
                # Long position
                if signal_type == 'SELL' and signal['strength'] < -0.4:
                    return 'CLOSE'  # Close long
                elif signal_type == 'BUY' and signal['strength'] > 0.5:
                    return 'BUY'  # Add to position (if risk allows)
            else:
                # Short position
                if signal_type == 'BUY' and signal['strength'] > 0.4:
                    return 'CLOSE'  # Close short
                elif signal_type == 'SELL' and signal['strength'] < -0.5:
                    return 'SELL'  # Add to position
        
        return 'NONE'
    
    def _create_trading_decision(self,
                                symbol: str,
                                signal: Dict,
                                action: str,
                                position: Dict) -> Dict:
        """Create a complete trading decision with risk parameters"""
        try:
            current_price = signal.get('price', 0)
            
            if action == 'CLOSE':
                # Close existing position
                return {
                    'action': 'CLOSE',
                    'symbol': symbol,
                    'side': 'SELL' if position.get('side') == 'BUY' else 'BUY',
                    'size': abs(float(position.get('size', 0))),
                    'price': current_price,
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'Signal reversal'
                }
            
            # Get ATR for stop loss calculation
            df = self.feature_store.get_feature_vector(symbol, lookback=20)
            atr = df['atr'].iloc[-1] if df is not None and 'atr' in df.columns else None
            
            # Calculate stop loss
            stop_loss = self.risk_manager.calculate_stop_loss(
                current_price, 
                action,
                atr
            )
            
            # Calculate take profit
            take_profit = self.risk_manager.calculate_take_profit(
                current_price,
                stop_loss,
                action,
                risk_reward_ratio=2.5
            )
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                symbol,
                signal['strength'],
                current_price,
                stop_loss,
                self.risk_manager.current_equity
            )
            
            # Check position limits
            if not self.risk_manager.check_position_limits(symbol, position_size):
                logger.warning(f"Position limits exceeded for {symbol}")
                return None
            
            return {
                'action': action,
                'symbol': symbol,
                'side': action,
                'size': position_size,
                'price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'signal': signal,
                'timestamp': datetime.now().isoformat(),
                'reason': ', '.join(signal.get('reasons', []))
            }
            
        except Exception as e:
            logger.error(f"Error creating trading decision: {e}")
            return None
    
    def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> Optional[str]:
        """
        Check if stop loss or take profit has been hit
        Returns: 'STOP_LOSS', 'TAKE_PROFIT', or None
        """
        position = self.redis.get_position(symbol)
        
        if not position or not position.get('size'):
            return None
        
        stop_loss = float(position.get('stop_loss', 0))
        take_profit = float(position.get('take_profit', 0))
        side = position.get('side')
        
        if side == 'BUY':
            if current_price <= stop_loss:
                return 'STOP_LOSS'
            elif current_price >= take_profit:
                return 'TAKE_PROFIT'
        else:  # SHORT
            if current_price >= stop_loss:
                return 'STOP_LOSS'
            elif current_price <= take_profit:
                return 'TAKE_PROFIT'
        
        return None
    
    def update_trailing_stop(self, symbol: str, current_price: float):
        """Update trailing stop loss"""
        position = self.redis.get_position(symbol)
        
        if not position or not position.get('size'):
            return
        
        side = position.get('side')
        entry_price = float(position.get('entry_price', 0))
        current_stop = float(position.get('stop_loss', 0))
        
        # Get ATR
        df = self.feature_store.get_feature_vector(symbol, lookback=20)
        atr = df['atr'].iloc[-1] if df is not None and 'atr' in df.columns else 0
        
        if atr == 0:
            return
        
        trail_distance = atr * self.risk_manager.config.stop_loss_atr_multiplier
        
        if side == 'BUY':
            # Update stop loss if price moved up
            new_stop = current_price - trail_distance
            if new_stop > current_stop:
                position['stop_loss'] = new_stop
                self.redis.set_position(symbol, position)
                logger.info(f"Updated trailing stop for {symbol}: {new_stop:.2f}")
        else:  # SHORT
            # Update stop loss if price moved down
            new_stop = current_price + trail_distance
            if new_stop < current_stop:
                position['stop_loss'] = new_stop
                self.redis.set_position(symbol, position)
                logger.info(f"Updated trailing stop for {symbol}: {new_stop:.2f}")
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of current portfolio"""
        positions = self.redis.get_all_positions()
        
        total_value = 0.0
        total_pnl = 0.0
        
        for symbol, position in positions.items():
            if position.get('size'):
                current_price = self.feature_store.redis.get_cached_price(symbol)
                if current_price:
                    position_value = float(position['size']) * current_price
                    entry_value = float(position['size']) * float(position['entry_price'])
                    pnl = position_value - entry_value
                    
                    total_value += position_value
                    total_pnl += pnl
        
        risk_metrics = self.risk_manager.get_risk_metrics()
        
        return {
            'total_positions': len([p for p in positions.values() if p.get('size')]),
            'total_value': total_value,
            'total_pnl': total_pnl,
            'risk_metrics': risk_metrics,
            'positions': positions
        }
