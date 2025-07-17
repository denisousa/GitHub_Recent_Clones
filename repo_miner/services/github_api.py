import requests
import time
import json
import os
from typing import Optional, Dict, Any
from setup.config import HEADERS, SLEEP_ON_RATE_LIMIT

class GitHubAPIService:
    """Base service for interactions with the GitHub API"""
    
    def __init__(self):
        self.headers = HEADERS
        self.base_url = "https://api.github.com"
        data_dir = ".data"
        os.makedirs(data_dir, exist_ok=True)
        self.cache_file = os.path.join(data_dir, "api_cache.json")
        self.cache = self._load_cache()
        self.request_count = 0
        self.start_time = time.time()
    
    def _load_cache(self) -> dict:
        """Loads the request cache from previous sessions"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    print(f"📋 Cache loaded: {len(cache_data)} entries")
                    return cache_data
            except Exception as e:
                print(f"⚠️ Error loading cache: {e}")
                return {}
        return {}
    
    def _save_cache(self) -> None:
        """Saves the cache to a file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
            print(f"💾 Cache saved: {len(self.cache)} entries")
        except Exception as e:
            print(f"❌ Error saving cache: {e}")
    
    def _get_cache_key(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generates a unique key for caching"""
        key = url
        if params:
            sorted_params = sorted(params.items())
            key += "?" + "&".join([f"{k}={v}" for k, v in sorted_params])
        return key
    
    def make_request(self, url: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Optional[requests.Response]:
        """Makes a request to the GitHub API with caching and rate limit handling"""
        cache_key = self._get_cache_key(url, params)
        
        # Check cache first
        if use_cache and cache_key in self.cache:
            print(f"  📋 Cache hit: {url.split('/')[-1]}")
            # Simulate a response object for compatibility
            cached_response = requests.Response()
            cached_response.status_code = 200
            cached_response._content = json.dumps(self.cache[cache_key]).encode()
            return cached_response
        
        try:
            # Monitor rate limit
            self._check_rate_limit()
            
            response = requests.get(url, headers=self.headers, params=params)
            self.request_count += 1
            
            # Log the request
            elapsed = time.time() - self.start_time
            print(f"  🌐 API call #{self.request_count} ({elapsed:.1f}s): {url.split('/')[-1]}")
            
            # Handle rate limit
            if response.status_code == 403:
                rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                if rate_limit_remaining == 0:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))
                    sleep_duration = max(reset_time - time.time() + 10, SLEEP_ON_RATE_LIMIT)
                    print(f"⚠️ Rate limit exceeded! Waiting for {sleep_duration/60:.1f} minutes...")
                    time.sleep(sleep_duration)
                    return self.make_request(url, params, use_cache)
            
            # Handle other HTTP errors that might indicate rate limiting
            elif response.status_code == 429:  # Too Many Requests
                print(f"⚠️ Secondary rate limit (429)! Waiting for {SLEEP_ON_RATE_LIMIT} seconds...")
                time.sleep(SLEEP_ON_RATE_LIMIT)
                return self.make_request(url, params, use_cache)
            
            # Cache successful response
            if response.status_code == 200 and use_cache:
                self.cache[cache_key] = response.json()
                # Save cache every 10 requests
                if self.request_count % 10 == 0:
                    self._save_cache()
            
            return response
        except Exception as e:
            print(f"❌ Error during request: {str(e)}")
            print(f"🔄 Waiting for {SLEEP_ON_RATE_LIMIT} seconds before continuing...")
            time.sleep(SLEEP_ON_RATE_LIMIT)
            return None
    
    def _check_rate_limit(self):
        """Checks if we are approaching the rate limit"""
        if self.request_count > 0 and self.request_count % 100 == 0:
            elapsed = time.time() - self.start_time
            rate = self.request_count / (elapsed / 3600)  # req/hour
            print(f"📊 Current rate: {rate:.0f} req/hour (limit: 5000)")
            
            if rate > 4500:  # 90% of the limit
                print(f"⚠️ Approaching rate limit, pausing for {SLEEP_ON_RATE_LIMIT} seconds...")
                time.sleep(SLEEP_ON_RATE_LIMIT)
        
        # Add a preventive delay between requests if configured
        if SLEEP_ON_RATE_LIMIT > 0 and self.request_count % 50 == 0:
            time.sleep(min(SLEEP_ON_RATE_LIMIT, 2))  # Max 2 seconds of preventive delay
    
    def get_json_response(self, url: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Optional[Any]:
        """Makes a request and returns the JSON from the response"""
        response = self.make_request(url, params, use_cache)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def finalize(self):
        """Finalizes and saves the cache"""
        self._save_cache()
        elapsed = time.time() - self.start_time
        print(f"\n📈 Final statistics:")
        print(f"   Total requests: {self.request_count}")
        print(f"   Total time: {elapsed/60:.1f} minutes")
        if elapsed > 0:
            print(f"   Average rate: {self.request_count/(elapsed/3600):.0f} req/hour")