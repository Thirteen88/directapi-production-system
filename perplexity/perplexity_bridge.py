"""
Perplexity Bridge - Unified Interface

Provides intelligent fallback between official API and UI automation.
Automatically selects the best available method and manages sessions.

Usage:
    from perplexity_bridge import PerplexityBridge

    bridge = PerplexityBridge()
    response = bridge.query("What is quantum computing?")
    print(response)
"""

import os
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

try:
    from api_client import PerplexityAPIClient, APIResponse
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    logging.warning("API client not available")

try:
    from ui_automation import PerplexityUIAutomation
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False
    logging.warning("UI automation not available")


class QueryMethod(Enum):
    """Available query methods"""
    API = "api"
    UI_AUTOMATION = "ui_automation"
    AUTO = "auto"


class SessionManager:
    """Manages conversation sessions and persistence"""

    def __init__(self, history_file: str):
        """
        Initialize session manager.

        Args:
            history_file: Path to history file
        """
        self.history_file = os.path.expanduser(history_file)
        self.sessions: Dict[str, List[Dict]] = {}
        self.current_session_id: Optional[str] = None
        self._load_sessions()

    def _load_sessions(self):
        """Load sessions from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.sessions = data.get("sessions", {})
                    self.current_session_id = data.get("current_session")
            except Exception as e:
                logging.warning(f"Failed to load sessions: {str(e)}")

    def _save_sessions(self):
        """Save sessions to file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump({
                    "sessions": self.sessions,
                    "current_session": self.current_session_id
                }, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save sessions: {str(e)}")

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create new session.

        Args:
            session_id: Optional custom session ID

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.sessions[session_id] = []
        self.current_session_id = session_id
        self._save_sessions()
        return session_id

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add message to current session.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata
        """
        if not self.current_session_id:
            self.create_session()

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.sessions[self.current_session_id].append(message)
        self._save_sessions()

    def get_session_history(self, session_id: Optional[str] = None) -> List[Dict]:
        """
        Get session history.

        Args:
            session_id: Session ID (uses current if None)

        Returns:
            List of messages
        """
        session_id = session_id or self.current_session_id
        return self.sessions.get(session_id, [])

    def clear_session(self, session_id: Optional[str] = None):
        """
        Clear session history.

        Args:
            session_id: Session ID (uses current if None)
        """
        session_id = session_id or self.current_session_id
        if session_id in self.sessions:
            self.sessions[session_id] = []
            self._save_sessions()

    def list_sessions(self) -> List[str]:
        """Get list of all session IDs"""
        return list(self.sessions.keys())


class PerplexityBridge:
    """
    Unified interface for Perplexity AI with intelligent fallback.

    Features:
    - Automatic method selection (API vs UI)
    - Seamless fallback on API failures
    - Session persistence
    - Context management
    - Usage statistics
    - Error recovery

    Example:
        bridge = PerplexityBridge()

        # Simple query (auto-selects method)
        response = bridge.query("What is AI?")
        print(response)

        # Force specific method
        response = bridge.query("Question", method=QueryMethod.API)

        # With conversation context
        bridge.query("Tell me about Python")
        response = bridge.query("What are its main features?")

        # Session management
        bridge.new_session()
        bridge.query("New conversation")
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        api_key: Optional[str] = None,
        default_method: QueryMethod = QueryMethod.AUTO,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Perplexity Bridge.

        Args:
            config_path: Path to config.json
            api_key: Perplexity API key
            default_method: Default query method
            logger: Custom logger instance
        """
        self.logger = logger or self._setup_logger()
        self.config = self._load_config(config_path)
        self.default_method = default_method

        # Initialize API client
        self.api_client: Optional[PerplexityAPIClient] = None
        if API_AVAILABLE:
            try:
                self.api_client = PerplexityAPIClient(
                    api_key=api_key,
                    config_path=config_path,
                    logger=self.logger
                )
                self.api_available = self.api_client.test_connection()
            except Exception as e:
                self.logger.warning(f"API client initialization failed: {str(e)}")
                self.api_available = False
        else:
            self.api_available = False

        # Initialize UI automation
        self.ui_automator: Optional[PerplexityUIAutomation] = None
        if UI_AVAILABLE and self.config["ui_automation"]["enabled"]:
            try:
                self.ui_automator = PerplexityUIAutomation(
                    config_path=config_path,
                    logger=self.logger
                )
                self.ui_available = True
            except Exception as e:
                self.logger.warning(f"UI automation initialization failed: {str(e)}")
                self.ui_available = False
        else:
            self.ui_available = False

        # Session management
        if self.config["session"]["persist_history"]:
            history_file = os.path.expanduser(
                self.config["session"]["history_file"]
            )
            self.session_manager = SessionManager(history_file)
        else:
            self.session_manager = None

        # Statistics
        self.stats = {
            "api_queries": 0,
            "ui_queries": 0,
            "api_failures": 0,
            "ui_failures": 0,
            "fallback_triggers": 0
        }

        self.logger.info(
            f"Perplexity Bridge initialized - "
            f"API: {self.api_available}, UI: {self.ui_available}"
        )

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file and console handlers"""
        logger = logging.getLogger("PerplexityBridge")
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "config.json"
            )

        with open(config_path, 'r') as f:
            return json.load(f)

    def _determine_method(self, preferred: QueryMethod) -> QueryMethod:
        """
        Determine which method to use based on availability.

        Args:
            preferred: Preferred method

        Returns:
            Actual method to use
        """
        if preferred == QueryMethod.AUTO:
            # Prefer API if available
            if self.api_available:
                return QueryMethod.API
            elif self.ui_available:
                return QueryMethod.UI_AUTOMATION
            else:
                raise RuntimeError("No query method available")

        elif preferred == QueryMethod.API:
            if not self.api_available:
                if self.ui_available and self.config["ui_automation"]["fallback_on_api_failure"]:
                    self.logger.warning("API not available, falling back to UI")
                    self.stats["fallback_triggers"] += 1
                    return QueryMethod.UI_AUTOMATION
                else:
                    raise RuntimeError("API not available")
            return QueryMethod.API

        elif preferred == QueryMethod.UI_AUTOMATION:
            if not self.ui_available:
                raise RuntimeError("UI automation not available")
            return QueryMethod.UI_AUTOMATION

    def query(
        self,
        prompt: str,
        method: Optional[QueryMethod] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Send query and get response.

        Args:
            prompt: User query/question
            method: Query method (uses default if None)
            **kwargs: Additional arguments for specific methods

        Returns:
            Response text or None if failed

        Example:
            # Simple query
            response = bridge.query("What is AI?")

            # Force API with specific model
            response = bridge.query(
                "Complex question",
                method=QueryMethod.API,
                model="sonar-pro"
            )
        """
        method = method or self.default_method
        actual_method = self._determine_method(method)

        self.logger.info(f"Processing query via {actual_method.value}: {prompt[:50]}...")

        # Save user message
        if self.session_manager:
            self.session_manager.add_message("user", prompt)

        response = None

        try:
            if actual_method == QueryMethod.API:
                response = self._query_via_api(prompt, **kwargs)
                self.stats["api_queries"] += 1

            elif actual_method == QueryMethod.UI_AUTOMATION:
                response = self._query_via_ui(prompt, **kwargs)
                self.stats["ui_queries"] += 1

            # Save assistant response
            if response and self.session_manager:
                self.session_manager.add_message(
                    "assistant",
                    response,
                    {"method": actual_method.value}
                )

            return response

        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")

            # Try fallback if configured
            if actual_method == QueryMethod.API and self.ui_available:
                if self.config["ui_automation"]["fallback_on_api_failure"]:
                    self.logger.info("Attempting UI fallback...")
                    self.stats["fallback_triggers"] += 1
                    try:
                        response = self._query_via_ui(prompt, **kwargs)
                        self.stats["ui_queries"] += 1

                        if response and self.session_manager:
                            self.session_manager.add_message(
                                "assistant",
                                response,
                                {"method": "ui_automation_fallback"}
                            )

                        return response
                    except Exception as fallback_error:
                        self.logger.error(f"Fallback failed: {str(fallback_error)}")

            return None

    def _query_via_api(self, prompt: str, **kwargs) -> Optional[str]:
        """Query via API client"""
        if not self.api_client:
            raise RuntimeError("API client not initialized")

        try:
            response: APIResponse = self.api_client.send_prompt(prompt, **kwargs)
            return response.content
        except Exception as e:
            self.stats["api_failures"] += 1
            raise

    def _query_via_ui(self, prompt: str, **kwargs) -> Optional[str]:
        """Query via UI automation"""
        if not self.ui_automator:
            raise RuntimeError("UI automator not initialized")

        try:
            max_retries = kwargs.get("max_retries", 2)
            response = self.ui_automator.send_query_with_retry(
                prompt,
                max_retries=max_retries
            )

            if not response:
                self.stats["ui_failures"] += 1
                raise RuntimeError("UI automation returned no response")

            return response
        except Exception as e:
            self.stats["ui_failures"] += 1
            raise

    def query_streaming(self, prompt: str, **kwargs):
        """
        Query with streaming response (API only).

        Args:
            prompt: User query
            **kwargs: Additional API arguments

        Yields:
            Response chunks

        Example:
            for chunk in bridge.query_streaming("Explain AI"):
                print(chunk, end='', flush=True)
        """
        if not self.api_available or not self.api_client:
            raise RuntimeError("Streaming requires API client")

        self.logger.info(f"Streaming query: {prompt[:50]}...")

        if self.session_manager:
            self.session_manager.add_message("user", prompt)

        full_response = []

        try:
            for chunk in self.api_client.send_prompt_streaming(prompt, **kwargs):
                full_response.append(chunk)
                yield chunk

            self.stats["api_queries"] += 1

            # Save complete response
            if self.session_manager:
                self.session_manager.add_message(
                    "assistant",
                    ''.join(full_response),
                    {"method": "api_streaming"}
                )

        except Exception as e:
            self.logger.error(f"Streaming query failed: {str(e)}")
            self.stats["api_failures"] += 1
            raise

    def new_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new conversation session.

        Args:
            session_id: Optional custom session ID

        Returns:
            Session ID
        """
        if not self.session_manager:
            raise RuntimeError("Session persistence not enabled")

        session_id = self.session_manager.create_session(session_id)

        # Clear API client history if available
        if self.api_client:
            self.api_client.clear_history()

        self.logger.info(f"Started new session: {session_id}")
        return session_id

    def get_session_history(self, session_id: Optional[str] = None) -> List[Dict]:
        """Get conversation history for session"""
        if not self.session_manager:
            return []
        return self.session_manager.get_session_history(session_id)

    def clear_session(self):
        """Clear current session"""
        if self.session_manager:
            self.session_manager.clear_session()
        if self.api_client:
            self.api_client.clear_history()
        self.logger.info("Session cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            **self.stats,
            "api_available": self.api_available,
            "ui_available": self.ui_available,
            "success_rate": self._calculate_success_rate()
        }

    def _calculate_success_rate(self) -> Dict[str, float]:
        """Calculate success rates"""
        api_total = self.stats["api_queries"] + self.stats["api_failures"]
        ui_total = self.stats["ui_queries"] + self.stats["ui_failures"]

        return {
            "api": (self.stats["api_queries"] / api_total * 100) if api_total > 0 else 0,
            "ui": (self.stats["ui_queries"] / ui_total * 100) if ui_total > 0 else 0
        }

    def test_methods(self) -> Dict[str, bool]:
        """
        Test all available methods.

        Returns:
            Dict with method availability
        """
        results = {
            "api": False,
            "ui_automation": False
        }

        # Test API
        if self.api_available and self.api_client:
            try:
                response = self.api_client.send_prompt("test", max_tokens=5)
                results["api"] = bool(response.content)
                self.api_client.clear_history()
            except Exception:
                pass

        # Test UI
        if self.ui_available and self.ui_automator:
            try:
                # Just test app launch, don't send query
                results["ui_automation"] = self.ui_automator.launch_app()
                self.ui_automator.close_app()
            except Exception:
                pass

        return results


if __name__ == "__main__":
    # Example usage
    bridge = PerplexityBridge()

    print("=== Perplexity Bridge Test ===\n")

    # Test methods
    print("Testing available methods...")
    methods = bridge.test_methods()
    print(f"API available: {methods['api']}")
    print(f"UI available: {methods['ui_automation']}")

    if methods['api'] or methods['ui_automation']:
        print("\n=== Simple Query ===")
        response = bridge.query("What is the capital of France?")
        if response:
            print(f"Response: {response[:200]}...")

        print("\n=== Statistics ===")
        stats = bridge.get_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
    else:
        print("\nNo methods available for testing.")
