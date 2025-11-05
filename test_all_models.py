#!/usr/bin/env python3
"""
Comprehensive test suite for all available models
Tests Sonnet 4.5, ISH.chat providers (zai, anthropic), and Android Perplexity automation
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Import all model integrations
from ish_chat_integration import ish_chat_integration
import importlib.util

# Import Android Perplexity Agent (module name has hyphens)
spec = importlib.util.spec_from_file_location("android_perplexity_agent", "android-perplexity-agent.py")
android_perplexity_agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(android_perplexity_agent)
AndroidPerplexityAgent = android_perplexity_agent.AndroidPerplexityAgent

def test_sonnet_45_via_orchestrator():
    """Test Sonnet 4.5 via orchestrator model selection"""
    print("🧠 Testing Sonnet 4.5 via Orchestrator Model Selection...")

    from orchestrator import select_best_model, AgentType, YOLOMode

    # Test model selection with different agent types
    test_cases = [
        {"agent_type": AgentType.CODE_GENERATOR, "description": "Generate Python function for API calls"},
        {"agent_type": AgentType.CODE_REVIEWER, "description": "Review security vulnerabilities"},
        {"agent_type": AgentType.TESTER, "description": "Create integration tests"},
        {"agent_type": AgentType.DOCUMENTER, "description": "Generate API documentation"}
    ]

    results = []
    for test_case in test_cases:
        selection = select_best_model(
            task_description=test_case["description"],
            agent_type=test_case["agent_type"],
            inputs={"test": True},
            yolo_mode=YOLOMode.AGGRESSIVE
        )

        model_used = selection["model"]
        reasoning = " → ".join(selection["reasoning"])

        is_sonnet_45 = "claude-sonnet-4-5-20250929" in model_used

        results.append({
            "agent_type": test_case["agent_type"].value,
            "task": test_case["description"],
            "model_selected": model_used,
            "is_sonnet_45": is_sonnet_45,
            "reasoning": reasoning
        })

        print(f"  {test_case['agent_type'].value}: {'✅' if is_sonnet_45 else '❌'} {model_used}")
        print(f"    Reasoning: {reasoning}")

    return results

def test_ish_chat_providers():
    """Test ISH.chat providers (zai, anthropic)"""
    print("\n🌐 Testing ISH.chat Providers...")

    # Check health first
    health = ish_chat_integration.check_health()
    print(f"  ISH.chat Health: {'✅' if health['status'] == 'healthy' else '❌'} {health['status']}")

    if health['status'] != 'healthy':
        return {"error": "ISH.chat backend not healthy", "health": health}

    providers = health['providers']
    print(f"  Available providers: {providers}")

    # Test prompts
    test_prompts = [
        {
            "name": "Simple Math",
            "prompt": "What is 15 * 23? Please calculate and give the result.",
            "expected_type": "numeric"
        },
        {
            "name": "Code Generation",
            "prompt": "Write a Python function to check if a number is prime.",
            "expected_type": "code"
        },
        {
            "name": "Knowledge Question",
            "prompt": "What are the main differences between REST and GraphQL APIs?",
            "expected_type": "explanation"
        }
    ]

    results = {}

    for provider in providers:
        print(f"\n  🧪 Testing {provider} provider:")
        provider_results = []

        for test_prompt in test_prompts:
            print(f"    Testing: {test_prompt['name']}")

            start_time = time.time()
            result = ish_chat_integration.query_via_provider(
                provider,
                test_prompt['prompt']
            )
            end_time = time.time()

            if result.get('success'):
                response = result.get('response', {})
                response_text = str(response)[:200] + "..." if len(str(response)) > 200 else str(response)

                provider_results.append({
                    "test_name": test_prompt['name'],
                    "success": True,
                    "response": response_text,
                    "model_used": result.get('model_used', f'ish.chat-{provider}'),
                    "response_time": f"{end_time - start_time:.2f}s"
                })

                print(f"      ✅ Success ({end_time - start_time:.2f}s)")
                print(f"      Model: {result.get('model_used', f'ish.chat-{provider}')}")
                print(f"      Response: {response_text}")

            else:
                error_msg = result.get('error', 'Unknown error')
                provider_results.append({
                    "test_name": test_prompt['name'],
                    "success": False,
                    "error": error_msg,
                    "response_time": f"{end_time - start_time:.2f}s"
                })

                print(f"      ❌ Failed ({end_time - start_time:.2f}s): {error_msg}")

        results[f"ish.chat-{provider}"] = provider_results

    return results

def test_android_perplexity():
    """Test Android Perplexity automation"""
    print("\n📱 Testing Android Perplexity Automation...")

    try:
        agent = AndroidPerplexityAgent()

        # Check device connection
        print("  Checking device connection...")
        # Note: We would need to implement a connection check method

        test_prompts = [
            "What is the capital of France?",
            "Explain machine learning in simple terms",
            "Write a hello world Python script"
        ]

        results = []

        for i, prompt in enumerate(test_prompts):
            print(f"  📱 Test {i+1}: {prompt[:50]}...")

            try:
                start_time = time.time()
                response = agent.send_prompt(prompt, wait_time=30, capture_interval=3)
                end_time = time.time()

                if response and response.get('success'):
                    response_text = response.get('extracted_text', '')[:200] + "..." if len(response.get('extracted_text', '')) > 200 else response.get('extracted_text', '')

                    results.append({
                        "test": f"Test {i+1}",
                        "prompt": prompt,
                        "success": True,
                        "response": response_text,
                        "model": response.get('model', 'claude-sonnet-4-5-20250929'),
                        "response_time": f"{end_time - start_time:.2f}s",
                        "screenshots": len(response.get('screenshots', []))
                    })

                    print(f"    ✅ Success ({end_time - start_time:.2f}s)")
                    print(f"    Model: {response.get('model', 'claude-sonnet-4-5-20250929')}")
                    print(f"    Screenshots: {len(response.get('screenshots', []))}")
                    print(f"    Response: {response_text}")

                else:
                    error_msg = response.get('error', 'No response') if response else 'Agent failed to respond'
                    results.append({
                        "test": f"Test {i+1}",
                        "prompt": prompt,
                        "success": False,
                        "error": error_msg,
                        "response_time": f"{end_time - start_time:.2f}s"
                    })

                    print(f"    ❌ Failed: {error_msg}")

            except Exception as e:
                results.append({
                    "test": f"Test {i+1}",
                    "prompt": prompt,
                    "success": False,
                    "error": str(e),
                    "response_time": "N/A"
                })
                print(f"    ❌ Exception: {str(e)}")

        return results

    except Exception as e:
        print(f"  ❌ Android Perplexity agent initialization failed: {str(e)}")
        return {"error": "Android Perplexity agent not available", "details": str(e)}

def run_comprehensive_model_test():
    """Run comprehensive tests for all available models"""
    print("=" * 80)
    print("🚀 COMPREHENSIVE MODEL TESTING SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")

    all_results = {
        "test_timestamp": datetime.now().isoformat(),
        "results": {}
    }

    # Test 1: Sonnet 4.5 via Orchestrator
    try:
        sonnet_results = test_sonnet_45_via_orchestrator()
        all_results["results"]["sonnet_45_orchestrator"] = sonnet_results

        # Count successes
        sonnet_success_count = sum(1 for r in sonnet_results if r.get('is_sonnet_45', False))
        sonnet_total = len(sonnet_results)
        print(f"\n📊 Sonnet 4.5 Selection: {sonnet_success_count}/{sonnet_total} tests selected Sonnet 4.5")

    except Exception as e:
        print(f"\n❌ Sonnet 4.5 test failed: {str(e)}")
        all_results["results"]["sonnet_45_orchestrator"] = {"error": str(e)}

    # Test 2: ISH.chat Providers
    try:
        ish_results = test_ish_chat_providers()
        all_results["results"]["ish_chat_providers"] = ish_results

        # Count successes
        ish_success_count = 0
        ish_total = 0
        for provider, tests in ish_results.items():
            if isinstance(tests, list):
                for test in tests:
                    ish_total += 1
                    if test.get('success', False):
                        ish_success_count += 1

        if ish_total > 0:
            print(f"\n📊 ISH.chat Providers: {ish_success_count}/{ish_total} tests successful")

    except Exception as e:
        print(f"\n❌ ISH.chat test failed: {str(e)}")
        all_results["results"]["ish_chat_providers"] = {"error": str(e)}

    # Test 3: Android Perplexity
    try:
        android_results = test_android_perplexity()
        all_results["results"]["android_perplexity"] = android_results

        # Count successes
        if isinstance(android_results, list):
            android_success_count = sum(1 for r in android_results if r.get('success', False))
            android_total = len(android_results)
            print(f"\n📊 Android Perplexity: {android_success_count}/{android_total} tests successful")

    except Exception as e:
        print(f"\n❌ Android Perplexity test failed: {str(e)}")
        all_results["results"]["android_perplexity"] = {"error": str(e)}

    # Save results
    results_file = f"model_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE MODEL TESTING COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {results_file}")
    print(f"Completed at: {datetime.now().isoformat()}")

    # Summary
    total_categories = len([r for r in all_results["results"].values() if "error" not in r])
    print(f"✅ Model categories tested: {total_categories}")

    return all_results

if __name__ == "__main__":
    run_comprehensive_model_test()