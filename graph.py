import json
import time
import logging
from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

# Import the agents and tools
from agents import (
    supervisor_node,
    bulgarian_legal_searcher_node,
    legal_document_analyzer_node,
    legal_citation_specialist_node,
    get_tools
)

# Setup logging
logger = logging.getLogger(__name__)

class BulgarianLegalState(TypedDict):
    """State for Bulgarian legal research workflow"""
    query: str
    search_results: str
    analysis_results: str
    final_answer: str
    next_agent: str
    iteration_count: int
    max_iterations: int
    metadata: Dict[str, Any]

def create_bulgarian_legal_workflow() -> StateGraph:
    """
    Create a simplified and robust Bulgarian legal research workflow.
    This workflow ensures proper routing between agents.
    """
    logger.info("🔧 Creating Bulgarian Legal Research Workflow")
    
    # Initialize the state graph
    workflow = StateGraph(BulgarianLegalState)
    
    # Add nodes for each agent
    workflow.add_node("supervisor", supervisor_wrapper)
    workflow.add_node("Bulgarian_Legal_Searcher", searcher_wrapper)
    workflow.add_node("Legal_Document_Analyzer", analyzer_wrapper)
    workflow.add_node("Legal_Citation_Specialist", citation_wrapper)
    
    # Define the workflow flow
    workflow.set_entry_point("supervisor")
    
    # Supervisor decides next action
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "Bulgarian_Legal_Searcher": "Bulgarian_Legal_Searcher",
            "Legal_Document_Analyzer": "Legal_Document_Analyzer", 
            "Legal_Citation_Specialist": "Legal_Citation_Specialist",
            "FINISH": END
        }
    )
    
    # Each agent returns to supervisor for routing decision
    workflow.add_edge("Bulgarian_Legal_Searcher", "supervisor")
    workflow.add_edge("Legal_Document_Analyzer", "supervisor")
    workflow.add_edge("Legal_Citation_Specialist", "supervisor")
    
    return workflow.compile()

def supervisor_wrapper(state: BulgarianLegalState) -> BulgarianLegalState:
    """Wrapper for supervisor with proper state management"""
    try:
        logger.info(f"🎯 Supervisor processing - Iteration {state.get('iteration_count', 0)}")
        
        # Check iteration limit
        iteration_count = state.get('iteration_count', 0) + 1
        max_iterations = state.get('max_iterations', 5)
        
        if iteration_count > max_iterations:
            logger.info("🏁 Reached maximum iterations, finishing workflow")
            return {
                **state,
                "next_agent": "FINISH",
                "iteration_count": iteration_count,
                "final_answer": state.get('analysis_results', state.get('search_results', 'No results found'))
            }
        
        # Prepare context for supervisor
        context = f"""
Query: {state['query']}
Search Results: {state.get('search_results', 'None yet')}
Analysis Results: {state.get('analysis_results', 'None yet')}
Iteration: {iteration_count}/{max_iterations}
        """
        
        # Get supervisor decision
        result = supervisor_node.invoke({"messages": [HumanMessage(content=context)]})
        
        # Extract next agent from supervisor response
        next_agent = extract_next_agent(result)
        
        logger.info(f"🎯 Supervisor decided: {next_agent}")
        
        return {
            **state,
            "next_agent": next_agent,
            "iteration_count": iteration_count,
            "metadata": {**state.get('metadata', {}), "supervisor_decision": next_agent}
        }
        
    except Exception as e:
        logger.error(f"Supervisor error: {e}")
        return {
            **state,
            "next_agent": "FINISH",
            "final_answer": f"Error in supervisor: {e}"
        }

