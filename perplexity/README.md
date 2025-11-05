# Perplexity AI Integration System

Complete integration system for Perplexity AI supporting both official API and UI automation fallback.

## Overview

This system provides multiple ways to interact with Perplexity AI:

1. **Official API Client** - Direct REST API integration with streaming support
2. **UI Automation** - Termux/ADB-based fallback for Android devices
3. **Unified Bridge** - Intelligent automatic fallback between methods

## Installation

### Prerequisites

```bash
# For API client
pip3 install requests

# For UI automation (Termux)
pkg install android-tools
pkg install tesseract  # Optional, for OCR

# For Python environment
pkg install python
```

### Setup

1. Set API key (optional, for API method):
```bash
export PERPLEXITY_API_KEY="your_api_key_here"
```

2. Configure settings in `config.json` if needed

## Quick Start

### Using the Bridge (Recommended)

The bridge automatically selects the best available method:

```python
from perplexity_bridge import PerplexityBridge

# Initialize bridge
bridge = PerplexityBridge()

# Simple query (auto-detects best method)
response = bridge.query("What is quantum computing?")
print(response)

# Conversation with context
bridge.query("Tell me about Python programming")
response = bridge.query("What are its main advantages?")
print(response)

# Force specific method
response = bridge.query(
    "Question here",
    method=QueryMethod.API
)
```

### Using API Client Directly

For direct API access with full control:

```python
from api_client import PerplexityAPIClient

# Initialize client
client = PerplexityAPIClient(api_key="your_key")

# Simple query
response = client.send_prompt("What is artificial intelligence?")
print(response.content)
print(f"Model: {response.model}")
print(f"Tokens used: {response.usage}")

# With citations
if response.citations:
    print("\nSources:")
    for citation in response.citations:
        print(f"  - {citation}")

# Streaming response
print("Streaming response:")
for chunk in client.send_prompt_streaming("Explain quantum physics"):
    print(chunk, end='', flush=True)

# Conversation with history
client.add_message("user", "What is machine learning?")
response = client.continue_conversation()
print(response.content)

# Switch models
client.switch_model("sonar-pro")
response = client.send_prompt("Complex question here")
```

### Using UI Automation Directly

For Android devices without API access:

```python
from ui_automation import PerplexityUIAutomation

# Initialize automator
automator = PerplexityUIAutomation()

# Launch app
automator.launch_app()

# Send query with automatic retry
response = automator.send_query_with_retry(
    "What is the capital of France?",
    max_retries=3
)
print(response)

# Close app
automator.close_app()
```

## Features

### API Client Features

- ✅ Bearer token authentication
- ✅ Multiple model support (sonar-pro, sonar-medium-online, etc.)
- ✅ Streaming and non-streaming responses
- ✅ Conversation history management
- ✅ Automatic retries with exponential backoff
- ✅ Rate limiting awareness
- ✅ Citation extraction
- ✅ Comprehensive error handling
- ✅ Usage statistics tracking

### UI Automation Features

- ✅ App launch via Android intents
- ✅ Text input via ADB commands
- ✅ Clipboard monitoring for responses
- ✅ Notification content parsing
- ✅ Screenshot OCR fallback
- ✅ Automatic error recovery
- ✅ App restart on failure
- ✅ Configurable retry logic

### Bridge Features

- ✅ Automatic method detection
- ✅ Intelligent fallback on failures
- ✅ Unified query interface
- ✅ Session persistence
- ✅ Context management
- ✅ Usage statistics
- ✅ Multi-session support

## Configuration

Edit `config.json` to customize:

### API Settings
```json
{
  "api": {
    "endpoint": "https://api.perplexity.ai/v1/chat/completions",
    "models": {
      "default": "sonar-medium-online"
    },
    "timeout": {
      "connect": 10,
      "read": 120
    },
    "retry": {
      "max_attempts": 3,
      "backoff_factor": 2
    }
  }
}
```

### UI Automation Settings
```json
{
  "ui_automation": {
    "app": {
      "package": "ai.perplexity.app.android",
      "activity": "ai.perplexity.app.android.MainActivity"
    },
    "interaction": {
      "text_field_tap": {"x": 540, "y": 1800},
      "send_button_tap": {"x": 1000, "y": 1800}
    },
    "response_detection": {
      "methods": ["clipboard", "notification", "screenshot"],
      "max_wait_time": 60
    }
  }
}
```

## Advanced Usage

### Session Management

```python
bridge = PerplexityBridge()

# Create new session
session_id = bridge.new_session()

# Query in session
bridge.query("First question")
bridge.query("Follow-up question")

# Get history
history = bridge.get_session_history()
for msg in history:
    print(f"{msg['role']}: {msg['content']}")

# Clear session
bridge.clear_session()
```

### Statistics and Monitoring

```python
# Get usage statistics
stats = bridge.get_statistics()
print(f"API queries: {stats['api_queries']}")
print(f"UI queries: {stats['ui_queries']}")
print(f"Fallback triggers: {stats['fallback_triggers']}")
print(f"Success rates: {stats['success_rate']}")
```

### Error Handling

```python
try:
    response = bridge.query("Your question")
    if response:
        print(response)
    else:
        print("Query failed")
except RuntimeError as e:
    print(f"Error: {e}")
```

### Custom Models

```python
# Using API client
client = PerplexityAPIClient()

# Available models
models = client.get_available_models()
print(f"Available: {models}")

# Use specific model
response = client.send_prompt(
    "Complex question",
    model="sonar-pro",
    temperature=0.5,
    max_tokens=1000
)
```

## Environment Variables

- `PERPLEXITY_API_KEY` - API authentication key
- Optional: Set in shell or `.env` file

```bash
# In ~/.bashrc or ~/.zshrc
export PERPLEXITY_API_KEY="pplx-xxxxxxxxxxxxxxxx"
```

## Troubleshooting

### API Issues

1. **Authentication Error**: Check API key is set correctly
2. **Rate Limiting**: Reduce request frequency or upgrade plan
3. **Timeout**: Increase timeout values in config.json

### UI Automation Issues

1. **App Not Launching**: Verify package name and ADB connection
2. **No Response Detected**: Adjust tap coordinates in config
3. **ADB Not Found**: Install `android-tools` in Termux

### General Issues

1. **Import Errors**: Ensure all dependencies installed
2. **Config Not Found**: Check config.json path
3. **Permissions**: Grant necessary Android permissions

## Examples

See individual module files for comprehensive examples:
- `api_client.py` - API usage examples
- `ui_automation.py` - UI automation examples
- `perplexity_bridge.py` - Bridge usage examples

## Testing

```python
# Test all methods
from perplexity_bridge import PerplexityBridge

bridge = PerplexityBridge()
results = bridge.test_methods()
print(f"API: {results['api']}")
print(f"UI: {results['ui_automation']}")
```

## License

Part of Android Automation System

## Support

For issues and questions, check the logs:
- API logs: Console output with timestamps
- UI logs: Console output with ADB command details
- Bridge logs: Combined system logs in `~/.perplexity_bridge.log`
