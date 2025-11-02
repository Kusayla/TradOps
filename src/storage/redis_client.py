"""Redis client for caching and online feature store"""
import json
from typing import Any, Dict, Optional, List
import redis
from loguru import logger

from src.config import settings


class RedisClient:
    """Redis client for caching and real-time features"""
    
    def __init__(self):
        self.client = None
        self.pubsub = None
    
    def initialize(self):
        """Initialize Redis connection"""
        try:
            password = settings.database.redis_password or None
            self.client = redis.Redis(
                host=settings.database.redis_host,
                port=settings.database.redis_port,
                password=password,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            logger.info("Initialized Redis client")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    def set(self, key: str, value: Any, expiry: int = None):
        """Set a key-value pair"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.client.set(key, value, ex=expiry)
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
    
    def delete(self, key: str):
        """Delete a key"""
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key}: {e}")
            return False
    
    def set_hash(self, name: str, mapping: Dict):
        """Set hash fields"""
        try:
            # Convert dict values to JSON strings
            json_mapping = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                           for k, v in mapping.items()}
            self.client.hset(name, mapping=json_mapping)
        except Exception as e:
            logger.error(f"Error setting hash {name}: {e}")
    
    def get_hash(self, name: str) -> Dict:
        """Get all hash fields"""
        try:
            data = self.client.hgetall(name)
            # Try to parse JSON values
            return {
                k: json.loads(v) if v.startswith('{') or v.startswith('[') else v
                for k, v in data.items()
            }
        except Exception as e:
            logger.error(f"Error getting hash {name}: {e}")
            return {}
    
    def cache_latest_price(self, symbol: str, price: float):
        """Cache latest price"""
        self.set(f"price:{symbol}", price, expiry=60)  # 1 minute expiry
    
    def get_cached_price(self, symbol: str) -> Optional[float]:
        """Get cached price"""
        price = self.get(f"price:{symbol}")
        return float(price) if price else None
    
    def cache_signal(self, symbol: str, signal: Dict):
        """Cache trading signal"""
        self.set(f"signal:{symbol}", signal, expiry=300)  # 5 minutes
    
    def get_cached_signal(self, symbol: str) -> Optional[Dict]:
        """Get cached signal"""
        return self.get(f"signal:{symbol}")
    
    def set_position(self, symbol: str, position: Dict):
        """Store current position"""
        self.set_hash(f"position:{symbol}", position)
    
    def get_position(self, symbol: str) -> Dict:
        """Get current position"""
        return self.get_hash(f"position:{symbol}")
    
    def get_all_positions(self) -> Dict[str, Dict]:
        """Get all positions"""
        positions = {}
        for key in self.client.scan_iter("position:*"):
            symbol = key.split(":")[-1]
            positions[symbol] = self.get_position(symbol)
        return positions
    
    def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """Acquire distributed lock"""
        try:
            return self.client.set(f"lock:{lock_name}", "1", nx=True, ex=timeout)
        except Exception as e:
            logger.error(f"Error acquiring lock {lock_name}: {e}")
            return False
    
    def release_lock(self, lock_name: str):
        """Release distributed lock"""
        self.delete(f"lock:{lock_name}")
    
    def publish(self, channel: str, message: Any):
        """Publish message to channel"""
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
    
    def subscribe(self, channels: List[str]):
        """Subscribe to channels"""
        try:
            self.pubsub = self.client.pubsub()
            self.pubsub.subscribe(*channels)
            return self.pubsub
        except Exception as e:
            logger.error(f"Error subscribing to channels: {e}")
            return None
    
    def close(self):
        """Close Redis connection"""
        if self.pubsub:
            self.pubsub.close()
        if self.client:
            self.client.close()
            logger.info("Closed Redis connection")