def searcher_wrapper(state: BulgarianLegalState) -> BulgarianLegalState:
    """Wrapper for Bulgarian Legal Searcher"""
    try:
        logger.info("🔍 Bulgarian Legal Searcher executing")
        
        # Execute search
        search_context = {"messages": [HumanMessage(content=f"Търсене на информация за: {state['query']}")]}
        result = bulgarian_legal_searcher_node(search_context)
        
        # Extract content from result
        search_results = extract_content_from_result(result)
        
        logger.info(f"🔍 Search completed - {len(search_results)} characters of results")
        
        return {
            **state,
            "search_results": search_results,
            "metadata": {**state.get('metadata', {}), "search_completed": True}
        }
        
    except Exception as e:
        logger.error(f"Searcher error: {e}")
        return {
            **state,
            "search_results": f"Search error: {e}",
            "metadata": {**state.get('metadata', {}), "search_error": str(e)}
        }

def analyzer_wrapper(state: BulgarianLegalState) -> BulgarianLegalState:
    """Wrapper for Legal Document Analyzer"""
    try:
        logger.info("📖 Legal Document Analyzer executing")
        
        search_results = state.get('search_results', '')
        if not search_results or 'error' in search_results.lower():
            logger.warning("No valid search results to analyze")
            return {
                **state,
                "analysis_results": "Няма валидни резултати за анализ.",
                "metadata": {**state.get('metadata', {}), "analysis_skipped": True}
            }
        
        # Prepare analysis context
        analysis_context = f"""
Запитване: {state['query']}
Резултати от търсенето:
{search_results}

Моля, направете задълбочен анализ на правните аспекти.
        """
        
        result = legal_document_analyzer_node({
            "messages": [HumanMessage(content=analysis_context)]
        })
        
        analysis_results = extract_content_from_result(result)
        
        logger.info(f"📖 Analysis completed - {len(analysis_results)} characters")
        
        return {
            **state,
            "analysis_results": analysis_results,
            "metadata": {**state.get('metadata', {}), "analysis_completed": True}
        }
        
    except Exception as e:
        logger.error(f"Analyzer error: {e}")
        return {
            **state,
            "analysis_results": f"Analysis error: {e}",
            "metadata": {**state.get('metadata', {}), "analysis_error": str(e)}
        }

def citation_wrapper(state: BulgarianLegalState) -> BulgarianLegalState:
    """Wrapper for Legal Citation Specialist"""
    try:
        logger.info("📚 Legal Citation Specialist executing")
        
        # Prepare citation context
        citation_context = f"""
Запитване: {state['query']}
Резултати от търсенето: {state.get('search_results', '')}
Анализ: {state.get('analysis_results', '')}

Моля, финализирайте отговора с правилни цитати и препоръки.
        """
        
        result = legal_citation_specialist_node({
            "messages": [HumanMessage(content=citation_context)]
        })
        
        final_answer = extract_content_from_result(result)
        
        logger.info(f"📚 Citation work completed - {len(final_answer)} characters")
        
        return {
            **state,
            "final_answer": final_answer,
            "metadata": {**state.get('metadata', {}), "citation_completed": True}
        }
        
    except Exception as e:
        logger.error(f"Citation specialist error: {e}")
        return {
            **state,
            "final_answer": f"Citation error: {e}",
            "metadata": {**state.get('metadata', {}), "citation_error": str(e)}
        }

def route_supervisor(state: BulgarianLegalState) -> str:
    """
    Route based on supervisor's decision and current state.
    """
    try:
        next_agent = state.get('next_agent', '')
        
        # Log routing decision
        logger.info(f"🔀 Routing to: {next_agent}")
        
        # Validate routing decision
        valid_agents = ["Bulgarian_Legal_Searcher", "Legal_Document_Analyzer", "Legal_Citation_Specialist", "FINISH"]
        
        if next_agent not in valid_agents:
            logger.warning(f"Invalid next_agent: {next_agent}, defaulting based on state")
            
            # Default routing logic based on current state
            if not state.get('search_results'):
                return "Bulgarian_Legal_Searcher"
            elif not state.get('analysis_results'):
                return "Legal_Document_Analyzer"
            elif not state.get('final_answer'):
                return "Legal_Citation_Specialist"
            else:
                return "FINISH"
        
        return next_agent
        
    except Exception as e:
        logger.error(f"Routing error: {e}")
        return "FINISH"

