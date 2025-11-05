"""
Perplexity AI Integration System

Complete integration system supporting both official API and UI automation fallback.

Main Components:
- api_client: Official Perplexity API REST client
- ui_automation: Termux/ADB-based UI automation
- perplexity_bridge: Unified interface with intelligent fallback

Usage:
    # Simple usage with automatic method selection
    from perplexity import PerplexityBridge

    bridge = PerplexityBridge()
    response = bridge.query("What is quantum computing?")
    print(response)

    # Direct API usage
    from perplexity import PerplexityAPIClient

    client = PerplexityAPIClient(api_key="your_key")
    response = client.send_prompt("Explain AI")
    print(response.content)

    # Direct UI automation
    from perplexity import PerplexityUIAutomation

    automator = PerplexityUIAutomation()
    response = automator.send_query("What is machine learning?")
    print(response)
"""

__version__ = "1.0.0"
__author__ = "Android Automation System"

# Import main classes
try:
    from .api_client import PerplexityAPIClient, APIResponse, Message
    __all__ = ["PerplexityAPIClient", "APIResponse", "Message"]
except ImportError:
    pass

try:
    from .ui_automation import PerplexityUIAutomation, ADBError, UIAutomationError
    __all__ = __all__ + ["PerplexityUIAutomation", "ADBError", "UIAutomationError"]
except ImportError:
    pass

try:
    from .perplexity_bridge import PerplexityBridge, QueryMethod, SessionManager
    __all__ = __all__ + ["PerplexityBridge", "QueryMethod", "SessionManager"]
except ImportError:
    pass
