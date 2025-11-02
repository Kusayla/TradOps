"""Kafka/Redpanda producer for streaming data"""
import json
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError
from loguru import logger

from src.config import settings


class StreamingProducer:
    """Produce messages to Kafka/Redpanda topics"""
    
    def __init__(self):
        self.producer = None
        self.topics = {
            'market_data': 'market_data',
            'news': 'news_feed',
            'social': 'social_signals',
            'signals': 'trading_signals',
            'trades': 'executed_trades',
        }
    
    def initialize(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.streaming.kafka_bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5,
                compression_type='snappy',
            )
            logger.info("Initialized Kafka producer")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def send_market_data(self, data: Dict[str, Any], key: str = None):
        """Send market data to Kafka"""
        self._send(self.topics['market_data'], data, key)
    
    def send_news(self, news: Dict[str, Any], key: str = None):
        """Send news data to Kafka"""
        self._send(self.topics['news'], news, key)
    
    def send_social_signal(self, signal: Dict[str, Any], key: str = None):
        """Send social media signal to Kafka"""
        self._send(self.topics['social'], signal, key)
    
    def send_trading_signal(self, signal: Dict[str, Any], key: str = None):
        """Send trading signal to Kafka"""
        self._send(self.topics['signals'], signal, key)
    
    def send_trade(self, trade: Dict[str, Any], key: str = None):
        """Send executed trade to Kafka"""
        self._send(self.topics['trades'], trade, key)
    
    def _send(self, topic: str, data: Dict[str, Any], key: str = None):
        """Internal send method"""
        try:
            future = self.producer.send(topic, value=data, key=key)
            # Non-blocking: add callback
            future.add_callback(self._on_send_success, topic)
            future.add_errback(self._on_send_error, topic)
        except Exception as e:
            logger.error(f"Error sending to {topic}: {e}")
    
    def _on_send_success(self, record_metadata, topic):
        """Callback on successful send"""
        logger.debug(
            f"Sent to {topic} - partition {record_metadata.partition}, "
            f"offset {record_metadata.offset}"
        )
    
    def _on_send_error(self, excp, topic):
        """Callback on send error"""
        logger.error(f"Failed to send to {topic}: {excp}")
    
    def flush(self):
        """Flush pending messages"""
        if self.producer:
            self.producer.flush()
    
    def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Closed Kafka producer")