def extract_next_agent(result) -> str:
    """
    Extract next agent from supervisor result with robust parsing.
    """
    try:
        # Handle different result formats
        if hasattr(result, 'content'):
            content = result.content
        elif isinstance(result, dict):
            content = result.get('content', str(result))
        elif isinstance(result, str):
            content = result
        else:
            content = str(result)
        
        content_lower = content.lower()
        
        # Look for agent names in the response
        if 'bulgarian_legal_searcher' in content_lower or 'търсене' in content_lower:
            return "Bulgarian_Legal_Searcher"
        elif 'legal_document_analyzer' in content_lower or 'анализ' in content_lower:
            return "Legal_Document_Analyzer"
        elif 'legal_citation_specialist' in content_lower or 'цитати' in content_lower or 'finish' in content_lower:
            return "Legal_Citation_Specialist"
        elif 'finish' in content_lower or 'готово' in content_lower:
            return "FINISH"
        else:
            logger.warning(f"Could not extract clear next agent from: {content[:100]}...")
            return "Bulgarian_Legal_Searcher"  # Default to search if unclear
            
    except Exception as e:
        logger.error(f"Error extracting next agent: {e}")
        return "Bulgarian_Legal_Searcher"

def extract_content_from_result(result) -> str:
    """
    Extract content from agent result with robust handling.
    """
    try:
        if hasattr(result, 'content'):
            return result.content
        elif isinstance(result, dict):
            # Handle dict with messages list (LangChain agent response format)
            if 'messages' in result and result['messages']:
                last_message = result['messages'][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                return str(last_message)
            return result.get('content', result.get('output', str(result)))
        elif isinstance(result, str):
            return result
        else:
            return str(result)
    except Exception as e:
        logger.error(f"Error extracting content: {e}")
        return f"Error extracting content: {e}"

def run_graph(query: str) -> str:
    """
    Execute the Bulgarian legal research workflow.
    """
    logger.info(f"🚀 Starting Bulgarian Legal Research for: '{query}'")
    
    try:
        # Create the workflow
        workflow = create_bulgarian_legal_workflow()
        
        # Initialize state
        initial_state = {
            "query": query,
            "search_results": "",
            "analysis_results": "",
            "final_answer": "",
            "next_agent": "",
            "iteration_count": 0,
            "max_iterations": 5,
            "metadata": {"start_time": time.time()}
        }
        
        # Execute the workflow
        result = workflow.invoke(initial_state)
        
        # Extract final answer
        final_answer = result.get('final_answer', '')
        if not final_answer:
            final_answer = result.get('analysis_results', result.get('search_results', 'Не бяха намерени резултати.'))
        
        # Log completion
        duration = time.time() - result.get('metadata', {}).get('start_time', time.time())
        logger.info(f"✅ Workflow completed in {duration:.1f} seconds")
        logger.info(f"📊 Final result: {len(final_answer)} characters")
        
        return final_answer
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        return f"⚠️ Възникна грешка при обработката на заявката: {e}"

def run_enhanced_legal_research_workflow(query: str) -> str:
    """
    Enhanced version of the workflow with better error handling and state management.
    """
    return run_graph(query)

def run_graph_with_streaming(query: str, progress_callback=None, config=None):
    """
    Enhanced version with streaming simulation for Streamlit compatibility.
    """
    logger.info(f"🔄 Starting streaming workflow for: '{query}'")
    
    if progress_callback:
        progress_callback("🔍 Initializing Bulgarian legal search...", 0.2)
        time.sleep(0.5)
        progress_callback("📊 Processing with BM25 + Semantic analysis...", 0.5)
        time.sleep(0.5)
        progress_callback("🎯 Ranking and scoring results...", 0.8)
        time.sleep(0.5)
        progress_callback("✅ Finalizing comprehensive analysis...", 1.0)
    
    return run_graph(query)

def visualize_graph():
    """
    Generate basic graph visualization information.
    """
    mermaid_syntax = """
    graph TD
        A[User Query] --> B[Supervisor]
        B --> C[Bulgarian Legal Searcher]
        B --> D[Legal Document Analyzer]
        B --> E[Legal Citation Specialist]
        C --> B
        D --> B
        E --> B
        B --> F[Final Result]
    """
    return mermaid_syntax

def get_graph_info():
    """
    Get information about the Bulgarian legal graph structure.
    """
    return {
        "nodes": ["supervisor", "Bulgarian_Legal_Searcher", "Legal_Document_Analyzer", "Legal_Citation_Specialist"],
        "edges": [
            ("supervisor", "Bulgarian_Legal_Searcher"),
            ("supervisor", "Legal_Document_Analyzer"),
            ("supervisor", "Legal_Citation_Specialist"),
            ("Bulgarian_Legal_Searcher", "supervisor"),
            ("Legal_Document_Analyzer", "supervisor"),
            ("Legal_Citation_Specialist", "supervisor")
        ],
        "entry_point": "supervisor",
        "specialized_agents": [
            "Bulgarian_Legal_Searcher - Expert Bulgarian legal search",
            "Legal_Document_Analyzer - Document analysis specialist", 
            "Legal_Citation_Specialist - Citation and formatting expert"
        ],
        "supported_domains": ["ciela.net", "apis.bg", "lakorda.com"],
        "legal_areas": ["Civil Law", "Criminal Law", "Administrative Law", "Commercial Law", "Labor Law"],
        "tools_available": [
            "enhanced_bulgarian_legal_search_tool - Enhanced legal search",
            "bulgarian_legal_search - Multi-domain legal search",
            "legal_precedent_search - Court precedent search",
            "legal_citation_extractor - Citation extraction"
        ]
    }

def get_config_options():
    """
    Get available configuration options for the legal research system.
    """
    return {
        "query_depth": {
            "shallow": "Shallow search - quick results",
            "medium": "Medium depth - balanced search", 
            "deep": "Deep search - comprehensive analysis"
        },
        "complexity_level": {
            "basic": "Basic level - simple explanations",
            "standard": "Standard level - detailed analysis",
            "expert": "Expert level - technical content"
        },
        "max_iterations": {
            1: "Quick search (1 iteration)",
            2: "Standard search (2 iterations)", 
            3: "In-depth search (3 iterations)",
            4: "Comprehensive search (4 iterations)",
            5: "Maximum depth search (5 iterations)"
        },
        "context_window": {
            2000: "Small context (2K words)",
            5000: "Medium context (5K words)",
            8000: "Large context (8K words)",
            10000: "Maximum context (10K words)"
        }
    }

def format_top_sources(sources, limit=5):
    """
    Format top sources with metadata for the response.
    """
    if not sources or not isinstance(sources, list):
        return "📚 **TOP 5 MOST RELEVANT SOURCES**\n\nNo sources available.\n\n"
    
    formatted = "📚 **TOP 5 MOST RELEVANT SOURCES**\n\n"
    
    for i, source in enumerate(sources[:limit], 1):
        if isinstance(source, dict):
            title = source.get('title', 'No Title')
            href = source.get('href', source.get('url', '#'))
            body = source.get('body', source.get('snippet', ''))
            domain = source.get('source_domain', 'Unknown source')
            
            # Extract key information for metadata  
            snippet = body[:80] + "..." if len(body) > 80 else body
            
            formatted += f"**{i}. [{title}]({href})**\n"
            formatted += f"   🏛️ *{domain}*\n" 
            formatted += f"   📄 {snippet}\n\n"
    
    formatted += "---\n\n"
    return formatted

def bulgarian_legal_research(query: str, config=None):
    """
    Compatibility function for enhanced Streamlit app.
    """
    return run_graph(query)

# Export the main function
__all__ = [
    'run_graph', 
    'run_enhanced_legal_research_workflow', 
    'create_bulgarian_legal_workflow',
    'run_graph_with_streaming',
    'visualize_graph',
    'get_graph_info',
    'get_config_options',
    'format_top_sources',
    'bulgarian_legal_research'
]
