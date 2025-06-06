import json
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from agents import AgentState, create_supervisor, create_search_agent, create_insights_researcher_agent, get_members

def build_graph():
    supervisor_chain = create_supervisor()
    search_node = create_search_agent()
    insights_research_node = create_insights_researcher_agent()

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("Supervisor", supervisor_chain)
    graph_builder.add_node("Web_Searcher", search_node)
    graph_builder.add_node("Insight_Researcher", insights_research_node)

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
            f.write("# Agent Graph Visualization\n\n")
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

def run_graph(input_message):
    graph = build_graph()
    
    # Enhanced response processing
    response = graph.invoke({
        "messages": [HumanMessage(content=input_message)]
    })

    # Extract and format the content with better handling
    if not response.get('messages'):
        return "No response generated."
    
    # Get the last message content
    last_message = response['messages'][-1]
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # Initialize results and references
    result = ""
    references = []

    # Split content by lines and process
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith("[^"):  # Assuming references start with [^
            references.append(line.strip())
        else:
            result += line + "\n"

    # Format references
    if references:
        result += "\n\n**References:**\n"
        for ref in references:
            result += f"{ref}\n"

    # Add metadata about the processing
    result += f"\n\n*Processed by {len(response['messages'])} agent interactions*"
    
    return result

def run_graph_with_streaming(input_message):
    """Run graph with streaming for better user experience"""
    graph = build_graph()
    
    print("🤖 Starting agentic search and analysis...\n")
    
    try:
        for event in graph.stream({
            "messages": [HumanMessage(content=input_message)]
        }):
            for key, value in event.items():
                if key != "__end__":
                    print(f"📊 **{key}**: {value}")
                    print("---")
        
        # Get final result
        final_response = graph.invoke({
            "messages": [HumanMessage(content=input_message)]
        })
        
        return run_graph(input_message)  # Use the existing formatting
        
    except Exception as e:
        print(f"Error during streaming execution: {e}")
        return run_graph(input_message)  # Fallback to regular execution

def get_graph_info():
    """Get information about the graph structure"""
    graph = build_graph()
    graph_dict = graph.get_graph()
    
    info = {
        "nodes": list(graph_dict.nodes.keys()),
        "edges": [(edge.source, edge.target) for edge in graph_dict.edges],
        "entry_point": "Supervisor",
        "tools_available": ["internet_search_DDGO", "bulgarian_search", "current_events_search", "process_content"]
    }
    
    return info