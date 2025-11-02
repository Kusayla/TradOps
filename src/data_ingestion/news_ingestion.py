"""News and social media data ingestion"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx
from loguru import logger

from src.config import settings


class NewsIngestion:
    """Fetch news from various sources"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def fetch_cryptopanic(self, currencies: List[str] = None) -> List[Dict]:
        """Fetch news from CryptoPanic"""
        try:
            api_key = settings.data_sources.cryptopanic_api_key
            if not api_key:
                logger.warning("CryptoPanic API key not configured")
                return []
            
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                'auth_token': api_key,
                'kind': 'news',
                'filter': 'rising',
            }
            
            if currencies:
                params['currencies'] = ','.join(currencies)
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    'source': 'cryptopanic',
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'published_at': item.get('published_at'),
                    'domain': item.get('domain'),
                    'votes': item.get('votes', {}).get('positive', 0),
                    'currencies': [c['code'] for c in item.get('currencies', [])],
                    'kind': item.get('kind'),
                }
                for item in data.get('results', [])
            ]
            
        except Exception as e:
            logger.error(f"Error fetching CryptoPanic news: {e}")
            return []
    
    async def fetch_newsapi(self, query: str = "cryptocurrency OR bitcoin OR ethereum") -> List[Dict]:
        """Fetch news from NewsAPI"""
        try:
            api_key = settings.data_sources.newsapi_key
            if not api_key:
                logger.warning("NewsAPI key not configured")
                return []
            
            url = "https://newsapi.org/v2/everything"
            from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            params = {
                'apiKey': api_key,
                'q': query,
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': 100,
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    'source': 'newsapi',
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'url': article.get('url'),
                    'published_at': article.get('publishedAt'),
                    'source_name': article.get('source', {}).get('name'),
                    'author': article.get('author'),
                    'content': article.get('content'),
                }
                for article in data.get('articles', [])
            ]
            
        except Exception as e:
            logger.error(f"Error fetching NewsAPI: {e}")
            return []
    
    async def fetch_all_news(self, currencies: List[str] = None) -> List[Dict]:
        """Fetch news from all sources concurrently"""
        tasks = [
            self.fetch_cryptopanic(currencies),
            self.fetch_newsapi(),
        ]
        results = await asyncio.gather(*tasks)
        
        all_news = []
        for news_list in results:
            all_news.extend(news_list)
        
        # Sort by timestamp
        all_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        return all_news
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class SocialMediaIngestion:
    """Fetch social media signals"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_lunarcrush(self, symbol: str = "BTC") -> Optional[Dict]:
        """Fetch social metrics from LunarCrush"""
        try:
            api_key = settings.data_sources.lunarcrush_api_key
            if not api_key:
                logger.warning("LunarCrush API key not configured")
                return None
            
            url = "https://api.lunarcrush.com/v2"
            params = {
                'data': 'assets',
                'key': api_key,
                'symbol': symbol,
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data'):
                asset = data['data'][0]
                return {
                    'source': 'lunarcrush',
                    'symbol': symbol,
                    'galaxy_score': asset.get('galaxy_score'),
                    'alt_rank': asset.get('alt_rank'),
                    'social_volume': asset.get('social_volume'),
                    'social_score': asset.get('social_score'),
                    'sentiment': asset.get('sentiment'),
                    'twitter_followers': asset.get('twitter_followers'),
                    'reddit_subscribers': asset.get('reddit_subscribers'),
                    'price_score': asset.get('price_score'),
                    'average_sentiment': asset.get('average_sentiment'),
                    'timestamp': datetime.now().isoformat(),
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching LunarCrush data: {e}")
            return None
    
    async def fetch_twitter_sentiment(self, query: str, max_results: int = 100) -> List[Dict]:
        """Fetch tweets (requires Twitter API v2)"""
        try:
            bearer_token = settings.data_sources.twitter_bearer_token
            if not bearer_token:
                logger.warning("Twitter Bearer Token not configured")
                return []
            
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            params = {
                'query': query,
                'max_results': max_results,
                'tweet.fields': 'created_at,public_metrics,entities',
            }
            
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    'source': 'twitter',
                    'id': tweet.get('id'),
                    'text': tweet.get('text'),
                    'created_at': tweet.get('created_at'),
                    'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                    'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0),
                    'replies': tweet.get('public_metrics', {}).get('reply_count', 0),
                }
                for tweet in data.get('data', [])
            ]
            
        except Exception as e:
            logger.error(f"Error fetching Twitter data: {e}")
            return []
    
    async def fetch_social_metrics(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch social metrics for multiple symbols"""
        tasks = [self.fetch_lunarcrush(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        return {
            symbol: result 
            for symbol, result in zip(symbols, results) 
            if result is not None
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
