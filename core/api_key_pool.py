import random
from threading import Lock
from typing import List, Dict
from core.config_utils import load_key, update_key

class APIKeyPool:
    def __init__(self):
        self._lock = Lock()
        self._current_index = 0
        self._usage_stats: Dict[str, int] = {}
        
    def _load_api_keys(self) -> List[str]:
        """Load API keys from config"""
        try:
            api_keys = load_key("api.google_ai.api_keys")
            if not isinstance(api_keys, list):
                return [api_keys] if api_keys else []
            return [key for key in api_keys if key]
        except KeyError:
            print ("api_keys is not a list")
            return []
            
    def get_next_api_key(self) -> str:
        """Get next available API key using round-robin strategy"""
        with self._lock:
            api_keys = self._load_api_keys()
            if not api_keys:
                raise ValueError("No API keys available")
                
            # Round-robin selection
            key = api_keys[self._current_index % len(api_keys)]
            self._current_index = (self._current_index + 1) % len(api_keys)
            
            # Update usage statistics
            self._usage_stats[key] = self._usage_stats.get(key, 0) + 1
            
            return key
            
    def get_random_api_key(self) -> str:
        """Get random API key from the pool"""
        with self._lock:
            api_keys = self._load_api_keys()
            if not api_keys:
                raise ValueError("No API keys available")
            key = random.choice(api_keys)
            self._usage_stats[key] = self._usage_stats.get(key, 0) + 1
            return key
            
    def get_least_used_api_key(self) -> str:
        """Get the least used API key from the pool"""
        with self._lock:
            api_keys = self._load_api_keys()
            if not api_keys:
                raise ValueError("No API keys available")
                
            # Find least used key
            min_usage = float('inf')
            least_used_key = api_keys[0]
            
            for key in api_keys:
                usage = self._usage_stats.get(key, 0)
                if usage < min_usage:
                    min_usage = usage
                    least_used_key = key
                    
            self._usage_stats[least_used_key] = min_usage + 1
            return least_used_key
            
    def get_usage_stats(self) -> Dict[str, int]:
        """Get current usage statistics for all keys"""
        return dict(self._usage_stats)

# Global instance
api_key_pool = APIKeyPool()