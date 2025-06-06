import json
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from advanced_legal_agents import (
    LegalAgentState,
    create_legal_supervisor,
    create_legal_researcher_agent,
    create_legal_analyst_agent,
    create_precedent_finder_agent,
    create_document_reviewer_agent,
    create_legal_conciliator_agent,
    get_legal_members,
    determine_legal_workflow,
    create_legal_memory_manager
)
from bulgarian_legal_domains import BULGARIAN_LEGAL_DOMAINS
from datetime import datetime
import logging

# Set up logging for legal research tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_enhanced_legal_graph():
    """Build enhanced legal research graph with Conciliator pattern"""
    
    # Create all agents
    supervisor_chain = create_legal_supervisor()
    legal_researcher_node = create_legal_researcher_agent()
    legal_analyst_node = create_legal_analyst_agent()
    precedent_finder_node = create_precedent_finder_agent()
    document_reviewer_node = create_document_reviewer_agent()
    legal_conciliator_node = create_legal_conciliator_agent()
    
    # Build the graph
    graph_builder = StateGraph(LegalAgentState)
    
    # Add all nodes
    graph_builder.add_node("Legal_Supervisor", supervisor_chain)
    graph_builder.add_node("Legal_Researcher", legal_researcher_node)
    graph_builder.add_node("Legal_Analyst", legal_analyst_node)
    graph_builder.add_node("Precedent_Finder", precedent_finder_node)
    graph_builder.add_node("Document_Reviewer", document_reviewer_node)
    graph_builder.add_node("Legal_Conciliator", legal_conciliator_node)
    
    # Set up edges for agent collaboration
    members = get_legal_members()
    for member in members:
        graph_builder.add_edge(member, "Legal_Supervisor")
    
    # Conditional map for routing
    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END
    conditional_map["CONCILIATE"] = "Legal_Conciliator"
    
    # Enhanced routing function with Conciliator pattern
    def route_legal_supervisor(x):
        """Enhanced routing with conflict detection and conciliation"""
        try:
            if isinstance(x, dict):
                if "args" in x:
                    next_action = x["args"].get("next", "FINISH")
                elif "next" in x:
                    next_action = x["next"]
                else:
                    next_action = "FINISH"
            else:
                next_action = "FINISH"
            
            # Check if we need conciliation (multiple conflicting results)
            if hasattr(x, 'get') and x.get('iterations', 0) >= 3:
                # If we've had multiple iterations, consider conciliation
                messages = x.get('messages', [])
                if len(messages) >= 4:  # Multiple agent responses
                    logger.info("Multiple iterations detected, considering conciliation")
                    return "Legal_Conciliator"
            
            logger.info(f"Routing to: {next_action}")
            return next_action
            
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return END
    
    # Add conditional edges with enhanced routing
    graph_builder.add_conditional_edges(
        "Legal_Supervisor", 
        route_legal_supervisor, 
        conditional_map
    )
    
    # Add edge from Conciliator back to supervisor or end
    graph_builder.add_edge("Legal_Conciliator", END)
    
    # Set entry point
    graph_builder.set_entry_point("Legal_Supervisor")
    
    # Compile the graph
    graph = graph_builder.compile()
    
    return graph

