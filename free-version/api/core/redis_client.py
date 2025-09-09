"""
Redis client configuration for Upstash
"""

import os
import redis.asyncio as redis
from typing import Optional, Union
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client with automatic connection management"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """Connect to Redis using Upstash credentials"""
        if self._connected:
            return
        
        try:
            # Upstash Redis URL format: rediss://default:password@host:port
            redis_url = os.getenv("UPSTASH_REDIS_REST_URL") or os.getenv("REDIS_URL")
            
            if not redis_url:
                logger.warning("No Redis URL found. Redis caching will be disabled.")
                return
            
            # Create Redis client
            self.client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.client.ping()
            self._connected = True
            logger.info("✅ Connected to Redis successfully")
            
        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed: {e}")
            self.client = None
            self._connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.aclose()
            self._connected = False
            logger.info("Redis connection closed")
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.client or not self._connected:
            return False
        
        try:
            await self.client.ping()
            return True
        except:
            self._connected = False
            return False
    
    async def set(self, key: str, value: Union[str, dict, list], 
                  expire: Optional[int] = None) -> bool:
        """Set a value in Redis with optional expiration"""
        if not await self.is_connected():
            return False
        
        try:
            # Convert complex types to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Union[str, dict, list]]:
        """Get a value from Redis"""
        if not await self.is_connected():
            return None
        
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        if not await self.is_connected():
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1, 
                       expire: Optional[int] = None) -> Optional[int]:
        """Increment a counter in Redis"""
        if not await self.is_connected():
            return None
        
        try:
            # Use pipeline for atomic increment + expire
            async with self.client.pipeline(transaction=True) as pipe:
                await pipe.incr(key, amount)
                if expire:
                    await pipe.expire(key, expire)
                results = await pipe.execute()
                return results[0]
        except Exception as e:
            logger.error(f"Redis INCREMENT error: {e}")
            return None
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not await self.is_connected():
            return False
        
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

# Global Redis client instance
redis_client = RedisClient()

# Dependency for FastAPI
async def get_redis():
    """Dependency to get Redis client"""
    if not redis_client._connected:
        await redis_client.connect()
    return redis_client