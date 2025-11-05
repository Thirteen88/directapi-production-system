#!/usr/bin/env python3
"""
Complete Model Inventory for Claude Orchestrator System
Lists all available models from all integrated providers
"""

import json
from datetime import datetime
from ish_chat_integration import ish_chat_integration

def get_complete_model_inventory():
    """Get comprehensive list of all available models"""

    print("=" * 80)
    print("🔍 COMPLETE MODEL INVENTORY - CLAUDE ORCHESTRATOR SYSTEM")
    print("=" * 80)
    print(f"Generated at: {datetime.now().isoformat()}")

    inventory = {
        "timestamp": datetime.now().isoformat(),
        "active_models": {},
        "available_providers": {},
        "model_details": {}
    }

    # 1. ORCHESTRATOR MODELS (Actively Used)
    print("\n🧠 === ORCHESTRATOR-ACTIVE MODELS ===")

    from orchestrator import select_best_model, AgentType, YOLOMode

  # Test all agent types to see what models get selected
    agent_types = [
        AgentType.CODE_GENERATOR,
        AgentType.CODE_REVIEWER,
        AgentType.TESTER,
        AgentType.DOCUMENTER,
        AgentType.DEBUGGER,
        AgentType.CUSTOM,
        AgentType.REFACTORER
    ]

    selected_models = set()

    for agent_type in agent_types:
        selection = select_best_model(
            task_description=f"Test task for {agent_type.value}",
            agent_type=agent_type,
            inputs={"test": True},
            yolo_mode=YOLOMode.AGGRESSIVE
        )

        model = selection["model"]
        reasoning = " → ".join(selection["reasoning"])
        selected_models.add(model)

        print(f"  {agent_type.value:15} → {model}")
        print(f"    Reasoning: {reasoning}")

    inventory["active_models"]["orchestrator"] = list(selected_models)

    # 2. ISH.CHAT MODELS (Backend Available)
    print("\n🌐 === ISH.CHAT BACKEND MODELS ===")

    # Check health and providers
    health = ish_chat_integration.check_health()

    if health["status"] == "healthy":
        providers = health.get("providers", [])
        print(f"  ✅ ISH.chat Backend: HEALTHY")
        print(f"  📡 Available Providers: {providers}")

        # Get detailed provider info
        try:
            import requests
            providers_response = requests.get("http://localhost:8000/api/ai/enhanced/providers", timeout=10)
            if providers_response.status_code == 200:
                providers_data = providers_response.json()

                print("\n  📋 Detailed Provider Information:")
                for provider_name, provider_info in providers_data.get("providers", {}).items():
                    model = provider_info.get("model", "Unknown")
                    streaming = provider_info.get("supports_streaming", False)
                    functions = provider_info.get("supports_functions", False)

                    print(f"    🏷️  {provider_name}")
                    print(f"       Model: {model}")
                    print(f"       Streaming: {'✅' if streaming else '❌'}")
                    print(f"       Functions: {'✅' if functions else '❌'}")

                    # Check health status
                    health_status = providers_data.get("health_status", {}).get(provider_name, {})
                    is_healthy = health_status.get("healthy", False)
                    error = health_status.get("error", "")

                    print(f"       Health: {'✅' if is_healthy else '❌'}")
                    if not is_healthy:
                        print(f"       Error: {error[:100]}...")
                    print()

                inventory["available_providers"]["ish_chat"] = providers_data

        except Exception as e:
            print(f"  ❌ Failed to get detailed provider info: {str(e)}")

        # List individual models
        print("  🔢 Individual ISH.chat Models:")
        for provider in providers:
            model_name = f"ish.chat-{provider}"
            print(f"    ✅ {model_name}")

        inventory["active_models"]["ish_chat"] = [f"ish.chat-{p}" for p in providers]

    else:
        print(f"  ❌ ISH.chat Backend: UNHEALTHY ({health.get('status', 'unknown')})")
        inventory["available_providers"]["ish_chat"] = {"error": "Backend unhealthy"}

    # 3. ANDROID PERPLEXITY MODELS
    print("\n📱 === ANDROID PERPLEXITY MODELS ===")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("android_perplexity_agent", "android-perplexity-agent.py")
        android_perplexity_agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(android_perplexity_agent)
        AndroidPerplexityAgent = android_perplexity_agent.AndroidPerplexityAgent

        agent = AndroidPerplexityAgent()
        print(f"  ✅ Android Perplexity Agent: INITIALIZED")
        print(f"  📱 Device: {getattr(agent, 'device_id', 'Unknown')}")
        print(f"  🤖 Model: claude-sonnet-4-5-20250929 (via Perplexity app)")

        inventory["active_models"]["android_perplexity"] = ["claude-sonnet-4-5-20250929 (Perplexity app)"]

    except Exception as e:
        print(f"  ❌ Android Perplexity Agent: FAILED - {str(e)}")
        inventory["active_models"]["android_perplexity"] = {"error": str(e)}

    # 4. SUMMARY
    print("\n📊 === COMPLETE MODEL SUMMARY ===")

    all_models = []
    for category, models in inventory["active_models"].items():
        if isinstance(models, list):
            all_models.extend(models)
            print(f"  📂 {category.replace('_', ' ').title()}: {len(models)} models")
            for model in models:
                print(f"    ✅ {model}")
        print()

    # Remove duplicates and count
    unique_models = list(set(all_models))
    print(f"🎯 TOTAL UNIQUE MODELS AVAILABLE: {len(unique_models)}")

    # Categorize by capability
    sonnet_models = [m for m in unique_models if "sonnet-4-5" in m.lower()]
    claude_models = [m for m in unique_models if "claude" in m.lower() and "sonnet-4-5" not in m.lower()]
    other_models = [m for m in unique_models if "claude" not in m.lower()]

    print(f"  🧠 Sonnet 4.5 Models: {len(sonnet_models)}")
    for model in sonnet_models:
        print(f"    ✅ {model}")

    print(f"  🤖 Other Claude Models: {len(claude_models)}")
    for model in claude_models:
        print(f"    ✅ {model}")

    print(f"  🔧 Other Models: {len(other_models)}")
    for model in other_models:
        print(f"    ✅ {model}")

    # 5. ACTIVATION STATUS
    print("\n⚡ === MODEL ACTIVATION STATUS ===")

    activation_status = {
        "actively_used_in_orchestrator": len(inventory["active_models"].get("orchestrator", [])),
        "configured_but_need_keys": 0,
        "connected_and_ready": 0,
        "total_available": len(unique_models)
    }

    # Count ISH.chat models that need API keys
    if "ish_chat" in inventory["active_models"]:
        ish_models = inventory["active_models"]["ish_chat"]
        activation_status["configured_but_need_keys"] = len(ish_models)
        print(f"  🔑 ISH.chat Models (need API keys): {len(ish_models)}")
        for model in ish_models:
            print(f"    ⚠️  {model} - Requires API key")

    # Count Android models
    if "android_perplexity" in inventory["active_models"]:
        android_models = inventory["active_models"]["android_perplexity"]
        if isinstance(android_models, list):
            activation_status["connected_and_ready"] = len(android_models)
            print(f"  📱 Android Models (connected): {len(android_models)}")
            for model in android_models:
                print(f"    ✅ {model} - Ready to use")

    print(f"\n📈 ACTIVATION SUMMARY:")
    print(f"  ✅ Active in Orchestrator: {activation_status['actively_used_in_orchestrator']}")
    print(f"  🔑 Need API Keys: {activation_status['configured_but_need_keys']}")
    print(f"  📱 Connected & Ready: {activation_status['connected_and_ready']}")
    print(f"  📊 Total Available: {activation_status['total_available']}")

    # Save inventory
    inventory_file = f"complete_model_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(inventory_file, 'w') as f:
        json.dump(inventory, f, indent=2)

    print(f"\n💾 Inventory saved to: {inventory_file}")

    return inventory

if __name__ == "__main__":
    get_complete_model_inventory()