#!/usr/bin/env python3
"""
Simple Function Tester for Bulgarian Legal Search System
Perfect for testing individual components!
"""

import sys
import time
from dotenv import load_dotenv

load_dotenv()

def test_basic_search():
    """Test basic search functions"""
    print("🔍 Testing Basic Search Functions...")
    
    try:
        from tools import internet_search_DDGO, google_cse_search, bulgarian_search
    
        # Test DuckDuckGo search
        print("\n1️⃣ Testing DuckDuckGo Search:")
        query = "българско право"
        result = internet_search_DDGO(query)
        print(f"   Query: {query}")
        print(f"   Results: {len(result) if isinstance(result, list) else 'Error'}")
        print(f"   First 200 characters: {result}...")
    
        # Test Google CSE search (if configured)
        print("\n2️⃣ Testing Google CSE Search:")
        result = google_cse_search(query)
        print(f"   Query: {query}")
        print(f"   Results: {len(result) if isinstance(result, list) else 'Error'}")
        print(f"   First 200 characters: {result}...")
        
        # Test Bulgarian-specific search
        print("\n3️⃣ Testing Bulgarian Search:")
        result = bulgarian_search(query)
        print(f"   Query: {query}")
        print(f"   Results: {len(result) if isinstance(result, list) else 'Error'}")
        print(f"   First 200 characters: {result}...")
        print("✅ Basic search tests completed!")
    
    except Exception as e:
        print(f"❌ Error in basic search test: {e}")

def test_enhanced_legal_search():
    """Test the enhanced legal search system"""
    print("\n🧠 Testing Enhanced Legal Search...")
    
    try:
        from enhanced_legal_tools import enhanced_bulgarian_legal_search_sync
        
        queries = [
            "обезщетение за трудова злополука",
            "какви са правата ми при уволнение",
            "как да предявя иск в съда"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i}️⃣ Testing Query: '{query}'")
            start_time = time.time()
            
            result = enhanced_bulgarian_legal_search_sync(
                query=query, 
                max_results=5, 
                min_relevancy=0.3
            )
            
            end_time = time.time()
            
            if isinstance(result, str) and len(result) > 100:
                print(f"   ✅ Success! Response length: {len(result)} characters")
                print(f"   ⏱️ Time taken: {end_time - start_time:.1f} seconds")
                print(f"   📄 First 200 characters: {result}...")
            else:
                print(f"   ⚠️ Short or error response: {result}")
            
            time.sleep(1)  # Be nice to APIs
        
        print("✅ Enhanced legal search tests completed!")
        
    except Exception as e:
        print(f"❌ Error in enhanced legal search test: {e}")

def test_relevancy_scoring():
    """Test the relevancy scoring system"""
    print("\n📊 Testing Relevancy Scoring...")
    
    try:
        from relevancy_scoring import BulgarianLegalRelevancyScorer
        import os
        
        if not os.getenv('OPENAI_API_KEY'):
            print("   ⚠️ Skipping - OPENAI_API_KEY not set")
            return
        
        scorer = BulgarianLegalRelevancyScorer()
        
        # Test relevancy calculation
        query = "обезщетение за злополука"
        test_content = "Според чл. 45 от ЗЗД, работникът има право на обезщетение при трудова злополука..."
        
        print(f"   Query: {query}")
        print(f"   Content: {test_content[:100]}...")
        
        relevancy = scorer.calculate_relevancy(query, test_content)
        print(f"   Relevancy Score: {relevancy:.2f}")
        
        if relevancy > 0.5:
            print("   ✅ Good relevancy score!")
        else:
            print("   ⚠️ Low relevancy score")
        
        print("✅ Relevancy scoring test completed!")
        
    except Exception as e:
        print(f"❌ Error in relevancy scoring test: {e}")

def test_streamlit_components():
    """Test if Streamlit app can be imported"""
    print("\n🖥️ Testing Streamlit App Components...")
    
    try:
        # Try importing the main app
        import enhanced_streamlit_legal_app as app
        print("   ✅ Main app imports successfully!")
        
        # Check if required functions exist
        if hasattr(app, 'main'):
            print("   ✅ Main function found!")
        else:
            print("   ⚠️ Main function not found")
        
        print("✅ Streamlit components test completed!")
        
    except Exception as e:
        print(f"❌ Error in Streamlit test: {e}")

def main():
    """Run all tests"""
    print("🚀 Bulgarian Legal Search System - Function Tests")
    print("=" * 60)
    
    # Run all tests
    # test_basic_search()
    test_enhanced_legal_search()
    # test_relevancy_scoring()
    # test_streamlit_components()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("\n💡 Next steps:")
    print("   1. Make sure your .env file has real API keys")
    print("   2. Run: streamlit run enhanced_streamlit_legal_app.py")
    print("   3. Open your browser and start searching!")

if __name__ == "__main__":
    main() 