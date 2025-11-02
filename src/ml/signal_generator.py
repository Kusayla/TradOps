"""Generate trading signals from features and ML models"""
import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime
from loguru import logger

from src.storage.feature_store import FeatureStore


class SignalGenerator:
    """Generate trading signals using multiple strategies"""
    
    def __init__(self, feature_store: FeatureStore):
        self.feature_store = feature_store
    
    def generate_technical_signal(self, symbol: str) -> Dict:
        """Generate signal based on technical indicators"""
        try:
            df = self.feature_store.get_feature_vector(symbol, lookback=200)
            
            if df is None or len(df) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return self._neutral_signal(symbol)
            
            # Get latest values
            latest = df.iloc[-1]
            
            signal_strength = 0.0
            reasons = []
            
            # RSI signals
            if 'rsi' in latest:
                rsi = latest['rsi']
                if rsi < 30:
                    signal_strength += 0.3
                    reasons.append("RSI oversold")
                elif rsi > 70:
                    signal_strength -= 0.3
                    reasons.append("RSI overbought")
            
            # MACD signals
            if 'macd' in latest and 'macd_signal' in latest:
                macd = latest['macd']
                macd_signal = latest['macd_signal']
                
                if macd > macd_signal:
                    signal_strength += 0.2
                    reasons.append("MACD bullish")
                else:
                    signal_strength -= 0.2
                    reasons.append("MACD bearish")
            
            # Moving average crossover
            if 'sma_20' in latest and 'sma_50' in latest:
                sma_20 = latest['sma_20']
                sma_50 = latest['sma_50']
                
                if sma_20 > sma_50:
                    signal_strength += 0.2
                    reasons.append("MA bullish crossover")
                elif sma_20 < sma_50:
                    signal_strength -= 0.2
                    reasons.append("MA bearish crossover")
            
            # Bollinger Bands
            if all(k in latest for k in ['close', 'bb_lower', 'bb_upper']):
                close = latest['close']
                bb_lower = latest['bb_lower']
                bb_upper = latest['bb_upper']
                
                if close < bb_lower:
                    signal_strength += 0.15
                    reasons.append("Price below BB lower")
                elif close > bb_upper:
                    signal_strength -= 0.15
                    reasons.append("Price above BB upper")
            
            # Trend strength (ADX)
            if 'adx' in latest:
                adx = latest['adx']
                if adx > 25:
                    # Strong trend - amplify signal
                    signal_strength *= 1.2
                    reasons.append("Strong trend (ADX)")
            
            # Normalize signal strength to [-1, 1]
            signal_strength = np.clip(signal_strength, -1, 1)
            
            # Determine signal type
            if signal_strength > 0.3:
                signal_type = 'BUY'
            elif signal_strength < -0.3:
                signal_type = 'SELL'
            else:
                signal_type = 'HOLD'
            
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'strength': signal_strength,
                'confidence': abs(signal_strength),
                'reasons': reasons,
                'price': latest['close'],
                'timestamp': datetime.now().isoformat(),
                'strategy': 'technical'
            }
            
        except Exception as e:
            logger.error(f"Error generating technical signal for {symbol}: {e}")
            return self._neutral_signal(symbol)
    
    def generate_sentiment_signal(self, symbol: str, sentiment_data: Dict) -> Dict:
        """Generate signal based on sentiment analysis"""
        try:
            avg_sentiment = sentiment_data.get('avg_sentiment', 0.0)
            confidence = sentiment_data.get('avg_confidence', 0.0)
            sentiment_ratio = sentiment_data.get('sentiment_ratio', 0.0)
            
            # Convert sentiment to signal
            signal_strength = avg_sentiment * confidence
            
            # Amplify if strong consensus
            if abs(sentiment_ratio) > 0.5:
                signal_strength *= 1.3
            
            signal_strength = np.clip(signal_strength, -1, 1)
            
            if signal_strength > 0.3:
                signal_type = 'BUY'
            elif signal_strength < -0.3:
                signal_type = 'SELL'
            else:
                signal_type = 'HOLD'
            
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'strength': signal_strength,
                'confidence': confidence,
                'sentiment_data': sentiment_data,
                'timestamp': datetime.now().isoformat(),
                'strategy': 'sentiment'
            }
            
        except Exception as e:
            logger.error(f"Error generating sentiment signal for {symbol}: {e}")
            return self._neutral_signal(symbol)
    
    def generate_combined_signal(self, symbol: str, sentiment_data: Optional[Dict] = None) -> Dict:
        """Combine technical and sentiment signals"""
        try:
            # Get technical signal
            tech_signal = self.generate_technical_signal(symbol)
            
            if sentiment_data:
                # Get sentiment signal
                sent_signal = self.generate_sentiment_signal(symbol, sentiment_data)
                
                # Weighted combination (60% technical, 40% sentiment)
                combined_strength = (0.6 * tech_signal['strength'] + 
                                   0.4 * sent_signal['strength'])
                
                combined_confidence = (tech_signal['confidence'] + 
                                     sent_signal['confidence']) / 2
                
                if combined_strength > 0.3:
                    signal_type = 'BUY'
                elif combined_strength < -0.3:
                    signal_type = 'SELL'
                else:
                    signal_type = 'HOLD'
                
                return {
                    'symbol': symbol,
                    'signal_type': signal_type,
                    'strength': combined_strength,
                    'confidence': combined_confidence,
                    'technical_signal': tech_signal,
                    'sentiment_signal': sent_signal,
                    'price': tech_signal['price'],
                    'timestamp': datetime.now().isoformat(),
                    'strategy': 'combined'
                }
            else:
                # Return technical signal only
                return tech_signal
                
        except Exception as e:
            logger.error(f"Error generating combined signal for {symbol}: {e}")
            return self._neutral_signal(symbol)
    
    def detect_breakout(self, symbol: str, lookback: int = 20) -> Optional[Dict]:
        """Detect price breakouts"""
        try:
            df = self.feature_store.get_feature_vector(symbol, lookback=lookback*2)
            
            if df is None or len(df) < lookback:
                return None
            
            recent = df.tail(lookback)
            latest_price = recent['close'].iloc[-1]
            
            # Calculate resistance and support
            resistance = recent['high'].max()
            support = recent['low'].min()
            
            # Check for breakout
            if latest_price > resistance * 1.01:  # 1% above resistance
                return {
                    'type': 'upside_breakout',
                    'price': latest_price,
                    'resistance': resistance,
                    'strength': (latest_price - resistance) / resistance
                }
            elif latest_price < support * 0.99:  # 1% below support
                return {
                    'type': 'downside_breakout',
                    'price': latest_price,
                    'support': support,
                    'strength': (support - latest_price) / support
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting breakout for {symbol}: {e}")
            return None
    
    def detect_divergence(self, symbol: str) -> Optional[Dict]:
        """Detect price-indicator divergence"""
        try:
            df = self.feature_store.get_feature_vector(symbol, lookback=50)
            
            if df is None or len(df) < 30:
                return None
            
            # Check RSI divergence
            if 'rsi' not in df.columns:
                return None
            
            recent = df.tail(30)
            
            # Price making new lows but RSI not (bullish divergence)
            price_lows = recent['close'].rolling(5).min()
            rsi_lows = recent['rsi'].rolling(5).min()
            
            if price_lows.iloc[-1] < price_lows.iloc[-10] and rsi_lows.iloc[-1] > rsi_lows.iloc[-10]:
                return {
                    'type': 'bullish_divergence',
                    'indicator': 'rsi',
                    'strength': 0.5
                }
            
            # Price making new highs but RSI not (bearish divergence)
            price_highs = recent['close'].rolling(5).max()
            rsi_highs = recent['rsi'].rolling(5).max()
            
            if price_highs.iloc[-1] > price_highs.iloc[-10] and rsi_highs.iloc[-1] < rsi_highs.iloc[-10]:
                return {
                    'type': 'bearish_divergence',
                    'indicator': 'rsi',
                    'strength': 0.5
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting divergence for {symbol}: {e}")
            return None
    
    def _neutral_signal(self, symbol: str) -> Dict:
        """Return neutral signal"""
        return {
            'symbol': symbol,
            'signal_type': 'HOLD',
            'strength': 0.0,
            'confidence': 0.0,
            'reasons': ['Insufficient data or error'],
            'timestamp': datetime.now().isoformat(),
            'strategy': 'neutral'
        }
