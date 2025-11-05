"""
Perplexity AI Official API Client

Provides a complete REST API wrapper for interacting with Perplexity AI's
official API with support for streaming, conversation history, and robust
error handling.

Usage:
    from api_client import PerplexityAPIClient

    client = PerplexityAPIClient(api_key="your_api_key")
    response = client.send_prompt("What is quantum computing?")
    print(response)

    # Streaming example
    for chunk in client.send_prompt_streaming("Explain AI"):
        print(chunk, end='', flush=True)
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Generator, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class Message:
    """Represents a chat message"""
    role: str  # 'system', 'user', or 'assistant'
    content: str
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert to API format"""
        return {"role": self.role, "content": self.content}


@dataclass
class APIResponse:
    """Represents an API response"""
    content: str
    model: str
    usage: Dict[str, int]
    citations: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[str] = None
    response_time: Optional[float] = None


class RateLimiter:
    """Simple token bucket rate limiter"""

    def __init__(self, requests_per_minute: int = 50):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.lock = False

    def acquire(self) -> bool:
        """Acquire a token, returns True if successful"""
        current_time = time.time()
        elapsed = current_time - self.last_update

        # Refill tokens based on elapsed time
        self.tokens = min(
            self.requests_per_minute,
            self.tokens + (elapsed * self.requests_per_minute / 60)
        )
        self.last_update = current_time

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def wait_if_needed(self):
        """Wait until a token is available"""
        while not self.acquire():
            time.sleep(0.1)


