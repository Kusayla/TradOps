"""Market data ingestion from exchanges using CCXT"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import ccxt.async_support as ccxt
from loguru import logger

from src.config import settings


class MarketDataIngestion:
    """Handles real-time market data ingestion from exchanges"""
    
    def __init__(self, exchange_id: str = None):
        self.exchange_id = exchange_id or settings.exchange.default_exchange
        self.exchange = None
        self.ws_connections = {}
        
    async def initialize(self):
        """Initialize exchange connection"""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            
            if self.exchange_id == 'binance':
                config['apiKey'] = settings.exchange.binance_api_key
                config['secret'] = settings.exchange.binance_api_secret
                if settings.exchange.binance_testnet:
                    config['urls'] = {
                        'api': {
                            'public': 'https://testnet.binance.vision/api',
                            'private': 'https://testnet.binance.vision/api',
                        }
                    }
            elif self.exchange_id == 'coinbase':
                config['apiKey'] = settings.exchange.coinbase_api_key
                config['secret'] = settings.exchange.coinbase_api_secret
            
            self.exchange = exchange_class(config)
            await self.exchange.load_markets()
            logger.info(f"Initialized {self.exchange_id} exchange")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> List[Dict]:
        """Fetch OHLCV data"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return [
                {
                    'timestamp': candle[0],
                    'datetime': datetime.fromtimestamp(candle[0] / 1000),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5],
                    'symbol': symbol,
                    'timeframe': timeframe
                }
                for candle in ohlcv
            ]
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch latest ticker data"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'timestamp': ticker.get('timestamp'),
                'datetime': ticker.get('datetime'),
                'last': ticker.get('last'),
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'volume': ticker.get('baseVolume'),
                'quote_volume': ticker.get('quoteVolume'),
                'change': ticker.get('change'),
                'percentage': ticker.get('percentage'),
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    async def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Fetch order book"""
        try:
            order_book = await self.exchange.fetch_order_book(symbol, limit)
            return {
                'symbol': symbol,
                'timestamp': order_book.get('timestamp'),
                'datetime': order_book.get('datetime'),
                'bids': order_book.get('bids', []),
                'asks': order_book.get('asks', []),
            }
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return None
    
    async def stream_trades(self, symbol: str, callback):
        """Stream real-time trades (WebSocket)"""
        # For CCXT Pro (paid), use watch_trades
        # For free version, we'll poll
        while True:
            try:
                trades = await self.exchange.fetch_trades(symbol, limit=10)
                for trade in trades:
                    await callback({
                        'symbol': symbol,
                        'id': trade.get('id'),
                        'timestamp': trade.get('timestamp'),
                        'datetime': trade.get('datetime'),
                        'price': trade.get('price'),
                        'amount': trade.get('amount'),
                        'side': trade.get('side'),
                    })
                await asyncio.sleep(1)  # Poll every second
            except Exception as e:
                logger.error(f"Error streaming trades for {symbol}: {e}")
                await asyncio.sleep(5)
    
    async def fetch_multiple_tickers(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch tickers for multiple symbols concurrently"""
        tasks = [self.fetch_ticker(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        return {
            symbol: result 
            for symbol, result in zip(symbols, results) 
            if result is not None
        }
    
    async def close(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            logger.info(f"Closed {self.exchange_id} exchange connection")


class MultiExchangeIngestion:
    """Manage data ingestion from multiple exchanges"""
    
    def __init__(self, exchange_ids: List[str] = None):
        self.exchange_ids = exchange_ids or ['binance']
        self.exchanges = {}
    
    async def initialize(self):
        """Initialize all exchanges"""
        for exchange_id in self.exchange_ids:
            try:
                ingestion = MarketDataIngestion(exchange_id)
                await ingestion.initialize()
                self.exchanges[exchange_id] = ingestion
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_id}: {e}")
    
    async def fetch_best_price(self, symbol: str) -> Dict:
        """Get best bid/ask across all exchanges"""
        tasks = [
            exchange.fetch_ticker(symbol) 
            for exchange in self.exchanges.values()
        ]
        results = await asyncio.gather(*tasks)
        
        best_bid = max((r['bid'] for r in results if r and r.get('bid')), default=0)
        best_ask = min((r['ask'] for r in results if r and r.get('ask')), default=float('inf'))
        
        return {
            'symbol': symbol,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': best_ask - best_bid if best_ask != float('inf') else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    async def close_all(self):
        """Close all exchange connections"""
        for exchange in self.exchanges.values():
            await exchange.close()
