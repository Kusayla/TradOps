"""Public data provider for free market data without API keys"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
from loguru import logger
import ccxt.async_support as ccxt


class PublicDataProvider:
    """
    Provides market data from public/free sources
    No API keys required for basic functionality
    
    Sources:
    - CoinGecko API (free tier, no auth)
    - CCXT public endpoints (Binance, Bybit, OKX)
    - Fallback mechanism for reliability
    """
    
    def __init__(self, preferred_exchange: str = "binance"):
        self.preferred_exchange = preferred_exchange
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.session = None
        self.ccxt_exchange = None
        
        # CoinGecko symbol mapping
        self.coingecko_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'MATIC': 'matic-network',
            'DOT': 'polkadot',
            'AVAX': 'avalanche-2',
        }
    
    async def initialize(self):
        """Initialize HTTP session and CCXT exchange"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Initialize CCXT exchange in public mode (no API keys)
            exchange_class = getattr(ccxt, self.preferred_exchange)
            self.ccxt_exchange = exchange_class({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            await self.ccxt_exchange.load_markets()
            
            logger.info(f"Initialized public data provider (exchange: {self.preferred_exchange})")
            
        except Exception as e:
            logger.error(f"Failed to initialize public data provider: {e}")
            raise
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Fetch latest ticker data for a symbol
        Tries CCXT first, falls back to CoinGecko
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            
        Returns:
            Ticker data dictionary or None
        """
        # Try CCXT first (faster and more detailed)
        ticker = await self._fetch_ticker_ccxt(symbol)
        if ticker:
            return ticker
        
        # Fallback to CoinGecko
        logger.debug(f"CCXT failed for {symbol}, trying CoinGecko")
        return await self._fetch_ticker_coingecko(symbol)
    
    async def _fetch_ticker_ccxt(self, symbol: str) -> Optional[Dict]:
        """Fetch ticker from CCXT public endpoint"""
        try:
            if not self.ccxt_exchange:
                return None
            
            ticker = await self.ccxt_exchange.fetch_ticker(symbol)
            
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
                'high': ticker.get('high'),
                'low': ticker.get('low'),
                'source': f'ccxt_{self.preferred_exchange}'
            }
            
        except Exception as e:
            logger.debug(f"CCXT fetch_ticker failed for {symbol}: {e}")
            return None
    
    async def _fetch_ticker_coingecko(self, symbol: str) -> Optional[Dict]:
        """Fetch ticker from CoinGecko API"""
        try:
            # Extract base currency (e.g., BTC from BTC/USDT)
            base = symbol.split('/')[0]
            coin_id = self.coingecko_ids.get(base)
            
            if not coin_id:
                logger.warning(f"No CoinGecko ID for {base}")
                return None
            
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"CoinGecko API returned {response.status}")
                    return None
                
                data = await response.json()
                coin_data = data.get(coin_id, {})
                
                if not coin_data:
                    return None
                
                price = coin_data.get('usd', 0)
                
                return {
                    'symbol': symbol,
                    'timestamp': coin_data.get('last_updated_at', 0) * 1000,
                    'datetime': datetime.fromtimestamp(
                        coin_data.get('last_updated_at', 0)
                    ).isoformat() if coin_data.get('last_updated_at') else None,
                    'last': price,
                    'bid': price * 0.9999,  # Approximate bid
                    'ask': price * 1.0001,  # Approximate ask
                    'volume': coin_data.get('usd_24h_vol', 0),
                    'quote_volume': None,
                    'change': coin_data.get('usd_24h_change', 0),
                    'percentage': coin_data.get('usd_24h_change', 0),
                    'high': None,
                    'low': None,
                    'source': 'coingecko'
                }
                
        except Exception as e:
            logger.error(f"CoinGecko fetch failed for {symbol}: {e}")
            return None
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', 
                          limit: int = 100) -> List[Dict]:
        """
        Fetch OHLCV (candlestick) data
        Uses CCXT public endpoints
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            
        Returns:
            List of OHLCV dictionaries
        """
        try:
            if not self.ccxt_exchange:
                logger.warning("CCXT exchange not initialized")
                return []
            
            ohlcv = await self.ccxt_exchange.fetch_ohlcv(
                symbol, timeframe, limit=limit
            )
            
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
                    'timeframe': timeframe,
                    'source': f'ccxt_{self.preferred_exchange}'
                }
                for candle in ohlcv
            ]
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    async def fetch_multiple_tickers(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch tickers for multiple symbols concurrently
        
        Args:
            symbols: List of trading pairs
            
        Returns:
            Dictionary mapping symbols to ticker data
        """
        tasks = [self.fetch_ticker(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        return {
            symbol: result 
            for symbol, result in zip(symbols, results) 
            if result is not None
        }
    
    async def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """
        Fetch order book from CCXT
        
        Args:
            symbol: Trading pair
            limit: Depth of order book
            
        Returns:
            Order book dictionary or None
        """
        try:
            if not self.ccxt_exchange:
                return None
            
            order_book = await self.ccxt_exchange.fetch_order_book(symbol, limit)
            
            return {
                'symbol': symbol,
                'timestamp': order_book.get('timestamp'),
                'datetime': order_book.get('datetime'),
                'bids': order_book.get('bids', []),
                'asks': order_book.get('asks', []),
                'source': f'ccxt_{self.preferred_exchange}'
            }
            
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return None
    
    async def fetch_market_overview(self) -> Dict:
        """
        Fetch overall market overview from CoinGecko
        
        Returns:
            Market statistics dictionary
        """
        try:
            url = f"{self.coingecko_base_url}/global"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                global_data = data.get('data', {})
                
                return {
                    'total_market_cap_usd': global_data.get('total_market_cap', {}).get('usd', 0),
                    'total_volume_24h_usd': global_data.get('total_volume', {}).get('usd', 0),
                    'btc_dominance': global_data.get('market_cap_percentage', {}).get('btc', 0),
                    'eth_dominance': global_data.get('market_cap_percentage', {}).get('eth', 0),
                    'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                    'markets': global_data.get('markets', 0),
                    'updated_at': global_data.get('updated_at', 0),
                    'source': 'coingecko'
                }
                
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            return {}
    
    async def test_connectivity(self) -> Dict[str, bool]:
        """
        Test connectivity to all data sources
        
        Returns:
            Dictionary with status for each source
        """
        results = {}
        
        # Test CCXT
        try:
            if self.ccxt_exchange:
                await self.ccxt_exchange.fetch_ticker('BTC/USDT')
                results[f'ccxt_{self.preferred_exchange}'] = True
            else:
                results[f'ccxt_{self.preferred_exchange}'] = False
        except Exception as e:
            logger.error(f"CCXT connectivity test failed: {e}")
            results[f'ccxt_{self.preferred_exchange}'] = False
        
        # Test CoinGecko
        try:
            url = f"{self.coingecko_base_url}/ping"
            async with self.session.get(url) as response:
                results['coingecko'] = response.status == 200
        except Exception as e:
            logger.error(f"CoinGecko connectivity test failed: {e}")
            results['coingecko'] = False
        
        return results
    
    async def close(self):
        """Close all connections"""
        try:
            if self.session:
                await self.session.close()
            
            if self.ccxt_exchange:
                await self.ccxt_exchange.close()
            
            logger.info("Closed public data provider")
            
        except Exception as e:
            logger.error(f"Error closing public data provider: {e}")


class PublicDataCache:
    """
    Simple in-memory cache for public data
    Reduces API calls and improves performance
    """
    
    def __init__(self, ttl_seconds: int = 10):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached value if not expired"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if datetime.now().timestamp() - entry['timestamp'] > self.ttl:
            del self.cache[key]
            return None
        
        return entry['data']
    
    def set(self, key: str, value: Dict):
        """Cache a value with current timestamp"""
        self.cache[key] = {
            'data': value,
            'timestamp': datetime.now().timestamp()
        }
    
    def clear(self):
        """Clear all cached data"""
        self.cache.clear()

