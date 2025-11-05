"""Script to download historical market data for backtesting"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_ingestion.historical_downloader import HistoricalDataDownloader
from src.config import settings


async def download_data(symbols: list, 
                       timeframes: list,
                       days: int = 90,
                       exchange: str = 'binance',
                       file_format: str = 'csv'):
    """
    Download historical data for multiple symbols and timeframes
    
    Args:
        symbols: List of trading pairs
        timeframes: List of timeframes
        days: Number of days of historical data
        exchange: Exchange to download from (using public API)
        file_format: 'csv' or 'parquet'
    """
    logger.info("=" * 60)
    logger.info("Historical Data Downloader")
    logger.info("=" * 60)
    logger.info(f"Exchange: {exchange}")
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"Timeframes: {', '.join(timeframes)}")
    logger.info(f"Days: {days}")
    logger.info(f"Format: {file_format}")
    logger.info("=" * 60)
    
    # Initialize downloader
    downloader = HistoricalDataDownloader(exchange_id=exchange)
    await downloader.initialize()
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    total_downloads = len(symbols) * len(timeframes)
    current = 0
    
    try:
        # Download for each symbol and timeframe
        for symbol in symbols:
            for timeframe in timeframes:
                current += 1
                logger.info(f"\n[{current}/{total_downloads}] Downloading {symbol} {timeframe}...")
                
                try:
                    df = await downloader.download_ohlcv(
                        symbol=symbol,
                        timeframe=timeframe,
                        start_date=start_date,
                        end_date=end_date,
                        save_format=file_format
                    )
                    
                    if not df.empty:
                        # Get summary
                        summary = downloader.get_data_summary(symbol, timeframe, file_format)
                        logger.info(f"✓ Downloaded {summary['num_candles']} candles "
                                  f"({summary['start_date']} to {summary['end_date']})")
                    else:
                        logger.warning(f"✗ No data downloaded for {symbol} {timeframe}")
                    
                except Exception as e:
                    logger.error(f"✗ Failed to download {symbol} {timeframe}: {e}")
        
        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("Download Summary")
        logger.info("=" * 60)
        
        files = downloader.list_downloaded_files()
        logger.info(f"Total files: {len(files)}")
        
        total_size_mb = sum(f['size_mb'] for f in files)
        logger.info(f"Total size: {total_size_mb:.2f} MB")
        
        logger.info("\nDownloaded files:")
        for file in files:
            logger.info(f"  - {file['symbol']} {file['timeframe']} "
                       f"({file['size_mb']:.2f} MB) - {file['format']}")
        
        logger.info("\n✓ Download complete!")
        logger.info(f"Data saved to: {downloader.data_dir}")
        
    finally:
        await downloader.close()


async def update_existing_data():
    """Update all existing historical data files with latest candles"""
    logger.info("=" * 60)
    logger.info("Update Existing Data")
    logger.info("=" * 60)
    
    downloader = HistoricalDataDownloader()
    await downloader.initialize()
    
    try:
        files = downloader.list_downloaded_files()
        
        if not files:
            logger.warning("No existing files found. Run download first.")
            return
        
        logger.info(f"Found {len(files)} files to update\n")
        
        for i, file in enumerate(files, 1):
            symbol = file['symbol']
            timeframe = file['timeframe']
            
            logger.info(f"[{i}/{len(files)}] Updating {symbol} {timeframe}...")
            
            try:
                df = await downloader.update_existing_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    file_format=file['format']
                )
                
                if not df.empty:
                    summary = downloader.get_data_summary(symbol, timeframe, file['format'])
                    logger.info(f"✓ Updated to {summary['num_candles']} candles "
                              f"(latest: {summary['end_date']})")
                else:
                    logger.warning(f"✗ No update for {symbol} {timeframe}")
                    
            except Exception as e:
                logger.error(f"✗ Failed to update {symbol} {timeframe}: {e}")
        
        logger.info("\n✓ Update complete!")
        
    finally:
        await downloader.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download historical market data')
    parser.add_argument('--symbols', type=str, 
                       help='Comma-separated list of symbols (default: from config)')
    parser.add_argument('--timeframes', type=str, default='1h,4h,1d',
                       help='Comma-separated list of timeframes (default: 1h,4h,1d)')
    parser.add_argument('--days', type=int, default=90,
                       help='Number of days to download (default: 90)')
    parser.add_argument('--exchange', type=str, default='binance',
                       help='Exchange to download from (default: binance)')
    parser.add_argument('--format', type=str, default='csv', choices=['csv', 'parquet'],
                       help='File format (default: csv)')
    parser.add_argument('--update', action='store_true',
                       help='Update existing data files instead of downloading')
    
    args = parser.parse_args()
    
    if args.update:
        # Update mode
        asyncio.run(update_existing_data())
    else:
        # Download mode
        symbols = args.symbols.split(',') if args.symbols else settings.trading.assets_list
        timeframes = args.timeframes.split(',')
        
        asyncio.run(download_data(
            symbols=symbols,
            timeframes=timeframes,
            days=args.days,
            exchange=args.exchange,
            file_format=args.format
        ))


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nDownload interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

