"""Prometheus metrics for monitoring"""
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
from loguru import logger

from src.config import settings


class MetricsCollector:
    """Collect and expose Prometheus metrics"""
    
    def __init__(self):
        # Trading metrics
        self.trades_total = Counter(
            'trading_trades_total',
            'Total number of trades executed',
            ['symbol', 'side', 'status']
        )
        
        self.trade_pnl = Histogram(
            'trading_pnl',
            'Profit/Loss per trade',
            ['symbol'],
            buckets=[-1000, -500, -100, -50, 0, 50, 100, 500, 1000, 5000]
        )
        
        self.portfolio_value = Gauge(
            'trading_portfolio_value',
            'Current portfolio value'
        )
        
        self.position_size = Gauge(
            'trading_position_size',
            'Current position size',
            ['symbol']
        )
        
        self.daily_pnl = Gauge(
            'trading_daily_pnl',
            'Daily profit/loss'
        )
        
        self.drawdown = Gauge(
            'trading_drawdown',
            'Current drawdown percentage'
        )
        
        # Signal metrics
        self.signals_generated = Counter(
            'trading_signals_generated',
            'Number of signals generated',
            ['symbol', 'signal_type', 'strategy']
        )
        
        self.signal_strength = Histogram(
            'trading_signal_strength',
            'Signal strength distribution',
            ['symbol'],
            buckets=[-1.0, -0.7, -0.5, -0.3, 0, 0.3, 0.5, 0.7, 1.0]
        )
        
        # Data ingestion metrics
        self.market_data_updates = Counter(
            'trading_market_data_updates',
            'Market data updates received',
            ['symbol', 'source']
        )
        
        self.news_items = Counter(
            'trading_news_items',
            'News items processed',
            ['source']
        )
        
        self.sentiment_score = Histogram(
            'trading_sentiment_score',
            'Sentiment scores',
            ['symbol', 'source'],
            buckets=[-1.0, -0.5, -0.2, 0, 0.2, 0.5, 1.0]
        )
        
        # Performance metrics
        self.execution_latency = Histogram(
            'trading_execution_latency_seconds',
            'Order execution latency',
            ['exchange'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        self.api_errors = Counter(
            'trading_api_errors_total',
            'API errors encountered',
            ['service', 'error_type']
        )
        
        # Risk metrics
        self.risk_checks_failed = Counter(
            'trading_risk_checks_failed',
            'Number of failed risk checks',
            ['check_type']
        )
        
        self.circuit_breaker_activations = Counter(
            'trading_circuit_breaker_activations',
            'Circuit breaker activations',
            ['reason']
        )
    
    def start_server(self, port: int = None):
        """Start Prometheus metrics server"""
        port = port or settings.monitoring.prometheus_port
        try:
            start_http_server(port)
            logger.info(f"Started Prometheus metrics server on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    
    # Helper methods for common operations
    def record_trade(self, symbol: str, side: str, status: str, pnl: float = None):
        """Record a trade execution"""
        self.trades_total.labels(symbol=symbol, side=side, status=status).inc()
        if pnl is not None:
            self.trade_pnl.labels(symbol=symbol).observe(pnl)
    
    def update_portfolio(self, value: float, daily_pnl: float, drawdown: float):
        """Update portfolio metrics"""
        self.portfolio_value.set(value)
        self.daily_pnl.set(daily_pnl)
        self.drawdown.set(drawdown)
    
    def update_position(self, symbol: str, size: float):
        """Update position size"""
        self.position_size.labels(symbol=symbol).set(size)
    
    def record_signal(self, symbol: str, signal_type: str, strategy: str, strength: float):
        """Record signal generation"""
        self.signals_generated.labels(
            symbol=symbol,
            signal_type=signal_type,
            strategy=strategy
        ).inc()
        self.signal_strength.labels(symbol=symbol).observe(strength)
    
    def record_market_data(self, symbol: str, source: str):
        """Record market data update"""
        self.market_data_updates.labels(symbol=symbol, source=source).inc()
    
    def record_news(self, source: str):
        """Record news item"""
        self.news_items.labels(source=source).inc()
    
    def record_sentiment(self, symbol: str, source: str, score: float):
        """Record sentiment analysis"""
        self.sentiment_score.labels(symbol=symbol, source=source).observe(score)
    
    def record_execution_latency(self, exchange: str, latency: float):
        """Record order execution latency"""
        self.execution_latency.labels(exchange=exchange).observe(latency)
    
    def record_api_error(self, service: str, error_type: str):
        """Record API error"""
        self.api_errors.labels(service=service, error_type=error_type).inc()
    
    def record_risk_check_failure(self, check_type: str):
        """Record risk check failure"""
        self.risk_checks_failed.labels(check_type=check_type).inc()
    
    def record_circuit_breaker(self, reason: str):
        """Record circuit breaker activation"""
        self.circuit_breaker_activations.labels(reason=reason).inc()


# Global metrics collector instance
metrics = MetricsCollector()
