#!/usr/bin/env python3
"""
Test script to verify the search functionality works with the fixes.
This will test both Google CSE (if configured) and DuckDuckGo fallback.
"""

import os
import sys
import logging
from typing import List, Dict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_search_functions():
    """Test the search functions to ensure they work properly."""
    
    try:
        # Import the search functions
        from enhanced_legal_tools import fallback_ddg_search, google_cse_search_legal
        
        print("🔍 Testing Bulgarian Legal Search Functions")
        print("=" * 50)
        
        # Test query
        test_query = "трудов кодекс България"
        
        print(f"\n1. Testing DuckDuckGo fallback search...")
        print(f"Query: {test_query}")
        
        ddg_results = fallback_ddg_search(test_query)
        
        if ddg_results:
            print(f"✅ DuckDuckGo search successful! Found {len(ddg_results)} results")
            for i, result in enumerate(ddg_results[:3], 1):
                print(f"  {i}. {result['title'][:60]}...")
                print(f"     URL: {result['href']}")
                print(f"     Source: {result['source_domain']}")
        else:
            print("❌ DuckDuckGo search returned no results")
        
        print(f"\n2. Testing Google CSE search (with fallback)...")
        print(f"Query: {test_query}")
        
        cse_results = google_cse_search_legal(test_query)
        
        if cse_results:
            print(f"✅ Search successful! Found {len(cse_results)} results")
            for i, result in enumerate(cse_results[:3], 1):
                print(f"  {i}. {result['title'][:60]}...")
                print(f"     URL: {result['href']}")
                print(f"     Source: {result['source_domain']}")
        else:
            print("❌ Search returned no results")
        
        print(f"\n3. Testing site-specific search...")
        site_query = "закон"
        site_domain = "lex.bg"
        
        site_results = google_cse_search_legal(site_query, site_search=site_domain)
        
        if site_results:
            print(f"✅ Site-specific search successful! Found {len(site_results)} results from {site_domain}")
            for i, result in enumerate(site_results[:2], 1):
                print(f"  {i}. {result['title'][:60]}...")
                print(f"     URL: {result['href']}")
        else:
            print(f"❌ Site-specific search for {site_domain} returned no results")
        
        print("\n" + "=" * 50)
        print("🎉 Search function tests completed!")
        
        # Summary
        total_results = len(ddg_results) + len(cse_results) + len(site_results)
        print(f"📊 Total results found across all tests: {total_results}")
        
        if total_results > 0:
            print("✅ Search functionality is working properly!")
            return True
        else:
            print("⚠️ No results found in any test - check network connection or API keys")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure enhanced_legal_tools.py is in the current directory")
        return False
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def check_environment():
    """Check if the environment is properly configured."""
    
    print("🔧 Checking Environment Configuration")
    print("=" * 40)
    
    # Check Google CSE configuration
    google_api_key = os.getenv('GOOGLE_CSE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')
    
    if google_api_key and google_cse_id:
        print("✅ Google CSE API configured")
    else:
        print("⚠️ Google CSE API not configured - will use DuckDuckGo only")
        print("   Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID environment variables")
    
    # Check OpenAI configuration
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if openai_api_key:
        print("✅ OpenAI API configured")
    else:
        print("⚠️ OpenAI API not configured - AI features may not work")
        print("   Set OPENAI_API_KEY environment variable")
    
    print()

if __name__ == "__main__":
    print("🚀 Bulgarian Legal Search System - Test Suite")
    print("=" * 60)
    
    check_environment()
    
    success = test_search_functions()
    
    if success:
        print("\n🎉 All tests passed! The search system is ready to use.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the configuration and try again.")
        sys.exit(1) 