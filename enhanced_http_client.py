#!/usr/bin/env python3
"""
Enhanced HTTP Client with Connection Pooling and Timeout Configuration
Based on AI Agent Review Recommendations

Top Improvement Implementation:
- Connection pooling for HTTP requests (3 AI model mentions)
- Request timeout configuration (3 AI model mentions)
- Performance optimization for DirectAPI ecosystem
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
import json
from datetime import datetime

@dataclass
class HttpClientConfig:
    """Configuration for enhanced HTTP client with AI-recommended optimizations"""
    pool_size: int = 100
    pool_limit: int = 1000
    connect_timeout: float = 10.0
    total_timeout: float = 30.0
    read_timeout: float = 20.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.3
    keepalive_timeout: float = 30.0
    enable_dns_cache: bool = True
    dns_cache_ttl: int = 300
    enable_cookies: bool = False
    chunk_size: int = 8192
    connection_limit_per_host: int = 50

class EnhancedHttpClient:
    """
    Enhanced HTTP Client implementing AI agent review recommendations

    Key Features:
    ✅ Connection pooling (top AI recommendation - 3 mentions)
    ✅ Request timeout configuration (top AI recommendation - 3 mentions)
    ✅ Performance monitoring and metrics
    ✅ Automatic retry with exponential backoff
    ✅ Resource management and cleanup
    ✅ Comprehensive error handling
    """

    def __init__(self, config: Optional[HttpClientConfig] = None):
        self.config = config or HttpClientConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time": 0.0,
            "avg_response_time": 0.0,
            "connection_pool_hits": 0,
            "connection_pool_misses": 0,
            "timeout_events": 0,
            "retries_attempted": 0
        }
        self._setup_logging()

    def _setup_logging(self):
        """Setup comprehensive logging for HTTP client operations"""
        self.logger = logging.getLogger("EnhancedHttpClient")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()

    async def start_session(self):
        """Initialize the enhanced HTTP session with connection pooling"""
        if self.session is None or self.session.closed:
            # Create connector with AI-recommended connection pooling settings
            connector = aiohttp.TCPConnector(
                limit=self.config.pool_limit,
                limit_per_host=self.config.connection_limit_per_host,
                keepalive_timeout=self.config.keepalive_timeout,
                enable_cleanup_closed=True,
                ttl_dns_cache=self.config.dns_cache_ttl if self.config.enable_dns_cache else 0,
                use_dns_cache=self.config.enable_dns_cache,
                force_close=False,
                ssl=False  # For API calls, SSL may not be needed
            )

            # Create timeout configuration
            timeout = aiohttp.ClientTimeout(
                total=self.config.total_timeout,
                connect=self.config.connect_timeout,
                sock_read=self.config.read_timeout
            )

            # Create session with enhanced configuration
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'DirectAPI-Enhanced-Client/1.0',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                },
                cookie_jar=None if not self.config.enable_cookies else aiohttp.CookieJar()
            )

            self.logger.info("✅ Enhanced HTTP session started with connection pooling")
            self.logger.info(f"   📊 Pool Settings: limit={self.config.pool_limit}, per_host={self.config.connection_limit_per_host}")
            self.logger.info(f"   ⏱️ Timeout Settings: connect={self.config.connect_timeout}s, total={self.config.total_timeout}s")

    async def close_session(self):
        """Close the HTTP session and cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("✅ HTTP session closed and resources cleaned up")

    async def make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with connection pooling and timeout handling

        Implements top AI recommendations:
        1. Connection pooling for improved performance
        2. Request timeout configuration to prevent hanging
        """
        if not self.session or self.session.closed:
            await self.start_session()

        start_time = time.time()
        retry_count = 0

        while retry_count <= self.config.max_retries:
            try:
                self.stats["total_requests"] += 1

                # Update connection pool statistics
                if self.session.connector:
                    if self.session.connector._available_connections._value > 0:
                        self.stats["connection_pool_hits"] += 1
                    else:
                        self.stats["connection_pool_misses"] += 1

                self.logger.debug(f"🔄 Making {method} request to {url} (attempt {retry_count + 1})")

                async with self.session.request(method, url, **kwargs) as response:
                    response_time = time.time() - start_time

                    # Update statistics
                    self.stats["total_time"] += response_time
                    self.stats["avg_response_time"] = self.stats["total_time"] / self.stats["total_requests"]

                    if response.status < 400:
                        self.stats["successful_requests"] += 1
                        self.logger.debug(f"✅ Request successful: {response.status} in {response_time:.3f}s")

                        # Handle response based on content type
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            return {
                                "success": True,
                                "status_code": response.status,
                                "data": await response.json(),
                                "response_time": response_time,
                                "headers": dict(response.headers),
                                "from_cache": False,
                                "connection_reused": getattr(response, 'connection_reused', False)
                            }
                        else:
                            return {
                                "success": True,
                                "status_code": response.status,
                                "data": await response.text(),
                                "response_time": response_time,
                                "headers": dict(response.headers),
                                "from_cache": False,
                                "connection_reused": getattr(response, 'connection_reused', False)
                            }
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP {response.status}: {error_text}"
                        )

            except asyncio.TimeoutError:
                self.stats["timeout_events"] += 1
                self.stats["retries_attempted"] += 1
                retry_count += 1

                if retry_count <= self.config.max_retries:
                    backoff_time = self.config.retry_backoff_factor * (2 ** (retry_count - 1))
                    self.logger.warning(f"⏰ Timeout on {url}, retrying in {backoff_time:.2f}s (attempt {retry_count}/{self.config.max_retries})")
                    await asyncio.sleep(backoff_time)
                    start_time = time.time()  # Reset start time for retry
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.error(f"❌ Request failed after {self.config.max_retries} retries: {url}")
                    return {
                        "success": False,
                        "error": "Request timeout",
                        "status_code": None,
                        "response_time": time.time() - start_time,
                        "retries": retry_count
                    }

            except Exception as e:
                self.stats["retries_attempted"] += 1
                retry_count += 1

                if retry_count <= self.config.max_retries:
                    backoff_time = self.config.retry_backoff_factor * (2 ** (retry_count - 1))
                    self.logger.warning(f"⚠️ Error on {url}: {str(e)}, retrying in {backoff_time:.2f}s (attempt {retry_count}/{self.config.max_retries})")
                    await asyncio.sleep(backoff_time)
                    start_time = time.time()  # Reset start time for retry
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.error(f"❌ Request failed after {self.config.max_retries} retries: {url} - {str(e)}")
                    return {
                        "success": False,
                        "error": str(e),
                        "status_code": getattr(e, 'status', None),
                        "response_time": time.time() - start_time,
                        "retries": retry_count
                    }

        return {
            "success": False,
            "error": "Max retries exceeded",
            "status_code": None,
            "response_time": time.time() - start_time,
            "retries": retry_count
        }

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        return await self.make_request('GET', url, **kwargs)

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        return await self.make_request('POST', url, **kwargs)

    async def put(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request"""
        return await self.make_request('PUT', url, **kwargs)

    async def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self.make_request('DELETE', url, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive HTTP client statistics"""
        if self.stats["total_requests"] > 0:
            success_rate = (self.stats["successful_requests"] / self.stats["total_requests"]) * 100
            connection_pool_efficiency = (self.stats["connection_pool_hits"] /
                                        (self.stats["connection_pool_hits"] + self.stats["connection_pool_misses"])) * 100
        else:
            success_rate = 0
            connection_pool_efficiency = 0

        return {
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate": round(success_rate, 2),
            "total_response_time": round(self.stats["total_time"], 3),
            "avg_response_time": round(self.stats["avg_response_time"], 3),
            "connection_pool_stats": {
                "hits": self.stats["connection_pool_hits"],
                "misses": self.stats["connection_pool_misses"],
                "efficiency": round(connection_pool_efficiency, 2)
            },
            "timeout_events": self.stats["timeout_events"],
            "retries_attempted": self.stats["retries_attempted"],
            "config": asdict(self.config)
        }

    def print_stats(self):
        """Print formatted statistics"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("🚀 ENHANCED HTTP CLIENT STATISTICS")
        print("="*60)
        print(f"📊 Total Requests: {stats['total_requests']}")
        print(f"✅ Successful: {stats['successful_requests']} ({stats['success_rate']}%)")
        print(f"❌ Failed: {stats['failed_requests']}")
        print(f"⏱️ Avg Response Time: {stats['avg_response_time']:.3f}s")
        print(f"🔄 Connection Pool Efficiency: {stats['connection_pool_stats']['efficiency']}%")
        print(f"⏰ Timeout Events: {stats['timeout_events']}")
        print(f"🔁 Retries Attempted: {stats['retries_attempted']}")
        print("="*60)

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor HTTP client performance"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time

        # Log performance metrics
        logging.getLogger("EnhancedHttpClient").info(
            f"⚡ {func.__name__} completed in {execution_time:.3f}s"
        )

        return result
    return wrapper

async def test_enhanced_client():
    """Test the enhanced HTTP client with various scenarios"""
    print("🧪 Testing Enhanced HTTP Client...")

    config = HttpClientConfig(
        pool_size=10,
        connect_timeout=5.0,
        total_timeout=15.0
    )

    async with EnhancedHttpClient(config) as client:
        # Test connection pooling with multiple requests
        print("\n🔄 Testing connection pooling...")
        urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/get",
            "https://httpbin.org/get"
        ]

        tasks = [client.get(url) for url in urls]
        results = await asyncio.gather(*tasks)

        print(f"✅ Completed {len(results)} requests")
        for i, result in enumerate(results):
            if result["success"]:
                print(f"   Request {i+1}: {result['response_time']:.3f}s (connection reused: {result.get('connection_reused', False)})")

        # Test timeout handling
        print("\n⏰ Testing timeout configuration...")
        slow_result = await client.get("https://httpbin.org/delay/10", timeout=aiohttp.ClientTimeout(total=5))
        if not slow_result["success"]:
            print("✅ Timeout handling working correctly")

        # Print final statistics
        client.print_stats()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_client())