#!/usr/bin/env python3
"""
Test Domain Access for Bulgarian Legal Domains
Tests if the specific domains work with Google CSE
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_domain_access():
    """Test if the Bulgarian legal domains work with Google CSE"""
    print("🔍 Testing Bulgarian Legal Domain Access with Google CSE")
    print("=" * 65)
    
    try:
        from tools import google_cse_search
        from bulgarian_legal_domains import get_domain_list
        
        domains = get_domain_list()
        test_queries = [
            "решение",
            "съд", 
            "правен",
            "закон"
        ]
        
        print(f"✅ Testing {len(domains)} domains with {len(test_queries)} queries")
        print(f"Domains: {', '.join(domains)}")
        print()
        
        for i, domain in enumerate(domains, 1):
            print(f"🏛️ {i}. Testing domain: {domain}")
            
            # Test each domain with different queries
            domain_working = False
            
            for query in test_queries:
                try:
                    print(f"   🔍 Query: '{query}'")
                    
                    # Test direct site search
                    results = google_cse_search.invoke({
                        "query": query,
                        "site_search": domain,
                        "country": "bg",
                        "language": "lang_bg", 
                        "num_results": 3
                    })
                    
                    if isinstance(results, list) and results:
                        print(f"   ✅ Found {len(results)} results")
                        domain_working = True
                        
                        # Show first result as sample
                        first_result = results[0]
                        title = first_result.get('title', 'No title')[:50]
                        href = first_result.get('href', 'No URL')
                        print(f"   📄 Sample: {title}...")
                        print(f"   🔗 URL: {href}")
                        break  # Found results, move to next domain
                    else:
                        print(f"   ❌ No results for '{query}'")
                        
                except Exception as e:
                    print(f"   ❌ Error with '{query}': {e}")
                    continue
            
            if domain_working:
                print(f"   🎉 Domain {domain} is WORKING\n")
            else:
                print(f"   ⚠️ Domain {domain} returned NO RESULTS\n")
                
                # Try alternative approach - general search with site: operator
                print(f"   🔄 Trying alternative approach for {domain}...")
                try:
                    alt_query = f"site:{domain} право OR решение OR съд"
                    alt_results = google_cse_search.invoke({
                        "query": alt_query,
                        "country": "bg",
                        "language": "lang_bg",
                        "num_results": 5
                    })
                    
                    if isinstance(alt_results, list) and alt_results:
                        print(f"   ✅ Alternative search found {len(alt_results)} results")
                        sample = alt_results[0]
                        print(f"   📄 Sample: {sample.get('title', 'No title')[:50]}...")
                    else:
                        print(f"   ❌ Alternative search also failed")
                        
                except Exception as e:
                    print(f"   ❌ Alternative search error: {e}")
                    
                print()
        
        print("=" * 65)
        print("📋 DOMAIN ACCESS TEST SUMMARY")
        print("=" * 65)
        
        # Test general Bulgarian legal search
        print("\n🇧🇬 Testing general Bulgarian legal search...")
        try:
            general_results = google_cse_search.invoke({
                "query": "българско право съд решение",
                "country": "bg",
                "language": "lang_bg",
                "num_results": 5
            })
            
            if isinstance(general_results, list) and general_results:
                print(f"✅ General Bulgarian legal search: {len(general_results)} results")
                
                # Check which domains appear in results
                domain_hits = {}
                for result in general_results:
                    href = result.get('href', '')
                    for domain in domains:
                        if domain in href:
                            domain_hits[domain] = domain_hits.get(domain, 0) + 1
                
                if domain_hits:
                    print("📊 Domain distribution in general search:")
                    for domain, count in domain_hits.items():
                        print(f"   • {domain}: {count} results")
                else:
                    print("⚠️ None of our target domains appeared in general search")
                    print("📋 Sample domains that did appear:")
                    for result in general_results[:3]:
                        href = result.get('href', '')
                        print(f"   • {href}")
                        
            else:
                print("❌ General Bulgarian legal search failed")
                
        except Exception as e:
            print(f"❌ General search error: {e}")
        
        print("\n💡 Recommendations:")
        print("1. Check if these domains are indexed by Google")
        print("2. Verify Google CSE configuration includes these domains")
        print("3. Consider using broader search terms")
        print("4. Check if domains require special handling")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Bulgarian Legal Domain Access Test\n")
    success = test_domain_access()
    
    if success:
        print("\n✅ Domain access test completed")
    else:
        print("\n❌ Domain access test failed")
        
    sys.exit(0 if success else 1) 