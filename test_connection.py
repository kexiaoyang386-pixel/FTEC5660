#!/usr/bin/env python3
"""
Test basic connectivity to OpenAI API endpoints
"""
import urllib.request
import json
import ssl

def test_connectivity():
    print("🌐 Testing basic internet connectivity...")
    
    # Test 1: Basic connectivity
    try:
        response = urllib.request.urlopen("https://httpbin.org/ip", timeout=5)
        data = json.loads(response.read().decode())
        print(f"✅ Internet OK - Your IP: {data['origin']}")
    except Exception as e:
        print(f"❌ Internet connectivity failed: {e}")
        return False
    
    # Test 2: OpenAI API endpoint reachability
    print("\n🔗 Testing OpenAI API endpoint...")
    try:
        # Just test if we can reach the API domain
        response = urllib.request.urlopen("https://api.openai.com/v1/models", timeout=5)
        print(f"✅ OpenAI API reachable (status: {response.getcode()})")
    except Exception as e:
        print(f"❌ OpenAI API not reachable: {e}")
        return False
    
    return True

def test_api_key_format():
    print("\n🔑 Checking API key format...")
    key = ""
    
    if not key.startswith("sk-"):
        print("❌ API key should start with 'sk-'")
        return False
    
    if len(key) < 40:
        print("❌ API key seems too short")
        return False
    
    print(f"✅ API key format looks correct (length: {len(key)})")
    return True

if __name__ == "__main__":
    print("🧪 OpenAI API Diagnostic Tool")
    print("=" * 40)
    
    # Check API key format
    api_key_ok = test_api_key_format()
    
    # Check connectivity
    connectivity_ok = test_connectivity()
    
    print("\n📊 Summary:")
    print(f"API Key Format: {'✅' if api_key_ok else '❌'}")
    print(f"Connectivity: {'✅' if connectivity_ok else '❌'}")
    
    if not connectivity_ok:
        print("\n💡 If connectivity fails:")
        print("1. Check if you're behind a firewall/proxy")
        print("2. Try using VPN or different network")
        print("3. Check DNS settings (try: nslookup api.openai.com)")
    
    if api_key_ok and not connectivity_ok:
        print("\n🤔 API key format is OK but network is blocked.")
        print("This is likely a network/firewall issue, not a key issue.")
