#!/usr/bin/env python3
"""
Test Enhanced Legal Graph System
Verifies that the search_patterns error is fixed and the system works properly
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_enhanced_legal_graph():
    """Test the enhanced legal graph system"""
    print("🏛️ Testing Enhanced Legal Graph System")
    print("=" * 60)
    
    try:
        from enhanced_legal_graph import run_legal_research
        
        # Test with a simple legal query
        test_query = "обезщетение за счупване на ръка"
        
        print(f"🔍 Testing query: {test_query}")
        print("📋 Running enhanced legal research...")
        
        result = run_legal_research(test_query)
        
        if result:
            print("✅ Enhanced legal graph system working!")
            print(f"📊 Result length: {len(result)} characters")
            print(f"📝 Preview: {result[:200]}...")
            return True
        else:
            print("❌ No result returned")
            return False
            
    except Exception as e:
        print(f"❌ Error in enhanced legal graph: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_legal_graph()
    
    if success:
        print("\n🎉 All systems working correctly!")
    else:
        print("\n⚠️ Some issues detected") 