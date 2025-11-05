"""
AI-powered Signal Generator
Combines technical analysis, sentiment analysis, and market context
"""
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from loguru import logger


class AISignalGenerator:
    """
    Generate trading signals using AI
    
    Combines:
    - Technical indicators (30%)
    - Sentiment analysis (40%)
    - Social metrics (20%)
    - Market context (10%)
    """
    
    def __init__(self):
        # Weights for each component
        self.weights = {
            'technical': 0.30,
            'sentiment': 0.40,
            'social': 0.20,
            'market_context': 0.10
        }
        
        # Thresholds
        self.thresholds = {
            'strong_buy': 0.7,
            'buy': 0.4,
            'neutral_high': 0.4,
            'neutral_low': -0.4,
            'sell': -0.4,
            'strong_sell': -0.7
        }
    
    def generate_signal(self,
                       symbol: str,
                       technical_data: Optional[Dict] = None,
                       sentiment_data: Optional[Dict] = None,
                       social_data: Optional[Dict] = None,
                       market_data: Optional[Dict] = None) -> Dict:
        """
        Generate AI trading signal
        
        Args:
            symbol: Trading pair (e.g., 'BTC/EUR')
            technical_data: Technical indicators dict
            sentiment_data: Sentiment analysis dict
            social_data: Social metrics dict
            market_data: Market context dict
            
        Returns:
            Signal dictionary with score and recommendation
        """
        scores = {}
        
        # 1. Technical Score (30%)
        technical_score = self._calculate_technical_score(technical_data) if technical_data else 0
        scores['technical'] = technical_score
        
        # 2. Sentiment Score (40%)
        sentiment_score = self._calculate_sentiment_score(sentiment_data) if sentiment_data else 0
        scores['sentiment'] = sentiment_score
        
        # 3. Social Score (20%)
        social_score = self._calculate_social_score(social_data) if social_data else 0
        scores['social'] = social_score
        
        # 4. Market Context Score (10%)
        market_score = self._calculate_market_score(market_data) if market_data else 0
        scores['market_context'] = market_score
        
        # Calculate weighted final score
        final_score = sum(scores[k] * self.weights[k] for k in scores.keys())
        
        # Determine action
        action = self._determine_action(final_score)
        
        # Generate explanation
        explanation = self._generate_explanation(scores, final_score, symbol)
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'final_score': final_score,
            'action': action,
            'confidence': abs(final_score),
            'scores': scores,
            'explanation': explanation,
            'weights': self.weights
        }
    
    def _calculate_technical_score(self, data: Dict) -> float:
        """Calculate technical analysis score (-1 to +1)"""
        score = 0
        count = 0
        
        # RSI
        if 'rsi' in data:
            rsi = data['rsi']
            if rsi < 30:
                score += 1  # Oversold - buy signal
            elif rsi > 70:
                score -= 1  # Overbought - sell signal
            else:
                score += (50 - rsi) / 20  # Normalized
            count += 1
        
        # MACD
        if 'macd' in data and 'signal' in data:
            macd_diff = data['macd'] - data['signal']
            if macd_diff > 0:
                score += 0.5
            else:
                score -= 0.5
            count += 1
        
        # SMA Crossover
        if 'sma_20' in data and 'sma_50' in data and 'close' in data:
            if data['sma_20'] > data['sma_50']:
                score += 0.5  # Bullish
            else:
                score -= 0.5  # Bearish
            count += 1
        
        # Trend
        if 'trend' in data:
            if data['trend'] == 'up':
                score += 0.7
            elif data['trend'] == 'down':
                score -= 0.7
            count += 1
        
        # Volume
        if 'volume_trend' in data:
            if data['volume_trend'] == 'increasing':
                score += 0.3
            elif data['volume_trend'] == 'decreasing':
                score -= 0.3
            count += 1
        
        return score / count if count > 0 else 0
    
    def _calculate_sentiment_score(self, data: Dict) -> float:
        """Calculate sentiment analysis score (-1 to +1)"""
        if not data:
            return 0
        
        # Main sentiment score from FinBERT
        score = data.get('sentiment_score', 0)
        
        # Sentiment trend (is it improving?)
        if 'sentiment_trend' in data:
            if data['sentiment_trend'] == 'improving':
                score += 0.2
            elif data['sentiment_trend'] == 'worsening':
                score -= 0.2
        
        # Number of recent news (more news = more weight)
        news_count = data.get('news_count', 0)
        if news_count > 10:
            # Many news, sentiment is more reliable
            score *= 1.2
        elif news_count < 3:
            # Few news, reduce weight
            score *= 0.7
        
        # Clamp to [-1, 1]
        return max(-1, min(1, score))
    
    def _calculate_social_score(self, data: Dict) -> float:
        """Calculate social metrics score (-1 to +1)"""
        if not data:
            return 0
        
        score = 0
        count = 0
        
        # Social sentiment
        if 'social_sentiment' in data:
            score += data['social_sentiment']
            count += 1
        
        # Mention volume change
        if 'mentions_change' in data:
            change = data['mentions_change']
            if change > 50:  # +50% mentions
                score += 0.5
            elif change > 100:  # +100% mentions
                score += 0.8
            elif change < -50:  # -50% mentions
                score -= 0.5
            count += 1
        
        # Galaxy score (LunarCrush)
        if 'galaxy_score' in data:
            # Galaxy score is 0-100, normalize to -1 to +1
            normalized = (data['galaxy_score'] - 50) / 50
            score += normalized
            count += 1
        
        return score / count if count > 0 else 0
    
    def _calculate_market_score(self, data: Dict) -> float:
        """Calculate market context score (-1 to +1)"""
        if not data:
            return 0
        
        score = 0
        count = 0
        
        # BTC dominance
        if 'btc_dominance' in data:
            dom = data['btc_dominance']
            if dom > 60:  # High BTC dom, altcoins may suffer
                score -= 0.3
            elif dom < 40:  # Low BTC dom, altcoins may rally
                score += 0.3
            count += 1
        
        # Fear & Greed Index
        if 'fear_greed' in data:
            fg = data['fear_greed']
            if fg < 20:  # Extreme fear - contrarian buy
                score += 0.5
            elif fg > 80:  # Extreme greed - contrarian sell
                score -= 0.5
            else:
                # Normalize to -1 to +1
                score += (fg - 50) / 50 * 0.3
            count += 1
        
        # Market trend
        if 'market_trend' in data:
            if data['market_trend'] == 'bull':
                score += 0.5
            elif data['market_trend'] == 'bear':
                score -= 0.5
            count += 1
        
        return score / count if count > 0 else 0
    
    def _determine_action(self, score: float) -> str:
        """Determine trading action based on score"""
        if score >= self.thresholds['strong_buy']:
            return 'STRONG_BUY'
        elif score >= self.thresholds['buy']:
            return 'BUY'
        elif score <= self.thresholds['strong_sell']:
            return 'STRONG_SELL'
        elif score <= self.thresholds['sell']:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _generate_explanation(self, scores: Dict, final_score: float, symbol: str) -> str:
        """Generate human-readable explanation"""
        parts = []
        
        # Technical
        tech = scores.get('technical', 0)
        if abs(tech) > 0.3:
            direction = "haussier" if tech > 0 else "baissier"
            parts.append(f"Technique {direction} ({tech:.2f})")
        
        # Sentiment
        sent = scores.get('sentiment', 0)
        if abs(sent) > 0.3:
            mood = "positif" if sent > 0 else "négatif"
            parts.append(f"Sentiment {mood} ({sent:.2f})")
        
        # Social
        soc = scores.get('social', 0)
        if abs(soc) > 0.3:
            trend = "en hausse" if soc > 0 else "en baisse"
            parts.append(f"Social {trend} ({soc:.2f})")
        
        # Market
        mkt = scores.get('market_context', 0)
        if abs(mkt) > 0.3:
            context = "favorable" if mkt > 0 else "défavorable"
            parts.append(f"Marché {context} ({mkt:.2f})")
        
        if parts:
            return f"{symbol}: " + " | ".join(parts) + f" → Score final: {final_score:.2f}"
        else:
            return f"{symbol}: Signaux neutres → Score final: {final_score:.2f}"
    
    def should_add_to_watchlist(self, signal: Dict) -> bool:
        """Determine if crypto should be added to watchlist"""
        return (
            signal['final_score'] > 0.6 and
            signal['confidence'] > 0.6 and
            signal['scores'].get('sentiment', 0) > 0.4
        )
    
    def should_remove_from_watchlist(self, signal: Dict) -> bool:
        """Determine if crypto should be removed from watchlist"""
        return (
            signal['final_score'] < -0.5 and
            signal['scores'].get('sentiment', 0) < -0.3
        )
    
    def calculate_position_size(self, signal: Dict, max_position: float = 0.05) -> float:
        """
        Calculate position size based on signal strength
        
        Args:
            signal: Signal dictionary
            max_position: Maximum position size (default 5%)
            
        Returns:
            Position size as fraction of capital
        """
        if signal['action'] in ['HOLD', 'SELL', 'STRONG_SELL']:
            return 0
        
        # Base size on confidence
        confidence = signal['confidence']
        
        if signal['action'] == 'STRONG_BUY':
            base_size = max_position
        else:  # BUY
            base_size = max_position * 0.6
        
        # Adjust by confidence
        position_size = base_size * confidence
        
        # Ensure minimum and maximum
        position_size = max(0.01, min(position_size, max_position))
        
        return position_size

