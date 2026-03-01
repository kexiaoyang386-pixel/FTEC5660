#!/usr/bin/env python3
"""
Test script to verify OpenAI API key works with different timeout settings
"""
import os
import time
from openai import OpenAI

OPENAI_API_KEY = "sk-e2GpF64Q21z5Ha1qt3Eg6NJiiBJrhFuf5s4rhr6nH9M78OWR"

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found")
    exit(1)

print(f"🔑 Testing OpenAI API key: {OPENAI_API_KEY[:20]}...")

# Test with different timeout settings
timeouts = [5, 10, 20, 30]

for timeout in timeouts:
    print(f"\n⏱️  Testing with {timeout}s timeout...")
    try:
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=timeout)
        
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        elapsed = time.time() - start_time
        
        print(f"✅ Success in {elapsed:.2f}s!")
        print(f"📝 Response: {response.choices[0].message.content.strip()}")
        break
        
    except Exception as e:
        print(f"❌ Failed with {timeout}s timeout: {e}")
        if "401" in str(e):
            print("🚫 This looks like an invalid API key. Check your key.")
            break
        elif "timeout" in str(e).lower():
            print("⏳ Network timeout - trying longer timeout...")
            continue
        else:
            print(f"🔥 Other error: {e}")
            break
else:
    print("\n💡 Suggestions:")
    print("1. Check if the API key is valid")
    print("2. Check internet connection")
    print("3. Try setting HTTP_PROXY/HTTPS_PROXY if behind firewall")
    print("4. Use a different network")