def visualize_legal_graph():
    """Generate visualization for the legal research graph"""
    graph = build_enhanced_legal_graph()
    
    try:
        # Try to create PNG visualization
        png_data = graph.get_graph().draw_mermaid_png()
        with open("legal_graph_visualization.png", "wb") as f:
            f.write(png_data)
        print("✅ Legal graph visualization saved as 'legal_graph_visualization.png'")
        
        # Create Mermaid text format
        mermaid_syntax = graph.get_graph().draw_mermaid()
        with open("legal_graph_visualization.md", "w") as f:
            f.write("# 🏛️ Enhanced Bulgarian Legal Research Graph\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_syntax)
            f.write("\n```\n\n")
            f.write("## 📋 Agent Descriptions\n\n")
            f.write("- **Legal_Supervisor**: Orchestrates legal research workflow\n")
            f.write("- **Legal_Researcher**: Searches Bulgarian legal domains (lex.bg, vks.bg, etc.)\n")
            f.write("- **Legal_Analyst**: Analyzes legal documents and extracts key information\n")
            f.write("- **Precedent_Finder**: Finds relevant court decisions and precedents\n")
            f.write("- **Document_Reviewer**: Reviews documents for citations and legal accuracy\n")
            f.write("- **Legal_Conciliator**: Resolves conflicts between agent findings\n")
            
        print("✅ Legal graph mermaid saved as 'legal_graph_visualization.md'")
        
        return mermaid_syntax
        
    except Exception as e:
        print(f"❌ Could not generate PNG visualization: {e}")
        # Fallback to text representation
        mermaid_syntax = graph.get_graph().draw_mermaid()
        print("📊 Legal Graph Structure:")
        print(mermaid_syntax)
        return mermaid_syntax

def run_legal_research(query: str, workflow_type: str = "auto"):
    """Run enhanced legal research with workflow optimization"""
    
    # Initialize legal memory
    legal_memory = create_legal_memory_manager()
    
    # Determine optimal workflow
    if workflow_type == "auto":
        workflow = determine_legal_workflow(query)
        logger.info(f"Determined workflow: {workflow['type']}")
    else:
        workflow = {"type": workflow_type, "agents": get_legal_members()}
    
    # Enhanced initial state
    initial_state = {
        "messages": [HumanMessage(content=f"""
🏛️ **ПРАВНА ЗАЯВКА**: {query}

**ЗАДАЧА**: Моля, извършете задълбочено правно изследване фокусирано върху:
- Българско законодателство и нормативни актове
- Съдебна практика от ВКС, ВАС и други български съдилища  
- Актуални правни позиции (2024-2025)
- Специализирани правни домейни: {', '.join(BULGARIAN_LEGAL_DOMAINS.keys())}

**ИЗИСКВАНИЯ**:
1. Търсете само в български правни източници
2. Предоставете точни цитати (чл., ал., т.)
3. Анализирайте съдебната практика
4. Оценете правните рискове и последици
5. Дайте практически препоръки

**WORKFLOW**: {workflow['type']}
""")],
        "next": "Legal_Researcher",  # Start with research
        "legal_area": None,
        "confidence": 0.0,
        "sources_checked": [],
        "iterations": 0,
        "max_iterations": 6,
        "final_decision": None,
        "citations": []
    }
    
    # Build and run graph
    graph = build_enhanced_legal_graph()
    
    try:
        logger.info(f"🔍 Starting legal research for: {query}")
        response = graph.invoke(initial_state)
        
        # Process and format results
        result = format_legal_results(response, legal_memory)
        
        logger.info("✅ Legal research completed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error during legal research: {e}")
        return f"❌ Грешка при правното изследване: {str(e)}"

def run_legal_research_with_streaming(query: str):
    """Run legal research with streaming for real-time updates"""
    
    print("🏛️ Започване на правно изследване...\n")
    
    # Track progress
    steps_completed = []
    
    try:
        graph = build_enhanced_legal_graph()
        
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "next": "Legal_Researcher",
            "legal_area": None,
            "confidence": 0.0,
            "sources_checked": [],
            "iterations": 0,
            "max_iterations": 6,
            "final_decision": None,
            "citations": []
        }
        
        # Stream the execution
        for step, event in enumerate(graph.stream(initial_state)):
            for key, value in event.items():
                if key != "__end__":
                    steps_completed.append(key)
                    print(f"📋 **Стъпка {step + 1} - {key}**:")
                    
                    # Extract meaningful information from agent responses
                    if isinstance(value, dict) and 'messages' in value:
                        last_message = value['messages'][-1] if value['messages'] else None
                        if last_message and hasattr(last_message, 'content'):
                            # Truncate long responses for streaming
                            content = last_message.content[:300] + "..." if len(last_message.content) > 300 else last_message.content
                            print(f"   {content}")
                    
                    print("---")
        
        # Get final result
        final_response = graph.invoke(initial_state)
        
        print(f"\n✅ **Завършено**: Обработени {len(steps_completed)} стъпки")
        print(f"📊 **Агенти**: {', '.join(set(steps_completed))}")
        
        return run_legal_research(query)  # Use the regular formatting
        
    except Exception as e:
        print(f"❌ Грешка при streaming изпълнение: {e}")
        return run_legal_research(query)  # Fallback

