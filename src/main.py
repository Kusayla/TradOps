"""
Main entry point for the AI-powered crypto trading bot
"""
import asyncio
from loguru import logger
import sys

from src.config import settings
from src.data_ingestion.market_data import MarketDataIngestion
from src.data_ingestion.news_ingestion import NewsIngestion, SocialMediaIngestion
from src.data_ingestion.streaming_producer import StreamingProducer
from src.storage.feature_store import FeatureStore
from src.ml.sentiment_analyzer import SentimentAnalyzer
from src.strategy.strategy_engine import StrategyEngine
from src.execution.order_executor import OrderExecutor
from src.monitoring.metrics import metrics
from src.monitoring.alerting import alert_manager


class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        # Core components
        self.market_data = None
        self.news_ingestion = None
        self.social_ingestion = None
        self.streaming_producer = None
        self.feature_store = None
        self.sentiment_analyzer = None
        self.strategy_engine = None
        self.order_executor = None
        
        # State
        self.running = False
        self.symbols = settings.trading.assets_list
        
        logger.info("Trading bot initialized")
    
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing trading bot components...")
            
            # Start metrics server
            metrics.start_server()
            
            # Initialize data ingestion
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            
            self.news_ingestion = NewsIngestion()
            self.social_ingestion = SocialMediaIngestion()
            
            # Initialize streaming
            self.streaming_producer = StreamingProducer()
            self.streaming_producer.initialize()
            
            # Initialize storage
            self.feature_store = FeatureStore()
            self.feature_store.initialize()
            
            # Initialize ML
            self.sentiment_analyzer = SentimentAnalyzer()
            self.sentiment_analyzer.initialize()
            
            # Initialize strategy
            self.strategy_engine = StrategyEngine(
                self.feature_store,
                self.feature_store.redis
            )
            
            # Initialize execution
            self.order_executor = OrderExecutor(
                redis_client=self.feature_store.redis,
                streaming_producer=self.streaming_producer
            )
            await self.order_executor.initialize()
            
            logger.info("? All components initialized successfully")
            await alert_manager.send_alert("Trading bot started successfully", level='INFO')
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            await alert_manager.send_alert(f"Bot initialization failed: {e}", level='CRITICAL')
            raise
    
    async def run(self):
        """Main bot loop"""
        self.running = True
        logger.info("?? Starting trading bot main loop...")
        
        try:
            # Start background tasks
            tasks = [
                asyncio.create_task(self._market_data_loop()),
                asyncio.create_task(self._news_loop()),
                asyncio.create_task(self._trading_loop()),
                asyncio.create_task(self._monitoring_loop()),
            ]
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await alert_manager.send_alert(f"Critical error: {e}", level='CRITICAL')
        finally:
            await self.shutdown()
    
    async def _market_data_loop(self):
        """Continuously fetch and store market data"""
        logger.info("Started market data loop")
        
        while self.running:
            try:
                # Fetch tickers for all symbols
                tickers = await self.market_data.fetch_multiple_tickers(self.symbols)
                
                for symbol, ticker in tickers.items():
                    # Store in database
                    self.feature_store.timescale.store_ticker(ticker)
                    
                    # Cache in Redis
                    self.feature_store.redis.cache_latest_price(symbol, ticker['last'])
                    
                    # Send to Kafka
                    self.streaming_producer.send_market_data(ticker, key=symbol)
                    
                    # Update metrics
                    metrics.record_market_data(symbol, 'exchange')
                
                # Fetch OHLCV data periodically
                for symbol in self.symbols:
                    ohlcv = await self.market_data.fetch_ohlcv(symbol, '1h', limit=100)
                    if ohlcv:
                        self.feature_store.timescale.store_ohlcv(ohlcv)
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in market data loop: {e}")
                metrics.record_api_error('exchange', type(e).__name__)
                await asyncio.sleep(30)
    
    async def _news_loop(self):
        """Continuously fetch and analyze news/social data"""
        logger.info("Started news loop")
        
        while self.running:
            try:
                # Fetch news from all sources
                news_items = await self.news_ingestion.fetch_all_news(
                    currencies=['BTC', 'ETH', 'SOL']
                )
                
                if news_items:
                    # Analyze sentiment
                    analyzed_news = self.sentiment_analyzer.analyze_news(news_items)
                    
                    # Store in database
                    self.feature_store.timescale.store_news(analyzed_news)
                    
                    # Send to Kafka
                    for news in analyzed_news:
                        self.streaming_producer.send_news(news)
                        metrics.record_news(news['source'])
                        
                        # Extract crypto mentions and record sentiment
                        mentions = self.sentiment_analyzer.extract_crypto_mentions(
                            news.get('title', '') + ' ' + news.get('description', '')
                        )
                        for crypto in mentions:
                            sentiment_score = news.get('sentiment', {}).get('sentiment_score', 0)
                            metrics.record_sentiment(crypto, news['source'], sentiment_score)
                
                # Fetch social metrics
                social_metrics = await self.social_ingestion.fetch_social_metrics(
                    ['BTC', 'ETH', 'SOL']
                )
                
                for symbol, metrics_data in social_metrics.items():
                    # Store in database
                    self.feature_store.timescale.store_social_metrics(metrics_data)
                    
                    # Send to Kafka
                    self.streaming_producer.send_social_signal(metrics_data, key=symbol)
                    
                    # Record metrics
                    sentiment = metrics_data.get('sentiment', 0)
                    metrics.record_sentiment(symbol, 'social', sentiment)
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in news loop: {e}")
                metrics.record_api_error('news', type(e).__name__)
                await asyncio.sleep(60)
    
    async def _trading_loop(self):
        """Main trading decision loop"""
        logger.info("Started trading loop")
        
        while self.running:
            try:
                for symbol in self.symbols:
                    # Get sentiment data
                    sentiment_features = self.feature_store.compute_sentiment_features(symbol)
                    
                    # Evaluate symbol and generate decision
                    decision = self.strategy_engine.evaluate_symbol(
                        symbol,
                        sentiment_data=sentiment_features if sentiment_features else None
                    )
                    
                    if decision:
                        # Record signal
                        signal = decision.get('signal', {})
                        metrics.record_signal(
                            symbol,
                            signal.get('signal_type', 'UNKNOWN'),
                            signal.get('strategy', 'unknown'),
                            signal.get('strength', 0)
                        )
                        
                        # Alert on strong signals
                        if abs(signal.get('strength', 0)) > 0.7:
                            await alert_manager.alert_strong_signal(symbol, signal)
                        
                        # Execute order
                        result = await self.order_executor.execute_order(decision)
                        
                        if result:
                            # Record trade
                            metrics.record_trade(
                                result['symbol'],
                                result['side'],
                                result['status']
                            )
                            
                            # Send alert
                            await alert_manager.alert_trade_executed(result)
                    
                    # Check stop loss / take profit
                    current_price = self.feature_store.redis.get_cached_price(symbol)
                    if current_price:
                        hit_type = self.strategy_engine.check_stop_loss_take_profit(
                            symbol, current_price
                        )
                        
                        if hit_type:
                            # Close position
                            position = self.feature_store.redis.get_position(symbol)
                            close_decision = {
                                'action': 'CLOSE',
                                'symbol': symbol,
                                'side': 'SELL' if position.get('side') == 'BUY' else 'BUY',
                                'size': abs(float(position.get('size', 0))),
                                'price': current_price
                            }
                            
                            result = await self.order_executor.execute_order(close_decision)
                            
                            if result and hit_type == 'STOP_LOSS':
                                await alert_manager.alert_stop_loss_hit(
                                    symbol, current_price, result.get('fee', 0)
                                )
                            elif result and hit_type == 'TAKE_PROFIT':
                                await alert_manager.alert_take_profit_hit(
                                    symbol, current_price, result.get('fee', 0)
                                )
                        else:
                            # Update trailing stop
                            self.strategy_engine.update_trailing_stop(symbol, current_price)
                
                await asyncio.sleep(60)  # Evaluate every minute
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self):
        """Monitor portfolio and update metrics"""
        logger.info("Started monitoring loop")
        
        while self.running:
            try:
                # Get portfolio summary
                summary = self.strategy_engine.get_portfolio_summary()
                
                # Update metrics
                risk_metrics = summary['risk_metrics']
                metrics.update_portfolio(
                    risk_metrics['current_equity'],
                    risk_metrics['daily_pnl'],
                    risk_metrics['drawdown']
                )
                
                # Update position metrics
                for symbol, position in summary['positions'].items():
                    if position.get('size'):
                        metrics.update_position(symbol, float(position['size']))
                
                # Check risk limits
                if risk_metrics['drawdown'] > settings.risk.max_drawdown * 0.8:
                    await alert_manager.alert_max_drawdown(
                        risk_metrics['drawdown'],
                        settings.risk.max_drawdown
                    )
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def shutdown(self):
        """Shutdown all components"""
        logger.info("Shutting down trading bot...")
        
        self.running = False
        
        try:
            # Close all connections
            if self.market_data:
                await self.market_data.close()
            
            if self.news_ingestion:
                await self.news_ingestion.close()
            
            if self.social_ingestion:
                await self.social_ingestion.close()
            
            if self.streaming_producer:
                self.streaming_producer.close()
            
            if self.feature_store:
                self.feature_store.close()
            
            if self.order_executor:
                await self.order_executor.close()
            
            await alert_manager.send_alert("Trading bot stopped", level='INFO')
            await alert_manager.close()
            
            logger.info("? Trading bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


async def main():
    """Main entry point"""
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/trading_bot_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG"
    )
    
    logger.info("=" * 60)
    logger.info("AI-Powered Crypto Trading Bot")
    logger.info(f"Trading Mode: {settings.trading.trading_mode.upper()}")
    logger.info(f"Symbols: {', '.join(settings.trading.assets_list)}")
    logger.info("=" * 60)
    
    # Create and run bot
    bot = TradingBot()
    await bot.initialize()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
