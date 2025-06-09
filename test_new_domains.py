#!/usr/bin/env python3
"""
Test script for new Bulgarian legal domains
Tests the integration of Апис, Лакорда, and Сиела Нет domains
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_domain_configuration():
    """Test that the new domains are properly configured"""
    print("🔍 Testing new Bulgarian legal domains configuration...")
    
    try:
        from bulgarian_legal_domains import BULGARIAN_LEGAL_DOMAINS
        
        # Check if new domains are present
        expected_domains = ['apis_bg', 'lakorda', 'ciela_net']
        
        for domain_key in expected_domains:
            if domain_key in BULGARIAN_LEGAL_DOMAINS:
                domain_info = BULGARIAN_LEGAL_DOMAINS[domain_key]
                print(f"✅ {domain_key}: {domain_info['description']}")
                print(f"   - Domain: {domain_info['domain']}")
                print(f"   - Focus areas: {', '.join(domain_info['focus_areas'])}")
            else:
                print(f"❌ Missing domain: {domain_key}")
        
        print(f"\n📊 Total domains configured: {len(BULGARIAN_LEGAL_DOMAINS)}")
        
    except ImportError as e:
        print(f"❌ Error importing domain configuration: {e}")

def test_tools_integration():
    """Test that the tools can access the new domains"""
    print("\n🛠️ Testing tools integration...")
    
    try:
        from tools import google_domain_search
        from enhanced_legal_tools import bulgarian_legal_search
        
        print("✅ Tools imported successfully")
        
        # Test a simple search (without actual execution to avoid API calls)
        test_query = "правни консултации"
        print(f"🧪 Test query prepared: '{test_query}'")
        print("✅ Tools ready for testing")
        
    except ImportError as e:
        print(f"❌ Error importing tools: {e}")

def test_streamlit_app_domains():
    """Test that the Streamlit app includes the new domains"""
    print("\n🖥️ Testing Streamlit app domain options...")
    
    try:
        # Read the enhanced streamlit app file to check domain options
        with open('enhanced_streamlit_legal_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'ciela_net' in content and 'apis_bg' in content and 'lakorda' in content:
            print("✅ New domains found in Streamlit app configuration")
            print("   - Ciela Net: Сиела Нет ✅")
            print("   - Apis BG: Апис ✅") 
            print("   - Lakorda: Лакорда ✅")
        else:
            print("❌ Some domains missing from Streamlit app")
            
    except Exception as e:
        print(f"❌ Error checking Streamlit app: {e}")

def display_domain_info():
    """Display information about each new domain"""
    print("\n📋 New Bulgarian Legal Domains Information:")
    print("=" * 60)
    
    domains_info = [
        {
            "name": "Апис (Apis)",
            "url": "https://www.apis.bg/bg/",
            "description": "Bulgarian legal information and publishing platform",
            "focus": "Legal information, juridical services, legal consultations"
        },
        {
            "name": "Лакорда (Lakorda)", 
            "url": "https://web.lakorda.com/lakorda/?news=1",
            "description": "Legal news and information portal",
            "focus": "Legal news, current information, legal analyses"
        },
        {
            "name": "Сиела Нет (Ciela Net)",
            "url": "https://www.ciela.net/",
            "description": "Legal software and reference systems",
            "focus": "Legal information systems, Bulgarian legislation, legal literature"
        }
    ]
    
    for i, domain in enumerate(domains_info, 1):
        print(f"{i}. {domain['name']}")
        print(f"   🌐 URL: {domain['url']}")
        print(f"   📝 Description: {domain['description']}")
        print(f"   🎯 Focus: {domain['focus']}")
        print()

def main():
    """Run all tests"""
    print("🇧🇬 Testing Enhanced Bulgarian Legal System - New Domains")
    print("=" * 70)
    
    display_domain_info()
    test_domain_configuration()
    test_tools_integration() 
    test_streamlit_app_domains()
    
    print("\n🎉 Domain integration test completed!")
    print("\nℹ️  To test the actual search functionality:")
    print("   python3 -m streamlit run enhanced_streamlit_legal_app.py")

if __name__ == "__main__":
    main() 