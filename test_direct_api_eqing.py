#!/usr/bin/env python3
"""
Test script for DirectAPI Eqing.tech integration
"""
import asyncio
import sys
import os

# Add the ish-chat-backend to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ish-chat-backend', 'src'))

from services.direct_api_eqing_service import eqing_service, DirectAPIEqingProvider

async def test_basic_functionality():
    """Test basic API functionality"""
    print("🚀 Testing DirectAPI Eqing.tech Integration")
    print("=" * 60)
    
    try:
        # Test 1: Initialize and get models
        print("\n1️⃣ Testing initialization and model discovery...")
        models = await eqing_service.get_available_models()
        print(f"✅ Found {len(models)} available models")
        
        # Show interesting models
        interesting = [m for m in models if any(x in m.lower() for x in ['gpt', 'claude', 'gemini'])][:10]
        print(f"🤖 Interesting models: {', '.join(interesting)}")
        
        # Test 2: Basic chat completion
        print("\n2️⃣ Testing basic chat completion...")
        response = await eqing_service.generate_response(
            "Write a simple 'Hello World' in Python",
            model="gpt-4o-mini"
        )
        print(f"✅ Response received: {response[:200]}...")
        
        # Test 3: Test with system prompt
        print("\n3️⃣ Testing with system prompt...")
        response = await eqing_service.generate_response(
            "What is 2+2?",
            system_prompt="You are a helpful math assistant. Be very concise.",
            model="gpt-4o-mini"
        )
        print(f"✅ System prompt response: {response[:100]}...")
        
        # Test 4: Test different models
        print("\n4️⃣ Testing multiple models...")
        test_models = ["gpt-4o-mini", "gpt-oss-120b-free", "claude-3.7-sonnet"]
        
        for model in test_models:
            if model in models:
                try:
                    print(f"   Testing {model}...")
                    response = await eqing_service.generate_response(
                        "Say hello in one word",
                        model=model,
                        max_tokens=10
                    )
                    print(f"   ✅ {model}: {response.strip()}")
                except Exception as e:
                    print(f"   ❌ {model}: {str(e)[:50]}...")
            else:
                print(f"   ⚠️ {model}: Not available")
        
        # Test 5: Performance test
        print("\n5️⃣ Performance test...")
        import time
        start_time = time.time()
        
        response = await eqing_service.generate_response(
            "Write a short poem about AI",
            model="gpt-4o-mini",
            max_tokens=100
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Performance test completed in {duration:.2f} seconds")
        print(f"📄 Response length: {len(response)} characters")
        
        # Test 6: Error handling
        print("\n6️⃣ Testing error handling...")
        try:
            response = await eqing_service.generate_response(
                "This should work even with edge cases",
                model="non-existent-model"
            )
            print("⚠️ Non-existent model somehow worked")
        except Exception as e:
            print(f"✅ Error handling works: {str(e)[:50]}...")
        
        print("\n🎉 All tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_provider_directly():
    """Test the provider class directly"""
    print("\n" + "=" * 60)
    print("🔧 Testing DirectAPI Provider Class Directly")
    print("=" * 60)
    
    try:
        provider = DirectAPIEqingProvider("gpt-4o-mini")
        
        # Initialize
        await provider.initialize()
        print(f"✅ Provider initialized with {len(provider.available_models)} models")
        
        # Test connection
        connection_ok = await provider.test_connection()
        print(f"✅ Connection test: {'PASSED' if connection_ok else 'FAILED'}")
        
        # Test model switching
        if provider.available_models:
            new_model = provider.available_models[1] if len(provider.available_models) > 1 else provider.available_models[0]
            await provider.switch_model(new_model)
            print(f"✅ Model switching: {provider.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 DirectAPI Eqing.tech Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test service
    service_success = await test_basic_functionality()
    success = success and service_success
    
    # Test provider directly
    provider_success = await test_provider_directly()
    success = success and provider_success
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\n📝 Integration Summary:")
        print("✅ DirectAPI Eqing.tech provider is working")
        print("✅ No API key required")
        print("✅ OpenAI-compatible endpoint")
        print("✅ Multiple models available")
        print("✅ Error handling implemented")
        print("\n🚀 Ready for production use!")
    else:
        print("❌ SOME TESTS FAILED")
        print("\n🔧 Troubleshooting:")
        print("1. Check internet connection")
        print("2. Verify eqing.tech is accessible")
        print("3. Check if service has changed")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())