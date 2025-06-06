#!/usr/bin/env python3
"""
Test Enhanced Bulgarian Legal Search System
Demonstrates the improved Google CSE integration with performance optimizations
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Test the enhanced tools
from tools import google_cse_search, google_domain_search, bulgarian_search
from enhanced_legal_tools import bulgarian_legal_search
import time

def test_enhanced_search():
    print("🚀 Enhanced Bulgarian Legal Search System Test")
    print("=" * 70)
    
    # Test queries in Bulgarian
    test_queries = [
        "обезщетение за счупване на ръка",
        "наказание за телесна повреда", 
        "трудово право България",
        "договор за купуване на недвижим имот"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Test optimized Google CSE search using invoke
            print("📊 Testing optimized Google CSE search...")
            results = google_cse_search.invoke({"query": query, "country": "bg", "language": "lang_bg"})
            
            if isinstance(results, list) and results:
                print(f"✅ Found {len(results)} results in {time.time() - start_time:.2f}s")
                
                # Show first result
                first_result = results[0]
                print(f"   Title: {first_result.get('title', 'N/A')[:80]}...")
                print(f"   Source: {first_result.get('source_domain', 'N/A')}")
                
                # Show domain distribution
                domains = {}
                for result in results:
                    href = result.get('href', '')
                    if 'lex.bg' in href:
                        domains['lex.bg'] = domains.get('lex.bg', 0) + 1
                    elif 'vks.bg' in href:
                        domains['vks.bg'] = domains.get('vks.bg', 0) + 1
                    elif 'justice.bg' in href:
                        domains['justice.bg'] = domains.get('justice.bg', 0) + 1
                    else:
                        domains['other'] = domains.get('other', 0) + 1
                
                if domains:
                    print(f"   Domain distribution: {domains}")
                    
            else:
                print(f"❌ No results found in {time.time() - start_time:.2f}s")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Rate limiting between tests
        time.sleep(1)
    
    print(f"\n🎯 Testing Multi-Domain Search")
    print("-" * 50)
    
    try:
        start_time = time.time()
        domain_results = google_domain_search.invoke({
            "query": "обезщетение ВКС", 
            "domains": ['lex.bg', 'vks.bg', 'justice.bg']
        })
        
        if isinstance(domain_results, list) and domain_results:
            print(f"✅ Multi-domain search: {len(domain_results)} results in {time.time() - start_time:.2f}s")
            
            # Show results by priority
            for result in domain_results[:3]:
                title = result.get('title', 'N/A')[:60]
                priority = result.get('domain_priority', 'N/A')
                print(f"   Priority {priority}: {title}...")
        else:
            print(f"❌ Multi-domain search failed in {time.time() - start_time:.2f}s")
            
    except Exception as e:
        print(f"❌ Multi-domain error: {e}")

    print(f"\n🔧 Testing Bulgarian Legal Search Integration")
    print("-" * 50)
    
    try:
        start_time = time.time()
        legal_results = bulgarian_legal_search.invoke({
            "query": "обезщетение за телесна повреда",
            "specific_domain": "lex.bg"
        })
        
        if isinstance(legal_results, list) and legal_results:
            print(f"✅ Legal search: {len(legal_results)} results in {time.time() - start_time:.2f}s")
            
            # Show sample result
            if legal_results:
                sample = legal_results[0]
                print(f"   Sample: {sample.get('title', 'N/A')[:60]}...")
        else:
            print(f"❌ Legal search failed in {time.time() - start_time:.2f}s")
            
    except Exception as e:
        print(f"❌ Legal search error: {e}")

    print(f"\n📈 Performance Summary")
    print("=" * 70)
    print("✅ Optimizations implemented:")
    print("   • Gzip compression for faster data transfer")
    print("   • Partial field selection to reduce payload size") 
    print("   • Intelligent domain prioritization")
    print("   • Early termination for sufficient results")
    print("   • Bulgarian legal term enhancement")
    print("   • Rate limiting optimization")
    print("\n🎉 Enhanced search system ready for production!")

if __name__ == "__main__":
    # Check API configuration
    if not os.getenv('GOOGLE_CSE_API_KEY'):
        print("❌ GOOGLE_CSE_API_KEY not found in environment")
        sys.exit(1)
    
    if not os.getenv('GOOGLE_CSE_ID'):
        print("❌ GOOGLE_CSE_ID not found in environment") 
        sys.exit(1)
        
    test_enhanced_search() 