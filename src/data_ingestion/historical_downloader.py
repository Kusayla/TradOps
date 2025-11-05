"""Download and store historical market data for backtesting"""
import asyncio
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger
import ccxt.async_support as ccxt


class HistoricalDataDownloader:
    """
    Download historical OHLCV data from public sources
    Saves data in CSV/Parquet format for backtesting
    """
    
    def __init__(self, exchange_id: str = "binance", data_dir: str = "data/historical"):
        self.exchange_id = exchange_id
        self.data_dir = Path(data_dir)
        self.exchange = None
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize exchange connection (public API, no keys needed)"""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            await self.exchange.load_markets()
            
            logger.info(f"Initialized historical downloader for {self.exchange_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize downloader: {e}")
            raise
    
    async def download_ohlcv(self,
                            symbol: str,
                            timeframe: str = '1h',
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            save_format: str = 'csv') -> pd.DataFrame:
        """
        Download OHLCV data for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            start_date: Start date (default: 90 days ago)
            end_date: End date (default: now)
            save_format: 'csv' or 'parquet'
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Default dates
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=90)
            
            logger.info(f"Downloading {symbol} {timeframe} from {start_date} to {end_date}")
            
            # Convert to milliseconds
            since = int(start_date.timestamp() * 1000)
            end_ms = int(end_date.timestamp() * 1000)
            
            all_ohlcv = []
            current_since = since
            
            # Fetch data in batches (most exchanges limit to 1000 candles per request)
            while current_since < end_ms:
                try:
                    ohlcv = await self.exchange.fetch_ohlcv(
                        symbol,
                        timeframe,
                        since=current_since,
                        limit=1000
                    )
                    
                    if not ohlcv:
                        break
                    
                    all_ohlcv.extend(ohlcv)
                    
                    # Update since to last candle timestamp
                    current_since = ohlcv[-1][0] + 1
                    
                    logger.debug(f"Downloaded {len(ohlcv)} candles, total: {len(all_ohlcv)}")
                    
                    # Respect rate limits
                    await asyncio.sleep(self.exchange.rateLimit / 1000)
                    
                except Exception as e:
                    logger.warning(f"Error in batch download: {e}")
                    await asyncio.sleep(5)
                    continue
            
            if not all_ohlcv:
                logger.warning(f"No data downloaded for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(
                all_ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            
            # Remove duplicates
            df = df[~df.index.duplicated(keep='first')]
            
            # Sort by datetime
            df.sort_index(inplace=True)
            
            logger.info(f"Downloaded {len(df)} candles for {symbol}")
            
            # Save to file
            filename = self._get_filename(symbol, timeframe, save_format)
            self._save_dataframe(df, filename, save_format)
            
            return df
            
        except Exception as e:
            logger.error(f"Error downloading {symbol}: {e}")
            return pd.DataFrame()
    
    async def download_multiple_symbols(self,
                                       symbols: List[str],
                                       timeframe: str = '1h',
                                       start_date: Optional[datetime] = None,
                                       end_date: Optional[datetime] = None,
                                       save_format: str = 'csv') -> dict:
        """
        Download OHLCV data for multiple symbols
        
        Args:
            symbols: List of trading pairs
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            save_format: File format
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        
        for symbol in symbols:
            try:
                df = await self.download_ohlcv(
                    symbol,
                    timeframe,
                    start_date,
                    end_date,
                    save_format
                )
                results[symbol] = df
                
            except Exception as e:
                logger.error(f"Failed to download {symbol}: {e}")
                results[symbol] = pd.DataFrame()
        
        logger.info(f"Downloaded data for {len([s for s, df in results.items() if not df.empty])}/{len(symbols)} symbols")
        
        return results
    
    def load_ohlcv(self, symbol: str, timeframe: str = '1h',
                   file_format: str = 'csv') -> pd.DataFrame:
        """
        Load previously downloaded OHLCV data
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe
            file_format: 'csv' or 'parquet'
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            filename = self._get_filename(symbol, timeframe, file_format)
            
            if not filename.exists():
                logger.warning(f"File not found: {filename}")
                return pd.DataFrame()
            
            if file_format == 'csv':
                df = pd.read_csv(filename, index_col='datetime', parse_dates=True)
            elif file_format == 'parquet':
                df = pd.read_parquet(filename)
            else:
                logger.error(f"Unsupported format: {file_format}")
                return pd.DataFrame()
            
            logger.info(f"Loaded {len(df)} candles for {symbol} from {filename}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {symbol}: {e}")
            return pd.DataFrame()
    
    def _get_filename(self, symbol: str, timeframe: str, file_format: str) -> Path:
        """Generate filename for symbol and timeframe"""
        # Replace / with _ for filename compatibility
        safe_symbol = symbol.replace('/', '_')
        return self.data_dir / f"{safe_symbol}_{timeframe}.{file_format}"
    
    def _save_dataframe(self, df: pd.DataFrame, filename: Path, file_format: str):
        """Save DataFrame to file"""
        try:
            if file_format == 'csv':
                df.to_csv(filename)
            elif file_format == 'parquet':
                df.to_parquet(filename)
            else:
                logger.error(f"Unsupported format: {file_format}")
                return
            
            logger.info(f"Saved data to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to {filename}: {e}")
    
    def list_downloaded_files(self) -> List[dict]:
        """
        List all downloaded data files
        
        Returns:
            List of dictionaries with file info
        """
        files = []
        
        for file_path in self.data_dir.glob('*.*'):
            if file_path.suffix in ['.csv', '.parquet']:
                # Parse filename
                parts = file_path.stem.split('_')
                if len(parts) >= 2:
                    symbol = '_'.join(parts[:-1]).replace('_', '/')
                    timeframe = parts[-1]
                    
                    # Get file stats
                    stat = file_path.stat()
                    
                    files.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'format': file_path.suffix[1:],
                        'size_mb': stat.st_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'path': str(file_path)
                    })
        
        return sorted(files, key=lambda x: x['symbol'])
    
    def get_data_summary(self, symbol: str, timeframe: str = '1h',
                        file_format: str = 'csv') -> dict:
        """
        Get summary statistics for downloaded data
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe
            file_format: File format
            
        Returns:
            Dictionary with summary stats
        """
        try:
            df = self.load_ohlcv(symbol, timeframe, file_format)
            
            if df.empty:
                return {}
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'num_candles': len(df),
                'start_date': df.index[0].isoformat(),
                'end_date': df.index[-1].isoformat(),
                'days_covered': (df.index[-1] - df.index[0]).days,
                'price_range': {
                    'min': df['low'].min(),
                    'max': df['high'].max(),
                    'mean': df['close'].mean()
                },
                'volume': {
                    'total': df['volume'].sum(),
                    'mean': df['volume'].mean(),
                    'max': df['volume'].max()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting summary for {symbol}: {e}")
            return {}
    
    async def update_existing_data(self, symbol: str, timeframe: str = '1h',
                                   file_format: str = 'csv') -> pd.DataFrame:
        """
        Update existing data file with latest candles
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe
            file_format: File format
            
        Returns:
            Updated DataFrame
        """
        try:
            # Load existing data
            existing_df = self.load_ohlcv(symbol, timeframe, file_format)
            
            if existing_df.empty:
                logger.info(f"No existing data for {symbol}, downloading from scratch")
                return await self.download_ohlcv(symbol, timeframe, save_format=file_format)
            
            # Download new data from last timestamp
            last_date = existing_df.index[-1].to_pydatetime()
            new_df = await self.download_ohlcv(
                symbol,
                timeframe,
                start_date=last_date,
                end_date=datetime.now(),
                save_format=file_format
            )
            
            if new_df.empty:
                logger.info(f"No new data for {symbol}")
                return existing_df
            
            # Combine and remove duplicates
            combined_df = pd.concat([existing_df, new_df])
            combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
            combined_df.sort_index(inplace=True)
            
            # Save updated data
            filename = self._get_filename(symbol, timeframe, file_format)
            self._save_dataframe(combined_df, filename, file_format)
            
            logger.info(f"Updated {symbol}: {len(existing_df)} -> {len(combined_df)} candles")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"Error updating {symbol}: {e}")
            return pd.DataFrame()
    
    async def close(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            logger.info("Closed historical downloader")

