#!/usr/bin/env python3
"""
Test Bright Data Proxy Connection
Quick script to verify proxy works before integrating into scrapers
"""
import requests
import sys

# Bright Data proxy configuration
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = 33335
PROXY_USER = "brd-customer-hl_b295a417-zone-datacenter_proxy2"
PROXY_PASS = "90wo2m3e40vv"

# Build proxy URL
proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

def test_proxy():
    """Test proxy connection and get geo info"""
    print("🔍 Testing Bright Data Proxy Connection...\n")

    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }

    try:
        # Test 1: Get IP
        print("1️⃣  Checking IP address...")
        response = requests.get('https://api.ipify.org?format=json', proxies=proxies, timeout=10)
        ip_data = response.json()
        print(f"   ✅ IP: {ip_data['ip']}\n")

        # Test 2: Get full geo info
        print("2️⃣  Checking geolocation...")
        response = requests.get('https://geo.brdtest.com/mygeo.json', proxies=proxies, timeout=10)
        geo_data = response.json()
        print(f"   ✅ Country: {geo_data.get('country')}")
        print(f"   ✅ City: {geo_data.get('city')}")
        print(f"   ✅ Region: {geo_data.get('region')}\n")

        # Test 3: Test with GATC API (most important test)
        print("3️⃣  Testing GATC access...")
        gatc_url = "https://adstransparency.google.com"
        response = requests.get(gatc_url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ GATC accessible (status: {response.status_code})\n")
        else:
            print(f"   ⚠️  GATC returned status: {response.status_code}\n")

        print("✅ All proxy tests passed!")
        print(f"\n📝 Use this proxy configuration:")
        print(f"   Host: {PROXY_HOST}")
        print(f"   Port: {PROXY_PORT}")
        print(f"   User: {PROXY_USER}")
        print(f"   Pass: {PROXY_PASS}")

        return True

    except requests.exceptions.ProxyError as e:
        print(f"❌ Proxy connection failed: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Request timed out: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_proxy()
    sys.exit(0 if success else 1)
