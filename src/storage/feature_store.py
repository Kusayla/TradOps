"""Feature store for online and offline features"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.storage.timescale_client import TimescaleClient
from src.storage.redis_client import RedisClient


class FeatureStore:
    """Feature store combining online (Redis) and offline (TimescaleDB) features"""
    
    def __init__(self):
        self.timescale = TimescaleClient()
        self.redis = RedisClient()
    
    def initialize(self):
        """Initialize feature store"""
        self.timescale.initialize()
        self.redis.initialize()
        logger.info("Initialized Feature Store")
    
    def compute_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute technical indicators from OHLCV data"""
        try:
            import pandas_ta as ta
            
            # Price-based indicators
            df['sma_20'] = ta.sma(df['close'], length=20)
            df['sma_50'] = ta.sma(df['close'], length=50)
            df['ema_12'] = ta.ema(df['close'], length=12)
            df['ema_26'] = ta.ema(df['close'], length=26)
            
            # Momentum indicators
            df['rsi'] = ta.rsi(df['close'], length=14)
            macd = ta.macd(df['close'])
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']
            
            # Volatility indicators
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
            bbands = ta.bbands(df['close'], length=20)
            df['bb_upper'] = bbands['BBU_20_2.0']
            df['bb_middle'] = bbands['BBM_20_2.0']
            df['bb_lower'] = bbands['BBL_20_2.0']
            
            # Volume indicators
            df['obv'] = ta.obv(df['close'], df['volume'])
            df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
            
            # Trend indicators
            df['adx'] = ta.adx(df['high'], df['low'], df['close'])['ADX_14']
            
            # Returns
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = pd.np.log(df['close'] / df['close'].shift(1))
            
            # Historical volatility
            df['volatility_20'] = df['returns'].rolling(20).std()
            
            return df
            
        except Exception as e:
            logger.error(f"Error computing technical features: {e}")
            return df
    
    def get_historical_features(self, symbol: str, lookback_days: int = 30) -> pd.DataFrame:
        """Get historical features for a symbol"""
        start_time = datetime.now() - timedelta(days=lookback_days)
        
        # Get OHLCV data
        df = self.timescale.get_ohlcv(symbol, '1h', start_time)
        
        if df.empty:
            logger.warning(f"No historical data for {symbol}")
            return pd.DataFrame()
        
        # Compute technical features
        df = self.compute_technical_features(df)
        
        return df
    
    def get_online_features(self, symbol: str) -> Dict:
        """Get real-time features from Redis"""
        features = {
            'price': self.redis.get_cached_price(symbol),
            'signal': self.redis.get_cached_signal(symbol),
            'position': self.redis.get_position(symbol),
        }
        return features
    
    def store_online_features(self, symbol: str, features: Dict):
        """Store real-time features to Redis"""
        # Store as hash for quick access
        feature_key = f"features:{symbol}"
        self.redis.set_hash(feature_key, features)
    
    def get_feature_vector(self, symbol: str, lookback: int = 100) -> Optional[pd.DataFrame]:
        """
        Get complete feature vector combining historical and online features
        Used for ML model inference
        """
        try:
            # Get recent historical data
            start_time = datetime.now() - timedelta(hours=lookback)
            df = self.timescale.get_ohlcv(symbol, '1h', start_time)
            
            if df.empty:
                return None
            
            # Compute features
            df = self.compute_technical_features(df)
            
            # Get online features
            online = self.get_online_features(symbol)
            
            # Add online features as latest row metadata
            if online.get('price'):
                df.loc[df.index[-1], 'latest_price'] = online['price']
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting feature vector for {symbol}: {e}")
            return None
    
    def compute_sentiment_features(self, symbol: str, lookback_hours: int = 24) -> Dict:
        """Compute sentiment features from news and social data"""
        try:
            # This would query news_data and social_metrics tables
            # and aggregate sentiment scores
            
            # Placeholder implementation
            features = {
                'avg_sentiment_24h': 0.0,
                'news_volume_24h': 0,
                'social_volume_24h': 0,
                'sentiment_trend': 0.0,  # Change in sentiment
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error computing sentiment features: {e}")
            return {}
    
    def close(self):
        """Close all connections"""
        self.timescale.close()
        self.redis.close()
        logger.info("Closed Feature Store")
