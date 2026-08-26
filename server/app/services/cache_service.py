import hashlib
import time
from typing import Optional, Dict, Any
from app.core.logger import logger

class PredictionCacheService:
    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 500):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def compute_image_hash(image_bytes: bytes) -> str:
        """Computes deterministic SHA-256 hash of image binary data."""
        return hashlib.sha256(image_bytes).hexdigest()

    def get(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached prediction if present and not expired."""
        if image_hash in self._cache:
            entry = self._cache[image_hash]
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                logger.info(f"⚡ Cache Hit for image SHA-256: {image_hash[:12]}...")
                return entry["data"]
            else:
                # Expired
                del self._cache[image_hash]
        return None

    def set(self, image_hash: str, prediction_data: Dict[str, Any]) -> None:
        """Stores prediction result in cache with timestamp and LRU eviction."""
        if len(self._cache) >= self.max_entries:
            # Evict oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]

        self._cache[image_hash] = {
            "data": prediction_data,
            "timestamp": time.time()
        }
        logger.info(f"Cached prediction entry for SHA-256: {image_hash[:12]}... (Total cached: {len(self._cache)})")

cache_service = PredictionCacheService()