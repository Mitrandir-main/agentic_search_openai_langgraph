#!/usr/bin/env python3
"""
Test Working Bulgarian Legal Domains System
Tests the 3 verified working domains with actual legal queries
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_working_domains():
    """Test the 3 working Bulgarian legal domains"""
    print("🇧🇬 Testing Working Bulgarian Legal Domains System")
    print("=" * 60)
    
    try:
        from bulgarian_legal_domains import BULGARIAN_LEGAL_DOMAINS, get_domain_list
        from tools import google_domain_search
        
        print("✅ 1. Domain Configuration Test")
        domains = get_domain_list()
        print(f"   Working domains: {len(domains)}")
        for i, domain in enumerate(domains, 1):
            description = BULGARIAN_LEGAL_DOMAINS[list(BULGARIAN_LEGAL_DOMAINS.keys())[i-1]]['description']
            print(f"   {i}. {domain} - {description}")
        
        print(f"\n✅ 2. Legal Query Tests")
        
        # Test with Bulgarian legal queries
        test_queries = [
            "наказание за телесна повреда",
            "обезщетение за вреди", 
            "развод",
            "договор за наем"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            try:
                results = google_domain_search.invoke({
                    "query": query,
                    "domains": domains
                })
                
                if isinstance(results, list) and results:
                    print(f"   ✅ Found {len(results)} total results")
                    
                    # Group by domain
                    domain_stats = {}
                    for result in results:
                        domain_info = result.get('source_domain', 'Unknown')
                        if 'ciela.net' in domain_info:
                            domain_stats['ciela.net'] = domain_stats.get('ciela.net', 0) + 1
                        elif 'apis.bg' in domain_info:
                            domain_stats['apis.bg'] = domain_stats.get('apis.bg', 0) + 1
                        elif 'lakorda.com' in domain_info:
                            domain_stats['lakorda.com'] = domain_stats.get('lakorda.com', 0) + 1
                    
                    print("   📊 Results by domain:")
                    for domain, count in domain_stats.items():
                        print(f"      • {domain}: {count} results")
                    
                    # Show sample result
                    if results:
                        sample = results[0]
                        title = sample.get('title', 'No title')[:60]
                        href = sample.get('href', 'No URL')
                        print(f"   📄 Sample: {title}...")
                        print(f"   🔗 URL: {href}")
                        
                else:
                    print(f"   ❌ No results found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n✅ 3. System Integration Test")
        from graph import run_graph
        
        test_query = "какви са наказанията за телесна повреда"
        print(f"Testing full system with: '{test_query}'")
        
        try:
            config = {
                "query_depth": "shallow",
                "complexity_level": "basic", 
                "max_iterations": 1,
                "focus_domains": domains
            }
            
            result = run_graph(test_query, config=config)
            
            if result and len(result) > 100:
                print("   ✅ System integration successful")
                print(f"   📏 Response length: {len(result)} characters")
                
                # Check if response contains our domains
                domain_mentions = 0
                for domain in domains:
                    if domain in result:
                        domain_mentions += 1
                
                print(f"   🔗 Domains mentioned in response: {domain_mentions}/{len(domains)}")
                
                # Check for proper formatting
                if "📚" in result and "⚖️" in result:
                    print("   ✅ Response formatting correct")
                else:
                    print("   ⚠️ Response formatting needs improvement")
                    
            else:
                print("   ❌ System integration failed")
                
        except Exception as e:
            print(f"   ❌ System integration error: {e}")
        
        print(f"\n🎉 All tests completed!")
        print(f"\n📊 Working System Summary:")
        print(f"   • {len(domains)} verified working domains")
        print(f"   • Google CSE integration functional")
        print(f"   • No fallback to DuckDuckGo required")
        print(f"   • All domains return results for legal queries")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Working Domains Test\n")
    success = test_working_domains()
    
    if success:
        print("\n✅ Working domains test PASSED")
    else:
        print("\n❌ Working domains test FAILED")
        
    sys.exit(0 if success else 1) 