def format_legal_results(response: dict, legal_memory) -> str:
    """Format legal research results with enhanced structure"""
    
    if not response.get('messages'):
        return "❌ Няма генериран отговор."
    
    # Get all messages for comprehensive analysis
    messages = response['messages']
    
    # Extract content from all agent responses
    agent_responses = {}
    citations_found = set()
    sources_used = set()
    
    for message in messages:
        if hasattr(message, 'name') and hasattr(message, 'content'):
            agent_name = message.name
            content = message.content
            
            agent_responses[agent_name] = content
            
            # Extract citations
            import re
            citations = re.findall(r'чл\.\s*\d+(?:,\s*ал\.\s*\d+)?(?:,\s*т\.\s*\d+)?', content, re.IGNORECASE)
            citations_found.update(citations)
            
            # Extract domain mentions  
            for domain_key, domain_info in BULGARIAN_LEGAL_DOMAINS.items():
                domain_found = False
                
                # Check domain in content
                if domain_info.get('domain', '') in content:
                    domain_found = True
                
                # Check search patterns if they exist
                search_patterns = domain_info.get('search_patterns', [])
                if search_patterns and any(pattern in content for pattern in search_patterns):
                    domain_found = True
                    
                if domain_found:
                    sources_used.add(domain_info.get('description', domain_key))
    
    # Get final response content
    final_content = messages[-1].content if messages else "Няма финален отговор"
    
    # Generate comprehensive report
    result = f"""
# 🏛️ **ПРАВНО ИЗСЛЕДВАНЕ - РЕЗУЛТАТИ**

## 📅 **Метаданни на изследването**
- **Дата на изследване**: {datetime.now().strftime("%d.%m.%Y %H:%M")}
- **Брой агенти**: {len(agent_responses)}
- **Брой съобщения**: {len(messages)}
- **Активни домейни**: {len(sources_used)}

## 📚 **Намерени правни цитати** ({len(citations_found)})
{chr(10).join(f"- {citation}" for citation in sorted(citations_found)) if citations_found else "❌ Няма намерени цитати"}

## 🌐 **Използвани правни източници**
{chr(10).join(f"- {source}" for source in sorted(sources_used)) if sources_used else "❌ Няма специфични домейни"}

## 🎯 **ОСНОВЕН АНАЛИЗ**

{final_content}

## 📋 **Детайлен анализ по агенти**
"""
    
    # Add individual agent contributions
    for agent_name, content in agent_responses.items():
        if agent_name and content:
            result += f"\n### 🤖 **{agent_name}**\n{content[:500]}{'...' if len(content) > 500 else ''}\n"
    
    # Add confidence and coverage metrics
    result += f"""
## 📊 **Качество на изследването**
- **Покритие на домейни**: {len(sources_used)}/{len(BULGARIAN_LEGAL_DOMAINS)}
- **Правни цитати**: {'✅ Добро' if len(citations_found) >= 3 else '⚠️ Ограничено' if len(citations_found) >= 1 else '❌ Без цитати'}
- **Агентна обработка**: {'✅ Комплексна' if len(agent_responses) >= 3 else '⚠️ Ограничена'}

---
*Генерирано от Enhanced Bulgarian Legal Research System*
*Използва специализирани агенти за българското право и съдебна практика*
"""
    
    return result

def get_legal_graph_info():
    """Get comprehensive information about the legal graph structure"""
    graph = build_enhanced_legal_graph()
    graph_dict = graph.get_graph()
    
    info = {
        "nodes": list(graph_dict.nodes.keys()),
        "edges": [(edge.source, edge.target) for edge in graph_dict.edges],
        "entry_point": "Legal_Supervisor",
        "legal_domains": list(BULGARIAN_LEGAL_DOMAINS.keys()),
        "tools_available": [
            "bulgarian_legal_search",
            "legal_document_analyzer", 
            "legal_precedent_search",
            "legal_area_classifier",
            "legal_update_tracker"
        ],
        "specialized_features": [
            "Bulgarian legal domain targeting",
            "Conciliator pattern for conflict resolution",
            "Legal citation extraction",
            "Court precedent analysis",
            "Multi-agent collaboration",
            "Streaming workflow execution"
        ],
        "supported_legal_areas": list(BULGARIAN_LEGAL_AREAS.keys()) if 'BULGARIAN_LEGAL_AREAS' in globals() else []
    }
    
    return info 