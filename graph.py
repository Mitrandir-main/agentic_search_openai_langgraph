import json
import time
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from agents import (
    AgentState, 
    create_supervisor, 
    create_bulgarian_legal_search_agent, 
    create_legal_document_analyzer_agent,
    create_legal_citation_specialist_agent,
    get_members
)

def build_graph():
    supervisor_chain = create_supervisor()
    bulgarian_search_node = create_bulgarian_legal_search_agent()
    document_analyzer_node = create_legal_document_analyzer_agent()
    citation_specialist_node = create_legal_citation_specialist_agent()

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("Supervisor", supervisor_chain)
    graph_builder.add_node("Bulgarian_Legal_Searcher", bulgarian_search_node)
    graph_builder.add_node("Legal_Document_Analyzer", document_analyzer_node)
    graph_builder.add_node("Legal_Citation_Specialist", citation_specialist_node)

    members = get_members()
    for member in members:
        graph_builder.add_edge(member, "Supervisor")

    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END
    
    # Update conditional edges to handle the new tool output format
    def route_supervisor(x):
        if isinstance(x, dict) and "args" in x:
            return x["args"]["next"]
        elif isinstance(x, dict) and "next" in x:
            return x["next"]
        else:
            return END
    
    graph_builder.add_conditional_edges("Supervisor", route_supervisor, conditional_map)
    graph_builder.set_entry_point("Supervisor")

    graph = graph_builder.compile()

    return graph

