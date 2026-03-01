#!/usr/bin/env python3
"""
Test script to verify OpenAI API key works
"""
import os
from openai import OpenAI

# Option 1: Use the hardcoded key from utils.py
OPENAI_API_KEY = ""

# Option 2: Use environment variable if set
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found")
    exit(1)

print(f"🔑 Testing OpenAI API key: {OPENAI_API_KEY[:20]}...")

try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Simple test request
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'API test successful' if you can see this."}],
        max_tokens=10,
        timeout=10  # 10 second timeout
    )
    
    print("✅ OpenAI API key works!")
    print(f"📝 Response: {response.choices[0].message.content.strip()}")
    
except Exception as e:
    print(f"❌ OpenAI API test failed: {e}")
    exit(1)
