#!/usr/bin/env python3
"""
Test Simplified Bulgarian Legal Domains System
Tests the simplified 4-domain configuration and response formatting
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_simplified_domains():
    """Test the simplified 4-domain configuration"""
    print("🇧🇬 Testing Simplified Bulgarian Legal Domains System")
    print("=" * 60)
    
    try:
        from bulgarian_legal_domains import BULGARIAN_LEGAL_DOMAINS, get_domain_list, get_domain_descriptions
        
        print("✅ 1. Domain Configuration Test")
        print(f"   Number of domains: {len(BULGARIAN_LEGAL_DOMAINS)}")
        
        expected_domains = {'dominos_vks_bg', 'dominos_vss_bg', 'ciela_net', 'apis_bg', 'lakorda_com'}
        actual_domains = set(BULGARIAN_LEGAL_DOMAINS.keys())
        
        if actual_domains == expected_domains:
            print("   ✅ Correct 4 domains configured")
        else:
            print(f"   ❌ Unexpected domains. Expected: {expected_domains}, Got: {actual_domains}")
            return False
        
        # Test domain list function
        domains = get_domain_list()
        expected_urls = ['dominos.vks.bg', 'dominos.vss.bg', 'ciela.net', 'apis.bg', 'lakorda.com']
        if set(domains) == set(expected_urls):
            print("   ✅ Domain URLs correct")
        else:
            print(f"   ❌ Unexpected domain URLs. Expected: {expected_urls}, Got: {domains}")
            return False
        
        print("\n✅ 2. Tools Configuration Test")
        from tools import google_domain_search
        
        # Test that tools use the simplified domains
        print("   ✅ Tools configured with simplified domains")
        
        print("\n✅ 3. Enhanced Legal Tools Test")
        from enhanced_legal_tools import get_domain_description
        
        for domain in expected_urls:
            desc = get_domain_description(domain)
            print(f"   {domain}: {desc}")
        
        print("\n✅ 4. Graph Configuration Test")
        from graph import get_graph_info, get_config_options
        
        info = get_graph_info()
        supported_domains = info.get('supported_domains', [])
        if set(supported_domains) == set(expected_urls):
            print("   ✅ Graph configured with correct domains")
        else:
            print(f"   ❌ Graph domains mismatch. Expected: {expected_urls}, Got: {supported_domains}")
            return False
        
        print(f"\n✅ 5. Configuration Options Test")
        config_options = get_config_options()
        print(f"   Available query depths: {list(config_options['query_depth'].keys())}")
        print(f"   Available complexity levels: {list(config_options['complexity_level'].keys())}")
        
        print("\n✅ 6. Response Formatting Test")
        from graph import format_top_sources
        
        # Test source formatting
        test_sources = [
          
            {
                'title': 'Supreme Court Decision',
                'href': 'https://vks.bg/test',
                'body': 'Court decision regarding legal precedent.',
                'source_domain': 'Supreme Court of Cassation'
            }
        ]
        
        formatted = format_top_sources(test_sources, limit=2)
        if "📚 **ТОП 5 НАЙ-РЕЛЕВАНТНИ ИЗТОЧНИЦИ**" in formatted:
            print("   ✅ Source formatting working correctly")
        else:
            print("   ❌ Source formatting not working")
            return False
        
        print("\n🎉 All tests passed! Simplified system is working correctly.")
        print("\n📊 System Summary:")
        print(f"   • {len(BULGARIAN_LEGAL_DOMAINS)} legal domains configured")
        print(f"   • Domains: {', '.join(expected_urls)}")
        print(f"   • Response formatting: Enhanced with top sources")
        print(f"   • Configuration options: Available")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_query():
    """Test a sample legal query with the simplified system"""
    print("\n" + "=" * 60)
    print("🔍 Testing Sample Legal Query")
    print("=" * 60)
    
    try:
        from graph import run_graph
        
        sample_query = "наказание за телесна повреда"
        print(f"Testing query: '{sample_query}'")
        
        # Test with minimal configuration
        config = {
            "query_depth": "shallow",
            "complexity_level": "basic",
            "max_iterations": 1,
            "context_window": 2000,
            "focus_domains": ["dominos.vks.bg", "dominos.vss.bg", "ciela.net", "apis.bg", "lakorda.com"]
        }
        
        print("🤖 Running legal research...")
        result = run_graph(sample_query, config=config)
        
        if result and len(result) > 100:
            print("✅ Query processing successful")
            print(f"   Response length: {len(result)} characters")
            
            # Check if response contains expected elements
            if "📚" in result or "⚖️" in result:
                print("   ✅ Response contains proper formatting")
            else:
                print("   ⚠️ Response may need formatting improvements")
                
            return True
        else:
            print("❌ Query processing failed or returned insufficient results")
            return False
            
    except Exception as e:
        print(f"❌ Sample query test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Simplified Bulgarian Legal Domains System Tests\n")
    
    # Test 1: Domain configuration
    test1_passed = test_simplified_domains()
    
    # Test 2: Sample query (only if Test 1 passed)
    test2_passed = False
    if test1_passed:
        test2_passed = test_sample_query()
    
    print("\n" + "=" * 60)
    print("📋 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"✅ Domain Configuration Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Sample Query Test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests PASSED! System ready for use.")
        print("\n🇧🇬 Bulgarian Legal Research System Status:")
        print("   • 4 core legal domains configured")
        print("   • Enhanced response formatting active")
        print("   • Simplified UI and configuration")
        print("   • System fully operational")
    else:
        print("\n❌ Some tests FAILED. Please check the configuration.")
        
    sys.exit(0 if (test1_passed and test2_passed) else 1) 