def visualize_graph():
    """Generate and save graph visualization"""
    graph = build_graph()
    try:
        # Try to create PNG visualization
        png_data = graph.get_graph().draw_mermaid_png()
        with open("graph_visualization.png", "wb") as f:
            f.write(png_data)
        print("Graph visualization saved as 'graph_visualization.png'")
        
        # Also create Mermaid text format
        mermaid_syntax = graph.get_graph().draw_mermaid()
        with open("graph_visualization.md", "w") as f:
            f.write("# Bulgarian Legal Research Agent Graph\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_syntax)
            f.write("\n```")
        print("Mermaid syntax saved as 'graph_visualization.md'")
        
        return mermaid_syntax
        
    except Exception as e:
        print(f"Could not generate PNG visualization: {e}")
        # Fallback to text representation
        mermaid_syntax = graph.get_graph().draw_mermaid()
        print("Mermaid Graph Structure:")
        print(mermaid_syntax)
        return mermaid_syntax

def run_graph(input_message, config=None):
    """Run the Bulgarian legal research graph with optional configuration"""
    graph = build_graph()
    
    # Default configuration
    default_config = {
        "query_depth": "medium",
        "complexity_level": "standard", 
        "max_iterations": 3,
        "context_window": 5000,
        "crawling_depth": 2,
        "focus_domains": ["ciela.net", "apis.bg", "lakorda.com"]
    }
    
    if config:
        default_config.update(config)
    
    # Enhanced response processing with configuration
    response = graph.invoke({
        "messages": [HumanMessage(content=input_message)],
        "config": default_config
    })

    # Extract and format the content with better handling
    if not response.get('messages'):
        return "Няма генериран отговор."
    
    # Get the last message content
    last_message = response['messages'][-1]
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # Extract sources from all messages for top sources formatting
    all_sources = []
    for msg in response['messages']:
        if hasattr(msg, 'content'):
            msg_content = msg.content
            # Look for sources in the message content 
            if isinstance(msg_content, list):
                for item in msg_content:
                    if isinstance(item, dict) and 'title' in item and 'href' in item:
                        all_sources.append(item)

    # Format the response with top sources at the beginning if not already formatted
    if "📚 **ТОП 5 НАЙ-РЕЛЕВАНТНИ ИЗТОЧНИЦИ**" not in content and all_sources:
        top_sources = format_top_sources(all_sources[:5])
        result = top_sources + content
    else:
        result = content

    # Add metadata about the processing
    result += f"\n\n---\n*Обработено от {len(response['messages'])} агентни взаимодействия*"
    result += f"\n*Конфигурация: {default_config['query_depth']} дълбочина, {default_config['complexity_level']} сложност*"
    
    return result

def run_graph_with_streaming(input_message, progress_callback=None, config=None):
    """Run graph with streaming for better user experience and progress tracking"""
    graph = build_graph()
    
    # Default configuration
    default_config = {
        "query_depth": "medium",
        "complexity_level": "standard", 
        "max_iterations": 3,
        "context_window": 5000,
        "crawling_depth": 2,
        "focus_domains": ["ciela.net", "apis.bg", "lakorda.com"]
    }
    
    if config:
        default_config.update(config)
    
    print("🤖 Започвам българско правно изследване...\n")
    
    events_processed = 0
    total_steps = default_config['max_iterations'] * 3  # Estimate based on agents
    
    try:
        for event in graph.stream({
            "messages": [HumanMessage(content=input_message)],
            "config": default_config
        }):
            for key, value in event.items():
                if key != "__end__":
                    events_processed += 1
                    progress = min(events_processed / total_steps, 1.0)
                    
                    # Enhanced progress tracking
                    if progress_callback:
                        if "Bulgarian_Legal_Searcher" in key:
                            progress_callback(f"🔍 Търся в български правни бази данни...", progress)
                        elif "Legal_Document_Analyzer" in key:
                            progress_callback(f"📚 Анализирам правни документи...", progress)
                        elif "Legal_Citation_Specialist" in key:
                            progress_callback(f"📖 Форматирам финален отговор...", progress)
                        elif "Supervisor" in key:
                            progress_callback(f"⚖️ Координирам правния анализ...", progress)
                    
                    print(f"📊 **{key}**: {value}")
                    print("---")
                    time.sleep(0.1)  # Small delay for better user experience
        
        # Get final result
        final_response = graph.invoke({
            "messages": [HumanMessage(content=input_message)],
            "config": default_config
        })
        
        return run_graph(input_message, config)  # Use the existing formatting
        
    except Exception as e:
        print(f"Грешка по време на стрийминг изпълнението: {e}")
        return run_graph(input_message, config)  # Fallback to regular execution

def get_graph_info():
    """Get information about the Bulgarian legal graph structure"""
    graph = build_graph()
    graph_dict = graph.get_graph()
    
    info = {
        "nodes": list(graph_dict.nodes.keys()),
        "edges": [(edge.source, edge.target) for edge in graph_dict.edges],
        "entry_point": "Supervisor",
        "specialized_agents": [
            "Bulgarian_Legal_Searcher - Експерт по търсене в БГ правни бази",
            "Legal_Document_Analyzer - Анализатор на правни документи", 
            "Legal_Citation_Specialist - Специалист по цитати и форматиране"
        ],
        "supported_domains": ["ciela.net", "apis.bg", "lakorda.com"],
        "legal_areas": ["Гражданско право", "Наказателно право", "Административно право", "Търговско право", "Трудово право"],
        "tools_available": [
            "google_cse_search - Google търсене за правни документи",
            "bulgarian_legal_search - Специализирано БГ правно търсене",
            "legal_precedent_search - Търсене на съдебна практика",
            "process_content - Анализ на правни документи"
        ]
    }
    
    return info

def get_config_options():
    """Get available configuration options for the legal research system"""
    return {
        "query_depth": {
            "shallow": "Повърхностно търсене - бързи резултати",
            "medium": "Средна дълбочина - балансирано търсене", 
            "deep": "Дълбоко търсене - изчерпателен анализ"
        },
        "complexity_level": {
            "basic": "Основно ниво - прости обяснения",
            "standard": "Стандартно ниво - подробен анализ",
            "expert": "Експертно ниво - техническо съдържание"
        },
        "max_iterations": {
            1: "Бързо търсене (1 итерация)",
            2: "Стандартно търсене (2 итерации)", 
            3: "Задълбочено търсене (3 итерации)",
            4: "Изчерпателно търсене (4 итерации)"
        },
        "context_window": {
            2000: "Малък контекст (2K думи)",
            5000: "Среден контекст (5K думи)",
            8000: "Голям контекст (8K думи)",
            10000: "Максимален контекст (10K думи)"
        },
        "crawling_depth": {
            1: "Само първо ниво на документи",
            2: "До второ ниво на препратки",
            3: "До трето ниво на препратки"
        }
    }

# Helper function to format sources for the response
def format_top_sources(sources, limit=5):
    """Format top sources with metadata for the response"""
    if not sources or not isinstance(sources, list):
        return "📚 **ТОП 5 НАЙ-РЕЛЕВАНТНИ ИЗТОЧНИЦИ**\n\nНяма налични източници.\n\n"
    
    formatted = "📚 **ТОП 5 НАЙ-РЕЛЕВАНТНИ ИЗТОЧНИЦИ**\n\n"
    
    for i, source in enumerate(sources[:limit], 1):
        if isinstance(source, dict):
            title = source.get('title', 'Без заглавие')
            href = source.get('href', '#')
            body = source.get('body', '')
            domain = source.get('source_domain', 'Неизвестен източник')
            
            # Extract key information for metadata  
            snippet = body[:80] + "..." if len(body) > 80 else body
            
            formatted += f"**{i}. [{title}]({href})**\n"
            formatted += f"   🏛️ *{domain}*\n" 
            formatted += f"   📄 {snippet}\n\n"
    
    formatted += "---\n\n"
    return formatted

def extract_sources_from_response(response_messages):
    """Extract sources from response messages for formatting"""
    sources = []
    
    for message in response_messages:
        content = message.content if hasattr(message, 'content') else str(message)
        
        # Look for source patterns in the content
        import re
        
        # Pattern to match source dictionaries or lists
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and 'title' in item and 'href' in item:
                    sources.append(item)
        elif hasattr(content, 'sources') or 'title' in str(content):
            # Try to extract sources from content
            continue
    
    return sources