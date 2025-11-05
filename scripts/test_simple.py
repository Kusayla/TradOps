#!/usr/bin/env python3
"""Simple test script for essential connections"""
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.data_ingestion.public_data_provider import PublicDataProvider
from src.data_ingestion.market_data import MarketDataIngestion

async def test_public_data():
    """Test public data provider"""
    print("\n🌐 Testing Public Data Sources...")
    try:
        provider = PublicDataProvider('binance')
        await provider.initialize()
        
        # Test connectivity
        connectivity = await provider.test_connectivity()
        print(f"   Connectivity test: {connectivity}")
        
        # Test ticker
        ticker = await provider.fetch_ticker('BTC/USDT')
        if ticker:
            print(f"✅ Public data working! BTC/USDT: ${ticker['last']:.2f}")
        
        # Test market overview
        overview = await provider.fetch_market_overview()
        if overview:
            total_mc = overview.get('total_market_cap_usd', 0) / 1e12
            print(f"✅ Market overview: Total market cap: ${total_mc:.2f}T")
        
        await provider.close()
        return True
    except Exception as e:
        print(f"❌ Public data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_exchange():
    """Test exchange connectivity"""
    print(f"\n📊 Testing Exchange Connection ({settings.exchange.default_exchange})...")
    print(f"   Mode: {settings.trading.trading_mode}")
    print(f"   API Keys configured: {settings.exchange.has_api_keys}")
    
    try:
        market_data = MarketDataIngestion()
        await market_data.initialize()
        
        # Test ticker
        ticker = await market_data.fetch_ticker('BTC/EUR')
        if ticker:
            source = ticker.get('source', 'unknown')
            print(f"✅ Ticker fetch successful! BTC/EUR: ${ticker['last']:.2f} (source: {source})")
        else:
            print("❌ Failed to fetch ticker")
            await market_data.close()
            return False
        
        # Test OHLCV
        ohlcv = await market_data.fetch_ohlcv('BTC/EUR', '1h', limit=10)
        if ohlcv:
            print(f"✅ OHLCV fetch successful! Got {len(ohlcv)} candles")
        else:
            print("⚠️  OHLCV fetch failed (might not be critical)")
        
        await market_data.close()
        return True
    except Exception as e:
        print(f"❌ Exchange connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner"""
    print("="*60)
    print("TRADOPS - BASIC CONNECTION TESTS")
    print("="*60)
    print(f"Trading Mode: {settings.trading.trading_mode}")
    print(f"Exchange: {settings.exchange.default_exchange}")
    print(f"Assets: {settings.trading.whitelisted_assets}")
    print("="*60)
    
    results = {}
    
    # Test public data
    results['Public Data'] = await test_public_data()
    
    # Test exchange
    results['Exchange'] = await test_exchange()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print("\n" + "="*60)
    
    all_passed = all(results.values())
    if all_passed:
        print("✅ All tests passed! You can now:")
        print("   1. Download historical data:")
        print("      python scripts/download_historical_data.py --symbols BTC/EUR,ETH/EUR --days 90")
        print("   2. Run the bot:")
        print("      python src/main.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

