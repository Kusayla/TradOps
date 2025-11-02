"""Configuration management using Pydantic"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class ExchangeConfig(BaseSettings):
    """Exchange API configuration"""
    binance_api_key: str = Field(default="", alias="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", alias="BINANCE_API_SECRET")
    binance_testnet: bool = Field(default=True, alias="BINANCE_TESTNET")
    
    coinbase_api_key: str = Field(default="", alias="COINBASE_API_KEY")
    coinbase_api_secret: str = Field(default="", alias="COINBASE_API_SECRET")
    
    default_exchange: str = Field(default="binance", alias="DEFAULT_EXCHANGE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class DataSourceConfig(BaseSettings):
    """External data sources configuration"""
    twitter_api_key: str = Field(default="", alias="TWITTER_API_KEY")
    twitter_api_secret: str = Field(default="", alias="TWITTER_API_SECRET")
    twitter_bearer_token: str = Field(default="", alias="TWITTER_BEARER_TOKEN")
    
    lunarcrush_api_key: str = Field(default="", alias="LUNARCRUSH_API_KEY")
    cryptopanic_api_key: str = Field(default="", alias="CRYPTOPANIC_API_KEY")
    newsapi_key: str = Field(default="", alias="NEWSAPI_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


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


class StreamingConfig(BaseSettings):
    """Streaming configuration"""
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class MLConfig(BaseSettings):
    """ML configuration"""
    mlflow_tracking_uri: str = Field(default="http://localhost:5000", alias="MLFLOW_TRACKING_URI")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


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


class RiskConfig(BaseSettings):
    """Risk management configuration"""
    max_position_size: float = Field(default=0.1, alias="MAX_POSITION_SIZE")
    max_daily_loss: float = Field(default=0.05, alias="MAX_DAILY_LOSS")
    max_drawdown: float = Field(default=0.15, alias="MAX_DRAWDOWN")
    stop_loss_atr_multiplier: float = Field(default=2.0, alias="STOP_LOSS_ATR_MULTIPLIER")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class TradingConfig(BaseSettings):
    """Trading configuration"""
    trading_mode: str = Field(default="paper", alias="TRADING_MODE")  # paper or live
    whitelisted_assets: str = Field(default="BTC/USDT,ETH/USDT,SOL/USDT", alias="WHITELISTED_ASSETS")
    
    @property
    def assets_list(self) -> List[str]:
        return [asset.strip() for asset in self.whitelisted_assets.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


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


# Global settings instance
settings = Settings()
