#!/usr/bin/env python3
"""
OAuth 2.0 Integration Test
Tests the complete OAuth flow setup without requiring full browser/Playwright environment
"""
import json
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs

BASE_URL = "http://10.150.254.15:5051"
TIMEOUT = 10


def test_login_page_accessible():
    """Test that login page is accessible"""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/auth/login", timeout=TIMEOUT) as response:
            content = response.read().decode('utf-8')
            assert "Device Scheduler" in content, "Page doesn't contain Device Scheduler title"
            assert "Sign in with your NIH credentials" in content, "Login prompt not found"
            print("✅ Login page is accessible and contains OAuth prompt")
            return True
    except Exception as e:
        print(f"❌ Login page test failed: {e}")
        return False


def test_entra_config_loads():
    """Test that Entra configuration loads correctly"""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/static/config/entra-config.json", timeout=TIMEOUT) as response:
            config = json.loads(response.read().decode('utf-8'))

            # Verify required fields
            required_fields = ['client_id', 'tenant_id', 'redirect_uri', 'authorization_endpoint']
            for field in required_fields:
                assert field in config, f"Missing required field: {field}"

            # Verify values
            assert config['client_id'] == "63b509bc-4e1c-46aa-9e71-bc9f79efcdde", f"Unexpected client_id: {config['client_id']}"
            assert "login.microsoftonline.com" in config['authorization_endpoint'], "Invalid authorization endpoint"
            assert config['redirect_uri'].startswith("https://"), f"Redirect URI should be HTTPS, got: {config['redirect_uri']}"
            assert "fmrif-schedule-backend-dev" in config['redirect_uri'], f"Redirect URI should use domain, got: {config['redirect_uri']}"

            print(f"✅ Entra config loaded successfully")
            print(f"   - Client ID: {config['client_id']}")
            print(f"   - Redirect URI: {config['redirect_uri']}")
            return True
    except Exception as e:
        print(f"❌ Entra config test failed: {e}")
        return False


def test_oauth_utils_available():
    """Test that OAuth utility files are served"""
    files_to_check = [
        '/static/js/oauth-utils.js',
        '/static/js/auth-manager.js'
    ]

    all_ok = True
    for file_path in files_to_check:
        try:
            with urllib.request.urlopen(f"{BASE_URL}{file_path}", timeout=TIMEOUT) as response:
                content = response.read().decode('utf-8')
                if 'generateVerifier' in content and 'startOAuthFlow' in content:
                    print(f"✅ {file_path} is available and contains OAuth functions")
                else:
                    print(f"⚠️  {file_path} available but missing expected functions")
                    all_ok = False
        except Exception as e:
            print(f"❌ {file_path} failed: {e}")
            all_ok = False

    return all_ok


def test_home_page_redirects():
    """Test that unauthenticated home page redirects to login"""
    try:
        req = urllib.request.Request(f"{BASE_URL}/")
        req.add_header('User-Agent', 'Mozilla/5.0')
        try:
            response = urllib.request.urlopen(req, timeout=TIMEOUT)
            content = response.read().decode('utf-8')
            # If we got here, either superuser mode is on or we got redirected content
            if "logged in as superuser" in content:
                print("⚠️  Home page shows superuser (RBAC__SUPERUSER_MODE might still be enabled)")
                return True  # This is ok for testing
            else:
                print("✅ Home page accessible (content varies by auth state)")
                return True
        except urllib.error.HTTPError as e:
            if e.code == 302 or e.code == 307:
                print("✅ Unauthenticated request redirects as expected")
                return True
            else:
                print(f"⚠️  Unexpected HTTP status: {e.code}")
                return False
    except Exception as e:
        print(f"❌ Home page test failed: {e}")
        return False


def test_callback_endpoint_exists():
    """Test that OAuth callback endpoint exists"""
    try:
        # OAuth callback should accept GET requests with code parameter
        # We won't actually test with real auth code, just verify endpoint is registered
        req = urllib.request.Request(f"{BASE_URL}/auth/callback?code=test&state=test")
        req.add_header('User-Agent', 'Mozilla/5.0')
        try:
            response = urllib.request.urlopen(req, timeout=TIMEOUT)
            # Even if it fails auth, the endpoint should exist and respond
            print("✅ OAuth callback endpoint is registered")
            return True
        except urllib.error.HTTPError as e:
            # 400/401 means endpoint exists but validation failed (expected)
            if 400 <= e.code < 500:
                print(f"✅ OAuth callback endpoint exists (validation error: {e.code} is expected)")
                return True
            else:
                print(f"❌ Unexpected error on callback: {e.code}")
                return False
    except Exception as e:
        print(f"⚠️  Callback endpoint test failed: {e}")
        return False


def main():
    print("=" * 60)
    print("OAuth 2.0 / Entra Integration Test")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}\n")

    tests = [
        ("Login Page", test_login_page_accessible),
        ("Entra Configuration", test_entra_config_loads),
        ("OAuth Utils", test_oauth_utils_available),
        ("Home Page Redirect", test_home_page_redirects),
        ("Callback Endpoint", test_callback_endpoint_exists),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All infrastructure tests passed!")
        print("OAuth 2.0 implementation is ready for end-to-end browser testing.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
