"""Configuration management using Pydantic"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class ExchangeConfig(BaseSettings):
    """Exchange API configuration - Multi-exchange support"""
    
    # Default exchange selection
    # Options: bybit, okx, kucoin, kraken, binance, coinbase
    default_exchange: str = Field(default="bybit", alias="DEFAULT_EXCHANGE")
    
    # Bybit (RECOMMENDED)
    bybit_api_key: str = Field(default="", alias="BYBIT_API_KEY")
    bybit_api_secret: str = Field(default="", alias="BYBIT_API_SECRET")
    bybit_testnet: bool = Field(default=True, alias="BYBIT_TESTNET")
    
    # OKX
    okx_api_key: str = Field(default="", alias="OKX_API_KEY")
    okx_api_secret: str = Field(default="", alias="OKX_API_SECRET")
    okx_passphrase: str = Field(default="", alias="OKX_PASSPHRASE")
    okx_testnet: bool = Field(default=True, alias="OKX_TESTNET")
    
    # KuCoin
    kucoin_api_key: str = Field(default="", alias="KUCOIN_API_KEY")
    kucoin_api_secret: str = Field(default="", alias="KUCOIN_API_SECRET")
    kucoin_passphrase: str = Field(default="", alias="KUCOIN_PASSPHRASE")
    
    # Kraken
    kraken_api_key: str = Field(default="", alias="KRAKEN_API_KEY")
    kraken_api_secret: str = Field(default="", alias="KRAKEN_API_SECRET")
    
    # Binance (optional, legacy support)
    binance_api_key: str = Field(default="", alias="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", alias="BINANCE_API_SECRET")
    binance_testnet: bool = Field(default=True, alias="BINANCE_TESTNET")
    
    # Coinbase (optional, legacy support)
    coinbase_api_key: str = Field(default="", alias="COINBASE_API_KEY")
    coinbase_api_secret: str = Field(default="", alias="COINBASE_API_SECRET")
    
    @property
    def has_api_keys(self) -> bool:
        """Check if any API keys are configured for the default exchange"""
        exchange = self.default_exchange.lower()
        
        if exchange == 'bybit':
            return bool(self.bybit_api_key and self.bybit_api_secret)
        elif exchange == 'okx':
            return bool(self.okx_api_key and self.okx_api_secret)
        elif exchange == 'kucoin':
            return bool(self.kucoin_api_key and self.kucoin_api_secret)
        elif exchange == 'kraken':
            return bool(self.kraken_api_key and self.kraken_api_secret)
        elif exchange == 'binance':
            return bool(self.binance_api_key and self.binance_api_secret)
        elif exchange == 'coinbase':
            return bool(self.coinbase_api_key and self.coinbase_api_secret)
        
        return False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class DataSourceConfig(BaseSettings):
    """External data sources configuration"""
    # Social Media
    twitter_api_key: str = Field(default="", alias="TWITTER_API_KEY")
    twitter_api_secret: str = Field(default="", alias="TWITTER_API_SECRET")
    twitter_bearer_token: str = Field(default="", alias="TWITTER_BEARER_TOKEN")
    
    # News & Social Analytics
    lunarcrush_api_key: str = Field(default="", alias="LUNARCRUSH_API_KEY")
    cryptopanic_api_key: str = Field(default="", alias="CRYPTOPANIC_API_KEY")
    newsapi_key: str = Field(default="", alias="NEWSAPI_KEY")
    
    # Public Market Data (free/no keys required for basic usage)
    coingecko_api_key: str = Field(default="", alias="COINGECKO_API_KEY")  # Optional, for higher limits
    cryptocompare_api_key: str = Field(default="", alias="CRYPTOCOMPARE_API_KEY")  # Optional
    
    # LLM APIs (for advanced tweet analysis)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")  # ChatGPT
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")  # Claude
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")  # openai, anthropic, ollama
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")  # gpt-4o-mini, gpt-3.5-turbo, etc.
    # Ollama: local, no key needed
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    timescaledb_host: str = Field(default="localhost", alias="TIMESCALEDB_HOST")
    timescaledb_port: int = Field(default=5432, alias="TIMESCALEDB_PORT")
    timescaledb_db: str = Field(default="trading_db", alias="TIMESCALEDB_DB")
    timescaledb_user: str = Field(default="postgres", alias="TIMESCALEDB_USER")
    timescaledb_password: str = Field(default="postgres", alias="TIMESCALEDB_PASSWORD")
    
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    
    @property
    def timescaledb_url(self) -> str:
        return f"postgresql://{self.timescaledb_user}:{self.timescaledb_password}@{self.timescaledb_host}:{self.timescaledb_port}/{self.timescaledb_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class StreamingConfig(BaseSettings):
    """Streaming configuration"""
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class MLConfig(BaseSettings):
    """ML configuration"""
    mlflow_tracking_uri: str = Field(default="http://localhost:5000", alias="MLFLOW_TRACKING_URI")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class MonitoringConfig(BaseSettings):
    """Monitoring configuration"""
    prometheus_port: int = Field(default=8000, alias="PROMETHEUS_PORT")
    grafana_url: str = Field(default="http://localhost:3000", alias="GRAFANA_URL")
    
    slack_webhook_url: str = Field(default="", alias="SLACK_WEBHOOK_URL")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class RiskConfig(BaseSettings):
    """Risk management configuration"""
    max_position_size: float = Field(default=0.1, alias="MAX_POSITION_SIZE")
    max_daily_loss: float = Field(default=0.05, alias="MAX_DAILY_LOSS")
    max_drawdown: float = Field(default=0.15, alias="MAX_DRAWDOWN")
    stop_loss_atr_multiplier: float = Field(default=2.0, alias="STOP_LOSS_ATR_MULTIPLIER")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class TradingConfig(BaseSettings):
    """Trading configuration"""
    # Trading mode: public (free data + paper), testnet (exchange testnet), live (real money)
    trading_mode: str = Field(default="public", alias="TRADING_MODE")
    
    # Assets to trade
    whitelisted_assets: str = Field(default="BTC/USDT,ETH/USDT,SOL/USDT", alias="WHITELISTED_ASSETS")
    
    # Initial capital for paper/testnet trading
    initial_capital: float = Field(default=10000.0, alias="INITIAL_CAPITAL")
    
    # Simulation parameters (for paper trading)
    simulated_slippage: float = Field(default=0.001, alias="SIMULATED_SLIPPAGE")  # 0.1%
    simulated_fees: float = Field(default=0.001, alias="SIMULATED_FEES")  # 0.1%
    
    @property
    def assets_list(self) -> List[str]:
        return [asset.strip() for asset in self.whitelisted_assets.split(",")]
    
    @property
    def is_paper_trading(self) -> bool:
        """Check if in paper/public mode (no real money)"""
        return self.trading_mode.lower() in ['paper', 'public']
    
    @property
    def is_testnet(self) -> bool:
        """Check if using exchange testnet"""
        return self.trading_mode.lower() == 'testnet'
    
    @property
    def is_live(self) -> bool:
        """Check if trading with real money"""
        return self.trading_mode.lower() == 'live'
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class Settings(BaseSettings):
    """Main settings aggregator"""
    exchange: ExchangeConfig = ExchangeConfig()
    data_sources: DataSourceConfig = DataSourceConfig()
    database: DatabaseConfig = DatabaseConfig()
    streaming: StreamingConfig = StreamingConfig()
    ml: MLConfig = MLConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    risk: RiskConfig = RiskConfig()
    trading: TradingConfig = TradingConfig()
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
