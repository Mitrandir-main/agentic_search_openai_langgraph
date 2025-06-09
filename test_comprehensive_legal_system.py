#!/usr/bin/env python3
"""
Comprehensive Testing Framework for Bulgarian Legal Research System
"""

import asyncio
import logging
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestResult:
    def __init__(self, query: str, response: str, issues: List[str], score: float):
        self.query = query
        self.response = response
        self.issues = issues
        self.score = score

class LegalSystemTester:
    """Comprehensive tester for the Bulgarian legal research system"""
    
    def __init__(self):
        self.test_queries = [
            "обезщетение за счупване на ръка",
            "какви са правата ми при уволнение",
            "как да предявя иск в съда",
            "наследство без завещание",
            "глоба за превишена скорост"
        ]
    
    async def test_query(self, query: str) -> TestResult:
        """Test a single query and analyze response quality"""
        
        logger.info(f"🧪 Testing: {query}")
        
        try:
            # Import and run the search
            from enhanced_legal_tools import enhanced_bulgarian_legal_search_sync
            
            start_time = time.time()
            response = enhanced_bulgarian_legal_search_sync(query, max_results=15, min_relevancy=0.1)
            response_time = time.time() - start_time
            
            # Analyze response quality
            issues = self.analyze_response_quality(response, query)
            score = self.calculate_quality_score(response, issues)
            
            logger.info(f"✅ Completed in {response_time:.1f}s - Score: {score:.1f}/10")
            
            return TestResult(query, response, issues, score)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return TestResult(query, f"Error: {e}", [f"System error: {e}"], 0.0)
    
    def analyze_response_quality(self, response: str, query: str) -> List[str]:
        """Analyze response quality and identify issues"""
        
        issues = []
        response_lower = response.lower()
        
        # Check response length
        if len(response) < 500:
            issues.append(f"Response too short: {len(response)} characters")
        
        # Check for generic/template responses
        generic_phrases = [
            "консултирайте се с юрист",
            "приложими са общите норми",
            "за процедурата:",
            "проверете актуалността"
        ]
        
        generic_count = sum(1 for phrase in generic_phrases if phrase in response_lower)
        if generic_count >= 3:
            issues.append("Response appears to be mostly generic template text")
        
        # Check for specific legal information
        if query == "обезщетение за счупване на ръка":
            expected_elements = ["ззд", "чл.", "гражданска отговорност", "компенсация", "размер"]
            missing_elements = [elem for elem in expected_elements if elem not in response_lower]
            if len(missing_elements) > 2:
                issues.append(f"Missing key legal elements: {missing_elements}")
        
        # Check for practical information
        practical_indicators = ["стъпки", "документи", "срок", "процедура", "размер", "лв"]
        practical_found = sum(1 for indicator in practical_indicators if indicator in response_lower)
        if practical_found < 2:
            issues.append("Lacks practical, actionable information")
        
        # Check for Bulgarian legal context
        bulgarian_indicators = ["български", "българия", "чл.", "закон", "кодекс"]
        bulgarian_found = sum(1 for indicator in bulgarian_indicators if indicator in response_lower)
        if bulgarian_found < 2:
            issues.append("Insufficient Bulgarian legal context")
        
        return issues
    
    def calculate_quality_score(self, response: str, issues: List[str]) -> float:
        """Calculate overall quality score (0-10)"""
        
        base_score = 10.0
        
        # Deduct points for issues
        for issue in issues:
            if "too short" in issue:
                base_score -= 3.0
            elif "generic template" in issue:
                base_score -= 4.0
            elif "missing key legal elements" in issue:
                base_score -= 3.0
            elif "lacks practical" in issue:
                base_score -= 2.0
            elif "insufficient bulgarian" in issue:
                base_score -= 2.0
            else:
                base_score -= 1.0
        
        # Bonus points for good content
        response_lower = response.lower()
        
        if "чл." in response_lower and any(law in response_lower for law in ["ззд", "кодекс", "закон"]):
            base_score += 1.0
        
        if len(response) > 1000:
            base_score += 1.0
        
        return max(0.0, min(10.0, base_score))
    
    async def run_full_test(self) -> Dict[str, Any]:
        """Run full test suite and generate report"""
        
        logger.info("🚀 Starting Comprehensive Legal System Test")
        
        results = []
        for query in self.test_queries:
            result = await self.test_query(query)
            results.append(result)
            await asyncio.sleep(1)  # Brief pause between tests
        
        # Generate report
        total_score = sum(r.score for r in results)
        average_score = total_score / len(results)
        
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        # Count issue types
        issue_summary = {}
        for issue in all_issues:
            issue_type = issue.split(":")[0]
            issue_summary[issue_type] = issue_summary.get(issue_type, 0) + 1
        
        report = {
            "summary": {
                "total_tests": len(results),
                "average_score": round(average_score, 2),
                "total_issues": len(all_issues),
                "passing_tests": sum(1 for r in results if r.score >= 7.0)
            },
            "issue_summary": issue_summary,
            "detailed_results": [
                {
                    "query": r.query,
                    "score": r.score,
                    "issues": r.issues,
                    "response_length": len(r.response)
                }
                for r in results
            ],
            "recommendations": self.generate_recommendations(results)
        }
        
        # Print summary
        print("\n" + "="*80)
        print("🔬 COMPREHENSIVE TEST RESULTS")
        print("="*80)
        print(f"📊 Average Score: {average_score:.1f}/10")
        print(f"✅ Passing Tests: {report['summary']['passing_tests']}/{len(results)}")
        print(f"⚠️  Total Issues: {len(all_issues)}")
        
        print("\n🔍 TOP ISSUES:")
        for issue_type, count in sorted(issue_summary.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {issue_type}: {count} occurrences")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations'][:3]:
            print(f"   • {rec}")
        
        return report
    
    def generate_recommendations(self, results: List[TestResult]) -> List[str]:
        """Generate improvement recommendations based on test results"""
        
        recommendations = []
        
        # Analyze common issues
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        if any("generic template" in issue for issue in all_issues):
            recommendations.append("CRITICAL: Replace generic template responses with actual content analysis")
        
        if any("too short" in issue for issue in all_issues):
            recommendations.append("HIGH: Increase response depth by analyzing more extracted content")
        
        if any("missing key legal elements" in issue for issue in all_issues):
            recommendations.append("HIGH: Improve content extraction to find relevant legal information")
        
        if any("lacks practical" in issue for issue in all_issues):
            recommendations.append("MEDIUM: Add more practical guidance and actionable steps")
        
        low_scoring = [r for r in results if r.score < 5.0]
        if low_scoring:
            recommendations.append(f"CRITICAL: {len(low_scoring)} tests failed completely - major system issues")
        
        return recommendations

# Main test function
async def run_test():
    """Run the comprehensive test"""
    tester = LegalSystemTester()
    report = await tester.run_full_test()
    return report

if __name__ == "__main__":
    asyncio.run(run_test()) 