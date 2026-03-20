import hashlib
import json
import logging
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)


class RedisCachingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
        return cls._instance

    def build_key(self, namespace: str, payload: dict[str, Any]) -> str:
        normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"cache:{namespace}:{digest}"

    def get_json(self, key: str) -> Optional[dict[str, Any]]:
        try:
            value = self.client.get(key)
            if not value:
                return None
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            return json.loads(value)
        except Exception as exc:
            logger.warning("Redis get failed for key=%s error=%s", key, exc)
            return None

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        try:
            payload = json.dumps(value, separators=(",", ":"))
            self.client.setex(key, ttl_seconds, payload)
        except Exception as exc:
            logger.warning("Redis set failed for key=%s error=%s", key, exc)


def get_redis_client():
    return RedisCachingService().client