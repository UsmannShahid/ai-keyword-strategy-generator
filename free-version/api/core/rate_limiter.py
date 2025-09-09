"""
Redis-based rate limiter for API endpoints
"""

import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import logging

from core.redis_client import RedisClient

logger = logging.getLogger(__name__)

class RateLimiter:
    """Redis-based rate limiter with different limits for different user plans"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Use user_id from request body if available, otherwise IP
        client_ip = request.client.host
        
        # Try to get user_id from request body for better tracking
        if hasattr(request.state, 'user_id'):
            return f"user:{request.state.user_id}"
        
        return f"ip:{client_ip}"
    
    def _get_rate_limits(self, user_plan: str) -> Dict[str, Dict[str, int]]:
        """Get rate limits for different user plans"""
        return {
            "free": {
                "keywords_per_hour": 5,
                "keywords_per_day": 20,
                "briefs_per_hour": 3,
                "briefs_per_day": 10,
                "requests_per_minute": 30
            },
            "pro": {
                "keywords_per_hour": 50,
                "keywords_per_day": 200,
                "briefs_per_hour": 30,
                "briefs_per_day": 100,
                "requests_per_minute": 120
            },
            "premium": {
                "keywords_per_hour": 200,
                "keywords_per_day": 1000,
                "briefs_per_hour": 100,
                "briefs_per_day": 500,
                "requests_per_minute": 300
            }
        }
    
    async def check_rate_limit(self, request: Request, endpoint: str, 
                             user_plan: str = "free", user_id: str = None) -> bool:
        """
        Check if request is within rate limits
        Returns True if allowed, raises HTTPException if rate limited
        """
        
        # If Redis is not available, allow requests (fail open)
        if not await self.redis.is_connected():
            logger.warning("Redis not available - rate limiting disabled")
            return True
        
        client_id = user_id if user_id else self._get_client_id(request)
        limits = self._get_rate_limits(user_plan)[user_plan]
        
        # Check different time windows
        now = int(time.time())
        checks = []
        
        # General requests per minute
        minute_key = f"rate_limit:{client_id}:requests:minute:{now // 60}"
        checks.append((minute_key, limits["requests_per_minute"], 60, "Too many requests"))
        
        # Endpoint-specific limits
        if endpoint == "keywords":
            hour_key = f"rate_limit:{client_id}:keywords:hour:{now // 3600}"
            day_key = f"rate_limit:{client_id}:keywords:day:{now // 86400}"
            
            checks.extend([
                (hour_key, limits["keywords_per_hour"], 3600, "Keyword search limit exceeded"),
                (day_key, limits["keywords_per_day"], 86400, "Daily keyword limit exceeded")
            ])
            
        elif endpoint == "briefs":
            hour_key = f"rate_limit:{client_id}:briefs:hour:{now // 3600}"
            day_key = f"rate_limit:{client_id}:briefs:day:{now // 86400}"
            
            checks.extend([
                (hour_key, limits["briefs_per_hour"], 3600, "Brief generation limit exceeded"),
                (day_key, limits["briefs_per_day"], 86400, "Daily brief limit exceeded")
            ])
        
        # Perform all rate limit checks
        for key, limit, window, error_message in checks:
            count = await self.redis.increment(key, 1, window)
            
            if count and count > limit:
                # Calculate retry after
                retry_after = window - (now % window)
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": error_message,
                        "limit": limit,
                        "window": window,
                        "retry_after": retry_after,
                        "plan": user_plan,
                        "upgrade_message": "Upgrade your plan for higher limits" if user_plan == "free" else None
                    },
                    headers={"Retry-After": str(retry_after)}
                )
        
        return True
    
    async def get_usage_stats(self, user_id: str, user_plan: str = "free") -> Dict[str, Any]:
        """Get current usage statistics for a user"""
        
        if not await self.redis.is_connected():
            return {"redis_available": False}
        
        now = int(time.time())
        client_id = f"user:{user_id}"
        limits = self._get_rate_limits(user_plan)[user_plan]
        
        # Get current usage counts
        usage = {}
        
        # Keywords
        keywords_hour_key = f"rate_limit:{client_id}:keywords:hour:{now // 3600}"
        keywords_day_key = f"rate_limit:{client_id}:keywords:day:{now // 86400}"
        
        keywords_hour = await self.redis.get(keywords_hour_key) or 0
        keywords_day = await self.redis.get(keywords_day_key) or 0
        
        usage["keywords"] = {
            "hour": {"used": int(keywords_hour), "limit": limits["keywords_per_hour"]},
            "day": {"used": int(keywords_day), "limit": limits["keywords_per_day"]}
        }
        
        # Briefs
        briefs_hour_key = f"rate_limit:{client_id}:briefs:hour:{now // 3600}"
        briefs_day_key = f"rate_limit:{client_id}:briefs:day:{now // 86400}"
        
        briefs_hour = await self.redis.get(briefs_hour_key) or 0
        briefs_day = await self.redis.get(briefs_day_key) or 0
        
        usage["briefs"] = {
            "hour": {"used": int(briefs_hour), "limit": limits["briefs_per_hour"]},
            "day": {"used": int(briefs_day), "limit": limits["briefs_per_day"]}
        }
        
        # Requests
        requests_minute_key = f"rate_limit:{client_id}:requests:minute:{now // 60}"
        requests_minute = await self.redis.get(requests_minute_key) or 0
        
        usage["requests"] = {
            "minute": {"used": int(requests_minute), "limit": limits["requests_per_minute"]}
        }
        
        return {
            "user_id": user_id,
            "plan": user_plan,
            "usage": usage,
            "redis_available": True
        }
    
    async def reset_user_limits(self, user_id: str) -> bool:
        """Reset all rate limits for a user (admin function)"""
        
        if not await self.redis.is_connected():
            return False
        
        now = int(time.time())
        client_id = f"user:{user_id}"
        
        # List of keys to delete
        keys_to_delete = [
            f"rate_limit:{client_id}:keywords:hour:{now // 3600}",
            f"rate_limit:{client_id}:keywords:day:{now // 86400}",
            f"rate_limit:{client_id}:briefs:hour:{now // 3600}",
            f"rate_limit:{client_id}:briefs:day:{now // 86400}",
            f"rate_limit:{client_id}:requests:minute:{now // 60}"
        ]
        
        for key in keys_to_delete:
            await self.redis.delete(key)
        
        logger.info(f"Reset rate limits for user: {user_id}")
        return True