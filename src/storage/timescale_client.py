"""TimescaleDB client for time-series data storage"""
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text, Column, Float, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

from src.config import settings

Base = declarative_base()


class OHLCVData(Base):
    """OHLCV data model"""
    __tablename__ = 'ohlcv_data'
    
    timestamp = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    timeframe = Column(String, primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)


class TickerData(Base):
    """Ticker data model"""
    __tablename__ = 'ticker_data'
    
    timestamp = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    last = Column(Float)
    bid = Column(Float)
    ask = Column(Float)
    volume = Column(Float)
    quote_volume = Column(Float)


class NewsData(Base):
    """News data model"""
    __tablename__ = 'news_data'
    
    id = Column(String, primary_key=True)
    source = Column(String)
    title = Column(String)
    url = Column(String)
    published_at = Column(DateTime)
    sentiment_score = Column(Float, nullable=True)


class SocialMetrics(Base):
    """Social media metrics model"""
    __tablename__ = 'social_metrics'
    
    timestamp = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    source = Column(String, primary_key=True)
    social_volume = Column(Float)
    sentiment = Column(Float)
    galaxy_score = Column(Float, nullable=True)


class TradingSignals(Base):
    """Trading signals model"""
    __tablename__ = 'trading_signals'
    
    timestamp = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    signal_type = Column(String)
    strength = Column(Float)
    price = Column(Float)
    metadata = Column(String)  # JSON


class ExecutedTrades(Base):
    """Executed trades model"""
    __tablename__ = 'executed_trades'
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime)
    symbol = Column(String)
    side = Column(String)
    price = Column(Float)
    amount = Column(Float)
    cost = Column(Float)
    fee = Column(Float)
    pnl = Column(Float, nullable=True)


class TimescaleClient:
    """Client for TimescaleDB operations"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
    
    def initialize(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(settings.database.timescaledb_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            
            # Create hypertables for time-series optimization
            with self.engine.connect() as conn:
                tables = ['ohlcv_data', 'ticker_data', 'social_metrics', 'trading_signals', 'executed_trades']
                for table in tables:
                    try:
                        conn.execute(text(f"SELECT create_hypertable('{table}', 'timestamp', if_not_exists => TRUE)"))
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Hypertable {table} might already exist: {e}")
            
            logger.info("Initialized TimescaleDB client")
            
        except Exception as e:
            logger.error(f"Failed to initialize TimescaleDB: {e}")
            raise
    
    def store_ohlcv(self, data: List[Dict]):
        """Store OHLCV data"""
        if not data:
            return
        
        try:
            session = self.Session()
            for item in data:
                ohlcv = OHLCVData(
                    timestamp=item['datetime'],
                    symbol=item['symbol'],
                    timeframe=item['timeframe'],
                    open=item['open'],
                    high=item['high'],
                    low=item['low'],
                    close=item['close'],
                    volume=item['volume']
                )
                session.merge(ohlcv)
            session.commit()
            session.close()
            logger.debug(f"Stored {len(data)} OHLCV records")
        except Exception as e:
            logger.error(f"Error storing OHLCV data: {e}")
    
    def store_ticker(self, data: Dict):
        """Store ticker data"""
        try:
            session = self.Session()
            ticker = TickerData(
                timestamp=datetime.fromtimestamp(data['timestamp'] / 1000),
                symbol=data['symbol'],
                last=data['last'],
                bid=data['bid'],
                ask=data['ask'],
                volume=data['volume'],
                quote_volume=data['quote_volume']
            )
            session.merge(ticker)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error storing ticker data: {e}")
    
    def store_news(self, news_list: List[Dict]):
        """Store news data"""
        try:
            session = self.Session()
            for item in news_list:
                # Parse published_at if string
                published_at = item.get('published_at')
                if isinstance(published_at, str):
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                
                news = NewsData(
                    id=item.get('id', f"{item.get('source')}_{hash(item.get('title'))}"),
                    source=item['source'],
                    title=item['title'],
                    url=item['url'],
                    published_at=published_at,
                    sentiment_score=item.get('sentiment_score')
                )
                session.merge(news)
            session.commit()
            session.close()
            logger.debug(f"Stored {len(news_list)} news records")
        except Exception as e:
            logger.error(f"Error storing news data: {e}")
    
    def store_social_metrics(self, data: Dict):
        """Store social media metrics"""
        try:
            session = self.Session()
            metrics = SocialMetrics(
                timestamp=datetime.fromisoformat(data['timestamp']),
                symbol=data['symbol'],
                source=data['source'],
                social_volume=data.get('social_volume', 0),
                sentiment=data.get('sentiment', 0),
                galaxy_score=data.get('galaxy_score')
            )
            session.merge(metrics)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error storing social metrics: {e}")
    
    def get_ohlcv(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime = None) -> pd.DataFrame:
        """Retrieve OHLCV data as DataFrame"""
        try:
            query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv_data
                WHERE symbol = :symbol AND timeframe = :timeframe
                AND timestamp >= :start_time
            """
            params = {'symbol': symbol, 'timeframe': timeframe, 'start_time': start_time}
            
            if end_time:
                query += " AND timestamp <= :end_time"
                params['end_time'] = end_time
            
            query += " ORDER BY timestamp"
            
            df = pd.read_sql(query, self.engine, params=params)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving OHLCV data: {e}")
            return pd.DataFrame()
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol"""
        try:
            query = """
                SELECT last FROM ticker_data
                WHERE symbol = :symbol
                ORDER BY timestamp DESC
                LIMIT 1
            """
            with self.engine.connect() as conn:
                result = conn.execute(text(query), {'symbol': symbol})
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Closed TimescaleDB connection")
