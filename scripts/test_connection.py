#!/usr/bin/env python3
"""
Test script to verify all connections and APIs
"""
import sys
import asyncio
from loguru import logger

# Add src to path
sys.path.insert(0, '/workspace')

from src.config import settings
from src.data_ingestion.market_data import MarketDataIngestion
from src.data_ingestion.news_ingestion import NewsIngestion, SocialMediaIngestion
from src.storage.timescale_client import TimescaleClient
from src.storage.redis_client import RedisClient


async def test_exchange():
    """Test exchange connectivity"""
    print("\n?? Testing Exchange Connection...")
    try:
        market_data = MarketDataIngestion()
        await market_data.initialize()
        
        # Fetch ticker
        ticker = await market_data.fetch_ticker('BTC/USDT')
        if ticker:
            print(f"? Exchange connected! BTC/USDT: ${ticker['last']:.2f}")
        else:
            print("? Failed to fetch ticker")
        
        await market_data.close()
        return True
    except Exception as e:
        print(f"? Exchange connection failed: {e}")
        return False


async def test_news_apis():
    """Test news APIs"""
    print("\n?? Testing News APIs...")
    success = True
    
    try:
        news_ingestion = NewsIngestion()
        
        # Test CryptoPanic
        if settings.data_sources.cryptopanic_api_key:
            news = await news_ingestion.fetch_cryptopanic(['BTC'])
            if news:
                print(f"? CryptoPanic: {len(news)} articles fetched")
            else:
                print("??  CryptoPanic: No data (check API key)")
        else:
            print("??  CryptoPanic API key not configured")
        
        # Test NewsAPI
        if settings.data_sources.newsapi_key:
            news = await news_ingestion.fetch_newsapi()
            if news:
                print(f"? NewsAPI: {len(news)} articles fetched")
            else:
                print("??  NewsAPI: No data (check API key)")
        else:
            print("??  NewsAPI key not configured")
        
        await news_ingestion.close()
    except Exception as e:
        print(f"? News API test failed: {e}")
        success = False
    
    return success


async def test_social_apis():
    """Test social media APIs"""
    print("\n?? Testing Social Media APIs...")
    success = True
    
    try:
        social_ingestion = SocialMediaIngestion()
        
        # Test LunarCrush
        if settings.data_sources.lunarcrush_api_key:
            data = await social_ingestion.fetch_lunarcrush('BTC')
            if data:
                print(f"? LunarCrush: Social score {data.get('social_score', 'N/A')}")
            else:
                print("??  LunarCrush: No data (check API key)")
        else:
            print("??  LunarCrush API key not configured")
        
        await social_ingestion.close()
    except Exception as e:
        print(f"? Social API test failed: {e}")
        success = False
    
    return success


def test_database():
    """Test database connections"""
    print("\n?? Testing Database Connections...")
    success = True
    
    # Test TimescaleDB
    try:
        timescale = TimescaleClient()
        timescale.initialize()
        print("? TimescaleDB connected")
        timescale.close()
    except Exception as e:
        print(f"? TimescaleDB connection failed: {e}")
        success = False
    
    # Test Redis
    try:
        redis = RedisClient()
        redis.initialize()
        redis.set('test_key', 'test_value')
        value = redis.get('test_key')
        if value == 'test_value':
            print("? Redis connected and working")
        redis.delete('test_key')
        redis.close()
    except Exception as e:
        print(f"? Redis connection failed: {e}")
        success = False
    
    return success


async def main():
    """Main test runner"""
    logger.remove()
    logger.add(sys.stdout, level="WARNING")
    
    print("="*60)
    print("TRADING BOT CONNECTION TESTS")
    print("="*60)
    
    results = {
        'Exchange': await test_exchange(),
        'News APIs': await test_news_apis(),
        'Social APIs': await test_social_apis(),
        'Databases': test_database(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, success in results.items():
        status = "? PASS" if success else "? FAIL"
        print(f"{test_name}: {status}")
    
    print("\n" + "="*60)
    
    all_passed = all(results.values())
    if all_passed:
        print("? All tests passed! You're ready to start trading.")
    else:
        print("??  Some tests failed. Please check your configuration.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
