#!/usr/bin/env python3
"""
ISH Chat Integration Service
Connects orchestrator to ISH.chat backend providers (zai, anthropic)
"""

import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

class ISHChatIntegration:
    """Integration service for ISH.chat backend providers"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.health_endpoint = f"{self.base_url}/health"
        self.relay_endpoint = f"{self.base_url}/api/relay"
        self.api_key = "ish-chat-secure-key-2024"  # Default API key for ISH.chat backend
        self.available_providers = []
        self.last_health_check = None

    def check_health(self) -> Dict[str, Any]:
        """Check ISH.chat backend health and available providers"""
        try:
            response = requests.get(self.health_endpoint, timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.available_providers = health_data.get("services", {}).get("ai_providers", [])
                self.last_health_check = datetime.now()
                return {
                    "status": "healthy",
                    "providers": self.available_providers,
                    "timestamp": self.last_health_check.isoformat()
                }
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def query_via_provider(self, provider: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Send query through ISH.chat backend using specified provider"""
        if provider not in self.available_providers:
            return {
                "success": False,
                "error": f"Provider '{provider}' not available. Available: {self.available_providers}"
            }

        payload = {
            "provider": provider,
            "sender": "orchestrator",
            "message": prompt,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        try:
            response = requests.post(
                self.relay_endpoint,
                json=payload,
                timeout=30,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.api_key
                }
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "provider": provider,
                    "response": response.json(),
                    "model_used": f"ish.chat-{provider}",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "provider": provider,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "provider": provider,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_available_models(self) -> List[str]:
        """Get list of available models from ISH.chat"""
        health = self.check_health()
        if health["status"] == "healthy":
            return [f"ish.chat-{provider}" for provider in health["providers"]]
        return []

    def test_all_providers(self, test_prompt: str = "Hello, please respond briefly.") -> Dict[str, Any]:
        """Test all available providers with a simple prompt"""
        results = {}

        for provider in self.available_providers:
            print(f"Testing provider: {provider}")
            result = self.query_via_provider(provider, test_prompt)
            results[provider] = result

        return {
            "test_results": results,
            "total_providers": len(self.available_providers),
            "successful_providers": sum(1 for r in results.values() if r.get("success", False)),
            "timestamp": datetime.now().isoformat()
        }

# Global instance
ish_chat_integration = ISHChatIntegration()

def get_ish_chat_models() -> List[str]:
    """Get available ISH.chat models for orchestrator"""
    return ish_chat_integration.get_available_models()

def query_ish_chat(provider: str, prompt: str, **kwargs) -> Dict[str, Any]:
    """Query ISH.chat backend through specified provider"""
    return ish_chat_integration.query_via_provider(provider, prompt, **kwargs)