#!/usr/bin/env python3
"""
Google CSE Debug Script
Helps diagnose and fix Google Custom Search Engine issues including forbidden errors.
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_google_cse_detailed():
    """Detailed Google CSE testing with error analysis."""
    print("🔍 Google CSE Detailed Diagnostics")
    print("=" * 60)
    
    # Get API credentials
    api_key = os.getenv('GOOGLE_CSE_API_KEY')
    cse_id = os.getenv('GOOGLE_CSE_ID')
    
    print(f"API Key: {api_key[:10]}...{api_key[-6:] if api_key and len(api_key) > 16 else 'INVALID'}")
    print(f"CSE ID: {cse_id[:15]}...{cse_id[-6:] if cse_id and len(cse_id) > 21 else 'INVALID'}")
    print()
    
    if not api_key or not cse_id:
        print("❌ Missing API key or CSE ID")
        return False
    
    # Test basic API connectivity
    print("🌐 Testing Google CSE API connectivity...")
    
    try:
        # Simple test query
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': 'test',
            'num': 1
        }
        
        print(f"Request URL: {url}")
        print(f"Parameters: {json.dumps(params, indent=2)}")
        print()
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            print(f"Search Information: {data.get('searchInformation', {})}")
            
            items = data.get('items', [])
            print(f"Results returned: {len(items)}")
            
            if items:
                print(f"First result: {items[0].get('title', 'No title')}")
            
            return True
            
        elif response.status_code == 403:
            print("❌ 403 Forbidden Error Detected!")
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
            
            error_reason = error_data.get('error', {}).get('errors', [{}])[0].get('reason', 'unknown')
            error_message = error_data.get('error', {}).get('message', 'No message')
            
            print(f"\nError Reason: {error_reason}")
            print(f"Error Message: {error_message}")
            
            # Provide specific solutions based on error
            if 'keyInvalid' in error_reason:
                print("\n🔧 Solution: API Key Invalid")
                print("1. Check your GOOGLE_CSE_API_KEY in .env file")
                print("2. Verify the API key in Google Cloud Console")
                print("3. Make sure Custom Search API is enabled")
                
            elif 'accessNotConfigured' in error_reason:
                print("\n🔧 Solution: API Not Enabled")
                print("1. Go to Google Cloud Console")
                print("2. Navigate to APIs & Services > Library")
                print("3. Search for 'Custom Search API'")
                print("4. Click 'Enable'")
                
            elif 'quotaExceeded' in error_reason:
                print("\n🔧 Solution: Quota Exceeded")
                print("1. You've exceeded the free tier (100 queries/day)")
                print("2. Enable billing or wait for quota reset")
                print("3. Consider using site-restricted CSE for unlimited queries")
                
            elif 'userRateLimitExceeded' in error_reason:
                print("\n🔧 Solution: Rate Limit Exceeded")
                print("1. Too many requests per second")
                print("2. Add delays between requests")
                print("3. The system already has rate limiting built-in")
                
            else:
                print(f"\n🔧 General Solutions for '{error_reason}':")
                print("1. Verify API key permissions")
                print("2. Check CSE configuration")
                print("3. Ensure billing is enabled if needed")
            
            return False
            
        elif response.status_code == 400:
            print("❌ 400 Bad Request")
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
            
            print("\n🔧 Solution: Check request parameters")
            print("1. Verify CSE ID format")
            print("2. Check query parameters")
            return False
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_cse_configuration():
    """Test CSE configuration and settings."""
    print("\n🛠️ CSE Configuration Test")
    print("=" * 40)
    
    cse_id = os.getenv('GOOGLE_CSE_ID')
    
    if not cse_id:
        print("❌ No CSE ID configured")
        return False
    
    print(f"CSE ID: {cse_id}")
    
    # Check CSE ID format
    if ':' in cse_id:
        print("✅ CSE ID appears to be in correct format (contains ':')")
    else:
        print("⚠️ CSE ID format may be incorrect (should contain ':')")
        print("   Expected format: 012345678901234567890:abcdefghijk")
    
    # CSE Management URL
    cse_url = f"https://cse.google.com/cse/setup/basic?cx={cse_id}"
    print(f"\n🔗 CSE Management URL: {cse_url}")
    print("Use this URL to check your CSE settings")
    
    return True

def provide_setup_guidance():
    """Provide step-by-step setup guidance."""
    print("\n📋 Google CSE Setup Checklist")
    print("=" * 50)
    
    checklist = [
        "1. Create Google Cloud Project",
        "2. Enable Custom Search API",
        "3. Create API Key",
        "4. Create Custom Search Engine at cse.google.com",
        "5. Enable 'Search the entire web'",
        "6. Copy Search Engine ID",
        "7. Add both keys to .env file",
        "8. Test the configuration"
    ]
    
    for item in checklist:
        print(f"☐ {item}")
    
    print("\n🔗 Useful Links:")
    print("• Google Cloud Console: https://console.cloud.google.com/")
    print("• Custom Search Engine: https://cse.google.com/")
    print("• API Library: https://console.cloud.google.com/apis/library")
    print("• API Credentials: https://console.cloud.google.com/apis/credentials")

def test_alternative_search():
    """Test fallback search methods."""
    print("\n🔄 Testing Fallback Search Methods")
    print("=" * 45)
    
    try:
        from enhanced_legal_tools import fallback_ddg_search
        
        print("Testing DuckDuckGo fallback...")
        results = fallback_ddg_search("test query")
        
        if isinstance(results, list) and len(results) > 0:
            print(f"✅ DuckDuckGo working - {len(results)} results")
        else:
            print("⚠️ DuckDuckGo may be rate limited")
        
    except Exception as e:
        print(f"❌ Fallback search error: {e}")

def main():
    """Run all diagnostic tests."""
    print("🚀 Google CSE Comprehensive Diagnostics")
    print("=" * 70)
    print()
    
    # Test 1: Detailed CSE testing
    cse_works = test_google_cse_detailed()
    
    # Test 2: CSE configuration
    test_cse_configuration()
    
    # Test 3: Alternative search
    test_alternative_search()
    
    # Test 4: Setup guidance
    provide_setup_guidance()
    
    # Summary
    print("\n📊 Summary")
    print("=" * 20)
    if cse_works:
        print("✅ Google CSE is working correctly!")
        print("Your system should now have reliable search capabilities.")
    else:
        print("❌ Google CSE needs configuration")
        print("Follow the solutions above to fix the issues.")
        print("The system will use DuckDuckGo fallback until CSE is fixed.")

if __name__ == "__main__":
    main() 