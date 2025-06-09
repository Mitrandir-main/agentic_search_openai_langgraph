#!/usr/bin/env python3
"""
Test script for Google Custom Search Engine integration
This script verifies the Google CSE setup and fallback mechanisms.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_keys():
    """Test if API keys are properly configured."""
    print("🔑 Testing API Key Configuration")
    print("=" * 50)
    
    # Check Google CSE configuration
    google_api_key = os.getenv('GOOGLE_CSE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')
    
    if google_api_key:
        print(f"✅ Google CSE API Key: {'*' * 10}{google_api_key[-6:] if len(google_api_key) > 6 else 'INVALID'}")
    else:
        print("❌ Google CSE API Key: NOT SET")
    
    if google_cse_id:
        print(f"✅ Google CSE ID: {google_cse_id[:15]}...{google_cse_id[-6:] if len(google_cse_id) > 21 else google_cse_id}")
    else:
        print("❌ Google CSE ID: NOT SET")
    
    # Check other API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')
    
    if openai_key:
        print(f"✅ OpenAI API Key: {'*' * 10}{openai_key[-6:] if len(openai_key) > 6 else 'INVALID'}")
    else:
        print("❌ OpenAI API Key: NOT SET")
        
    if tavily_key:
        print(f"✅ Tavily API Key: {'*' * 10}{tavily_key[-6:] if len(tavily_key) > 6 else 'INVALID'}")
    else:
        print("⚠️  Tavily API Key: NOT SET (optional fallback)")
    
    print("\n")
    return bool(google_api_key and google_cse_id)

def test_google_cse_direct():
    """Test Google CSE directly using the API."""
    print("🔍 Testing Google CSE Direct API")
    print("=" * 50)
    
    try:
        import requests
        
        api_key = os.getenv('GOOGLE_CSE_API_KEY')
        cse_id = os.getenv('GOOGLE_CSE_ID')
        
        if not api_key or not cse_id:
            print("❌ Google CSE not configured - skipping direct API test")
            return False
        
        # Test simple search
        test_query = "българско право"
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': test_query,
            'num': 3,
            'gl': 'bg',
            'lr': 'lang_bg'
        }
        
        print(f"Testing query: '{test_query}'")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            total_results = data.get('searchInformation', {}).get('totalResults', '0')
            
            print(f"✅ Google CSE API working!")
            print(f"   Total results: {total_results}")
            print(f"   Returned items: {len(items)}")
            
            for i, item in enumerate(items[:2], 1):
                print(f"   {i}. {item.get('title', 'No Title')[:60]}...")
                
            return True
        else:
            print(f"❌ Google CSE API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Google CSE API: {e}")
        return False

def test_enhanced_legal_tools():
    """Test the enhanced legal tools with Google CSE integration."""
    print("⚖️  Testing Enhanced Legal Tools")
    print("=" * 50)
    
    try:
        # Import the enhanced legal tools
        from enhanced_legal_tools import (
            bulgarian_legal_search,
            legal_precedent_search,
            legal_citation_extractor,
            legal_area_classifier
        )
        
        # Test 1: Bulgarian legal search
        print("Test 1: Bulgarian Legal Search")
        test_query = "обезщетение за телесна повреда"
        print(f"Query: '{test_query}'")
        
        results = bulgarian_legal_search(test_query)
        if isinstance(results, list) and len(results) > 0:
            print(f"✅ Found {len(results)} results")
            
            # Show first result
            first_result = results[0]
            if isinstance(first_result, dict) and 'title' in first_result:
                print(f"   First result: {first_result.get('title', 'No Title')[:60]}...")
                print(f"   Domain: {first_result.get('source_domain', 'Unknown')}")
            else:
                print(f"   Results format: {type(first_result)}")
        else:
            print(f"⚠️  No results or error: {results}")
        
        print()
        
        # Test 2: Legal area classifier
        print("Test 2: Legal Area Classifier")
        classification = legal_area_classifier(test_query)
        if isinstance(classification, dict):
            print(f"✅ Classification successful")
            print(f"   Legal area: {classification.get('legal_area', 'Unknown')}")
            print(f"   Bulgarian name: {classification.get('bulgarian_name', 'Unknown')}")
            print(f"   Confidence: {classification.get('confidence', 0)}")
        else:
            print(f"⚠️  Classification failed: {classification}")
        
        print()
        
        # Test 3: Citation extractor
        print("Test 3: Citation Extractor")
        test_text = "Съгласно чл. 45 ал. 2 от Закона за здравното осигуряване и решение № 123 от ВКС."
        citations = legal_citation_extractor(test_text)
        if isinstance(citations, dict) and citations.get('total_found', 0) > 0:
            print(f"✅ Found {citations['total_found']} citations")
            print(f"   Citations: {citations.get('extracted_citations', [])}")
        else:
            print(f"⚠️  No citations found: {citations}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure enhanced_legal_tools.py is available")
        return False
    except Exception as e:
        print(f"❌ Error testing legal tools: {e}")
        return False

def test_fallback_mechanisms():
    """Test fallback from Google CSE to DuckDuckGo."""
    print("🔄 Testing Fallback Mechanisms")
    print("=" * 50)
    
    try:
        from enhanced_legal_tools import fallback_ddg_search
        
        print("Testing DuckDuckGo fallback search...")
        test_query = "българско право"
        
        results = fallback_ddg_search(test_query)
        if isinstance(results, list) and len(results) > 0:
            print(f"✅ DuckDuckGo fallback working - {len(results)} results")
            
            first_result = results[0]
            if isinstance(first_result, dict):
                print(f"   First result: {first_result.get('title', 'No Title')[:60]}...")
        else:
            print(f"⚠️  DuckDuckGo fallback failed or rate limited: {results}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing fallback: {e}")
        return False

def create_sample_env_file():
    """Create a sample .env file if it doesn't exist."""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print("📝 Creating sample .env file...")
        
        sample_env = """# API Configuration for Bulgarian Legal Research System

# OpenAI API Key (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Google Custom Search Engine (Recommended for better search results)
GOOGLE_CSE_API_KEY=your_google_cse_api_key_here  
GOOGLE_CSE_ID=your_google_cse_id_here

# Tavily API Key (Optional fallback)
TAVILY_API_KEY=your_tavily_api_key_here

# LangSmith (Optional - for debugging and monitoring)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(sample_env)
        
        print(f"✅ Created {env_file} - please add your API keys")
        return True
    
    return False

def main():
    """Run all tests."""
    print("🚀 Bulgarian Legal Research System - Google CSE Integration Test")
    print("=" * 70)
    print()
    
    # Create sample .env if needed
    if create_sample_env_file():
        print("⚠️  Please configure your API keys in .env file and run the test again.\n")
        return
    
    # Test API keys
    keys_ok = test_api_keys()
    
    # Test Google CSE direct API
    if keys_ok:
        cse_ok = test_google_cse_direct()
        print()
    else:
        cse_ok = False
        print("⚠️  Skipping Google CSE direct test - keys not configured\n")
    
    # Test enhanced legal tools
    tools_ok = test_enhanced_legal_tools()
    print()
    
    # Test fallback mechanisms
    fallback_ok = test_fallback_mechanisms()
    print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 50)
    print(f"API Keys: {'✅ Configured' if keys_ok else '❌ Missing'}")
    print(f"Google CSE: {'✅ Working' if cse_ok else '❌ Failed' if keys_ok else '⚠️ Not tested'}")
    print(f"Legal Tools: {'✅ Working' if tools_ok else '❌ Failed'}")
    print(f"Fallback: {'✅ Working' if fallback_ok else '❌ Failed'}")
    
    if cse_ok or fallback_ok:
        print("\n🎉 System is ready for Bulgarian legal research!")
        if not cse_ok:
            print("   Note: Using DuckDuckGo fallback (may have rate limits)")
    else:
        print("\n⚠️  System has issues - check API configuration")
    
    print("\nFor setup instructions, see: GOOGLE_CSE_SETUP.md")

if __name__ == "__main__":
    main() 