class PerplexityAPIClient:
    """
    Official Perplexity AI API client with comprehensive features.

    Features:
    - Bearer token authentication
    - Multiple model support
    - Streaming and non-streaming responses
    - Conversation history management
    - Automatic retries with exponential backoff
    - Rate limiting
    - Citations extraction
    - Error handling

    Example:
        client = PerplexityAPIClient()

        # Simple query
        response = client.send_prompt("What is AI?")
        print(response.content)

        # With conversation history
        client.add_message("user", "What is machine learning?")
        response = client.continue_conversation()
        print(response.content)

        # Streaming
        for chunk in client.send_prompt_streaming("Explain quantum physics"):
            print(chunk, end='', flush=True)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config_path: Optional[str] = None,
        model: str = "sonar-medium-online",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the API client.

        Args:
            api_key: Perplexity API key (falls back to PERPLEXITY_API_KEY env var)
            config_path: Path to config.json file
            model: Model to use for requests
            logger: Custom logger instance
        """
        self.logger = logger or self._setup_logger()
        self.config = self._load_config(config_path)

        # API key handling
        self.api_key = api_key or os.environ.get(
            self.config["api"]["api_key_env"],
            ""
        )
        if not self.api_key:
            self.logger.warning("No API key provided. Set PERPLEXITY_API_KEY environment variable.")

        # API settings
        self.endpoint = self.config["api"]["endpoint"]
        self.model = model
        self.timeout = (
            self.config["api"]["timeout"]["connect"],
            self.config["api"]["timeout"]["read"]
        )

        # Session management
        self.session = self._create_session()
        self.conversation_history: List[Message] = []
        self.rate_limiter = RateLimiter(
            self.config["api"]["rate_limit"]["requests_per_minute"]
        )

        self.logger.info(f"Perplexity API Client initialized with model: {model}")

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger("PerplexityAPI")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from JSON file"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "config.json"
            )

        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "api": {
                "endpoint": "https://api.perplexity.ai/v1/chat/completions",
                "api_key_env": "PERPLEXITY_API_KEY",
                "timeout": {"connect": 10, "read": 120},
                "retry": {
                    "max_attempts": 3,
                    "backoff_factor": 2,
                    "retry_on_status": [429, 500, 502, 503, 504]
                },
                "rate_limit": {"requests_per_minute": 50}
            }
        }

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()

        retry_config = self.config["api"]["retry"]
        retry_strategy = Retry(
            total=retry_config["max_attempts"],
            backoff_factor=retry_config["backoff_factor"],
            status_forcelist=retry_config["retry_on_status"],
            allowed_methods=["POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def add_message(self, role: str, content: str):
        """
        Add a message to conversation history.

        Args:
            role: Message role ('system', 'user', or 'assistant')
            content: Message content
        """
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        self.conversation_history.append(message)
        self.logger.debug(f"Added {role} message to history")

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history in API format"""
        return [msg.to_dict() for msg in self.conversation_history]

    def send_prompt(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        include_citations: bool = True,
        system_message: Optional[str] = None
    ) -> APIResponse:
        """
        Send a prompt to Perplexity API and get response.

        Args:
            prompt: User prompt/question
            model: Model to use (overrides default)
            temperature: Response randomness (0.0-2.0)
            max_tokens: Maximum tokens in response
            include_citations: Include source citations
            system_message: Optional system message for context

        Returns:
            APIResponse object with content, metadata, and citations

        Raises:
            requests.exceptions.RequestException: On API errors
        """
        self.rate_limiter.wait_if_needed()

        model = model or self.model
        messages = []

        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add conversation history
        messages.extend(self.get_history())

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "return_citations": include_citations
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        self.logger.info(f"Sending prompt to {model}: {prompt[:50]}...")
        start_time = time.time()

        try:
            response = self.session.post(
                self.endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            response_time = time.time() - start_time
            data = response.json()

            # Extract response content
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            citations = data.get("citations", [])

            # Update conversation history
            self.add_message("user", prompt)
            self.add_message("assistant", content)

            self.logger.info(f"Response received in {response_time:.2f}s")

            return APIResponse(
                content=content,
                model=model,
                usage=usage,
                citations=citations if include_citations else None,
                timestamp=datetime.now().isoformat(),
                response_time=response_time
            )

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise

    def send_prompt_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Send a prompt and stream the response in chunks.

        Args:
            prompt: User prompt/question
            model: Model to use (overrides default)
            temperature: Response randomness (0.0-2.0)
            system_message: Optional system message for context

        Yields:
            Response chunks as they arrive

        Example:
            for chunk in client.send_prompt_streaming("Explain AI"):
                print(chunk, end='', flush=True)
        """
        self.rate_limiter.wait_if_needed()

        model = model or self.model
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.extend(self.get_history())
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        self.logger.info(f"Sending streaming prompt to {model}: {prompt[:50]}...")

        try:
            response = self.session.post(
                self.endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            full_content = []

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix

                        if data == '[DONE]':
                            break

                        try:
                            chunk_data = json.loads(data)
                            delta = chunk_data["choices"][0]["delta"]

                            if "content" in delta:
                                content = delta["content"]
                                full_content.append(content)
                                yield content

                        except json.JSONDecodeError:
                            continue

            # Update conversation history
            complete_response = ''.join(full_content)
            self.add_message("user", prompt)
            self.add_message("assistant", complete_response)

            self.logger.info("Streaming response completed")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Streaming request failed: {str(e)}")
            raise

    def continue_conversation(
        self,
        model: Optional[str] = None,
        temperature: float = 0.2
    ) -> APIResponse:
        """
        Continue conversation with existing history.
        Last message in history should be a user message.

        Args:
            model: Model to use (overrides default)
            temperature: Response randomness (0.0-2.0)

        Returns:
            APIResponse object
        """
        if not self.conversation_history:
            raise ValueError("No conversation history available")

        if self.conversation_history[-1].role != "user":
            raise ValueError("Last message must be from user")

        self.rate_limiter.wait_if_needed()

        model = model or self.model
        messages = self.get_history()

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "return_citations": True
        }

        self.logger.info("Continuing conversation...")
        start_time = time.time()

        try:
            response = self.session.post(
                self.endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            response_time = time.time() - start_time
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            citations = data.get("citations", [])

            self.add_message("assistant", content)

            self.logger.info(f"Response received in {response_time:.2f}s")

            return APIResponse(
                content=content,
                model=model,
                usage=usage,
                citations=citations,
                timestamp=datetime.now().isoformat(),
                response_time=response_time
            )

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Conversation continuation failed: {str(e)}")
            raise

    def switch_model(self, model: str):
        """
        Switch to a different model.

        Args:
            model: Model name (e.g., 'sonar-pro', 'sonar-medium-online')
        """
        self.model = model
        self.logger.info(f"Switched to model: {model}")

    def test_connection(self) -> bool:
        """
        Test API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.send_prompt("Hello", max_tokens=5)
            self.logger.info("API connection test successful")
            self.clear_history()  # Clear test messages
            return True
        except Exception as e:
            self.logger.error(f"API connection test failed: {str(e)}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models from config"""
        return self.config.get("api", {}).get("models", {}).get("available", [])


if __name__ == "__main__":
    # Example usage
    client = PerplexityAPIClient()

    if client.api_key:
        print("Testing API connection...")
        if client.test_connection():
            print("\n=== Simple Query ===")
            response = client.send_prompt("What is the capital of France?")
            print(f"Response: {response.content}")
            print(f"Model: {response.model}")
            print(f"Response time: {response.response_time:.2f}s")

            if response.citations:
                print("\nCitations:")
                for cite in response.citations:
                    print(f"  - {cite}")
    else:
        print("No API key found. Set PERPLEXITY_API_KEY environment variable.")
