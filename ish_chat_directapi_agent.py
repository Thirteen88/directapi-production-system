#!/usr/bin/env python3
"""
ish.chat DirectAPI Agent
High-performance DirectAPI agent for ish.chat service
Based on successful eqing.tech DirectAPI implementation
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class IshChatTask:
    """ish.chat API task definition"""
    prompt: str
    model: str = "claude-3.5-sonnet"
    max_tokens: int = 2000
    temperature: float = 0.7
    system_prompt: Optional[str] = None

class IshChatDirectAPIAgent:
    """DirectAPI agent for ish.chat service"""

    def __init__(self):
        self.base_url = "https://ish.chat"
        # Try multiple possible API endpoints
        self.api_endpoints = [
            "https://ish.chat/api/chat",
            "https://ish.chat/api/v1/chat/completions",
            "https://ish.chat/v1/chat/completions",
            "https://ish.chat/api/llm",
            "https://ish.chat/chat/api"
        ]

        # Headers based on captured data and successful patterns
        self.headers = {
            'Accept': 'application/json, text/event-stream',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # Remove 'br' to avoid brotli issues
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'https://ish.chat',
            'Referer': 'https://ish.chat/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Ch-UA': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-UA-Mobile': '?0',
            'Sec-Ch-UA-Platform': '"Windows"'
        }

        # Available models on ish.chat
        self.available_models = [
            "claude-3.5-sonnet",
            "claude-3.5-haiku",
            "gpt-4o",
            "gpt-4o-mini",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "llama-3.1-70b",
            "llama-3.1-8b"
        ]

        self.stats = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0.0
        }

    async def initialize(self) -> bool:
        """Initialize the ish.chat DirectAPI agent"""
        logger.info("🚀 Initializing ish.chat DirectAPI Agent...")

        try:
            # Test basic connectivity to ish.chat
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        logger.info("✅ ish.chat connectivity verified")
                        return True
                    else:
                        logger.warning(f"⚠️ ish.chat returned status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to ish.chat: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.available_models

    async def generate_response(self, task: IshChatTask) -> str:
        """Generate response using ish.chat DirectAPI"""
        self.stats["requests"] += 1
        start_time = time.time()

        # Prepare the payload based on ish.chat API structure
        payload = {
            "model": task.model,
            "messages": []
        }

        # Add system message if provided
        if task.system_prompt:
            payload["messages"].append({
                "role": "system",
                "content": task.system_prompt
            })

        # Add user message
        payload["messages"].append({
            "role": "user",
            "content": task.prompt
        })

        # Add generation parameters
        payload.update({
            "max_tokens": task.max_tokens,
            "temperature": task.temperature,
            "stream": False  # Disable streaming for DirectAPI
        })

        logger.info(f"📤 Sending request to ish.chat with model {task.model}")

        # Try each endpoint until one works
        for endpoint in self.api_endpoints:
            try:
                logger.info(f"🔄 Trying endpoint: {endpoint}")

                timeout = aiohttp.ClientTimeout(total=30)  # Shorter timeout for testing
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        endpoint,
                        headers=self.headers,
                        json=payload
                    ) as response:

                        execution_time = time.time() - start_time
                        response_text = await response.text()

                        logger.info(f"📥 Response from {endpoint}: {response.status} in {execution_time:.2f}s")

                        # Handle different response scenarios
                        if response.status == 200:
                            try:
                                response_data = json.loads(response_text)

                                # Extract content from response
                                content = self._extract_content_from_response(response_data)

                                if content:
                                    self.stats["successful"] += 1
                                    self.stats["total_time"] += execution_time
                                    logger.info(f"✅ Response generated successfully ({len(content)} chars)")
                                    return content
                                else:
                                    logger.warning(f"⚠️ No content in response from {endpoint}")
                                    continue  # Try next endpoint

                            except json.JSONDecodeError as e:
                                logger.error(f"❌ JSON decode error from {endpoint}: {e}")
                                continue  # Try next endpoint

                        elif response.status == 403:
                            # 403 might still contain valid data (like eqing.tech)
                            logger.info(f"📥 Got 403 from {endpoint} - checking for response data")
                            try:
                                response_data = json.loads(response_text)
                                content = self._extract_content_from_response(response_data)

                                if content:
                                    self.stats["successful"] += 1
                                    self.stats["total_time"] += execution_time
                                    logger.info(f"✅ Response extracted from 403 ({len(content)} chars)")
                                    return content
                            except:
                                pass

                            logger.warning(f"⚠️ 403 Forbidden from {endpoint} - no usable data")
                            continue  # Try next endpoint

                        elif response.status == 429:
                            logger.warning(f"⚠️ Rate limited (429) from {endpoint}")
                            continue  # Try next endpoint

                        else:
                            logger.warning(f"⚠️ HTTP {response.status} from {endpoint}")
                            continue  # Try next endpoint

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                logger.warning(f"⚠️ Request timeout for {endpoint} after {execution_time:.2f}s")
                continue  # Try next endpoint

            except Exception as e:
                execution_time = time.time() - start_time
                logger.warning(f"⚠️ Request failed for {endpoint}: {e}")
                continue  # Try next endpoint

        # If we get here, all endpoints failed
        execution_time = time.time() - start_time
        logger.error(f"❌ All endpoints failed after {execution_time:.2f}s")
        self.stats["failed"] += 1
        return "Error: All ish.chat endpoints failed - service may be unavailable"

    def _extract_content_from_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extract content from ish.chat response structure"""
        try:
            # Try different response structures
            if "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "text" in choice:
                    return choice["text"]

            elif "content" in response_data:
                return response_data["content"]

            elif "response" in response_data:
                return response_data["response"]

            elif "message" in response_data:
                return response_data["message"]

            elif "data" in response_data:
                data = response_data["data"]
                if isinstance(data, dict) and "content" in data:
                    return data["content"]
                elif isinstance(data, str):
                    return data

            # Last resort: return the whole response as string
            return json.dumps(response_data, indent=2)

        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return None

    async def switch_model(self, model: str) -> bool:
        """Switch to a different model"""
        if model in self.available_models:
            logger.info(f"🔄 Switched to model: {model}")
            return True
        else:
            logger.warning(f"⚠️ Model {model} not available. Available: {self.available_models}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        stats = self.stats.copy()
        if stats["successful"] > 0:
            stats["avg_response_time"] = stats["total_time"] / stats["successful"]
            stats["success_rate"] = (stats["successful"] / stats["requests"]) * 100
        else:
            stats["avg_response_time"] = 0.0
            stats["success_rate"] = 0.0

        return stats

    async def test_agent(self) -> Dict[str, Any]:
        """Test the ish.chat DirectAPI agent"""
        logger.info("🧪 Testing ish.chat DirectAPI Agent...")

        test_task = IshChatTask(
            prompt="Write hello world in Python",
            model="claude-3.5-sonnet",
            max_tokens=100
        )

        start_time = time.time()
        response = await self.generate_response(test_task)
        execution_time = time.time() - start_time

        return {
            "success": response and not response.startswith("Error:"),
            "response": response,
            "execution_time": execution_time,
            "response_length": len(response) if response else 0,
            "model_used": test_task.model
        }

async def main():
    """Test the ish.chat DirectAPI agent"""
    print("🤖 ish.chat DirectAPI Agent Test")
    print("="*50)

    agent = IshChatDirectAPIAgent()

    # Initialize
    if await agent.initialize():
        print("✅ Agent initialized successfully")

        # Get available models
        models = await agent.get_available_models()
        print(f"📋 Available models: {len(models)}")
        for model in models[:5]:  # Show first 5
            print(f"   • {model}")

        # Test with a simple request
        print(f"\n🧪 Testing agent...")
        test_result = await agent.test_agent()

        if test_result["success"]:
            print(f"✅ Test successful!")
            print(f"   Response time: {test_result['execution_time']:.2f}s")
            print(f"   Response length: {test_result['response_length']} chars")
            print(f"   Response preview: {test_result['response'][:100]}...")
        else:
            print(f"❌ Test failed: {test_result['response']}")

        # Show stats
        stats = agent.get_stats()
        print(f"\n📊 Agent Statistics:")
        print(f"   Total requests: {stats['requests']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        if stats['avg_response_time'] > 0:
            print(f"   Avg response time: {stats['avg_response_time']:.2f}s")

    else:
        print("❌ Failed to initialize agent")

if __name__ == "__main__":
    asyncio.run(main())