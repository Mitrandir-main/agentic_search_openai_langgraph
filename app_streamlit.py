import streamlit as st
from dotenv import load_dotenv
from graph import run_graph, run_graph_with_streaming, visualize_graph, get_graph_info
import os

load_dotenv()

def main():
    st.set_page_config(
        page_title="🔍 AI-Powered Agentic Search & Insights",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar with configuration and info
    with st.sidebar:
        st.title("🛠️ Configuration")
        
        # Check API keys
        openai_key = os.getenv('OPENAI_API_KEY')
        tavily_key = os.getenv('TAVILY_API_KEY')
        
        st.subheader("🔑 API Status")
        st.write("✅ OpenAI:" if openai_key else "❌ OpenAI:", "Configured" if openai_key else "Missing")
        st.write("✅ Tavily:" if tavily_key else "❌ Tavily:", "Configured" if tavily_key else "Missing (Optional)")
        
        # Search options
        st.subheader("🎯 Search Options")
        bulgarian_focus = st.checkbox("🇧🇬 Focus on Bulgarian sources", value=False)
        current_events = st.checkbox("📅 Prioritize current events", value=True)
        
        # Advanced options
        st.subheader("⚙️ Advanced")
        show_streaming = st.checkbox("📡 Show streaming results", value=False)
        show_graph_info = st.checkbox("📊 Show graph structure", value=False)
        
        if st.button("🎨 Generate Graph Visualization"):
            with st.spinner("Generating visualization..."):
                try:
                    mermaid_syntax = visualize_graph()
                    st.success("✅ Visualization generated!")
                    st.text_area("Mermaid Syntax:", value=mermaid_syntax, height=200)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    # Main content
    st.title("🔍 AI-Powered Agentic Search & Insights")
    st.markdown("""
    **Advanced AI system for intelligent search and analysis**
    - 🌐 Multi-agent web search and analysis
    - 🇧🇬 Bulgarian language and regional content support  
    - 📊 Real-time insights and current information
    - 🔄 Streaming results with agent interactions
    """)
    
    # Input section
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_area(
            "Enter your search query or research question:",
            height=100,
            placeholder="Example: What are the latest developments in AI technology in Bulgaria?"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        search_button = st.button("🔍 Search & Analyze", type="primary", use_container_width=True)
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.rerun()
    
    # Show graph info if requested
    if show_graph_info:
        with st.expander("📊 Graph Structure Information", expanded=False):
            try:
                info = get_graph_info()
                col1, col2 = st.columns(2)
                with col1:
                    st.json({"nodes": info["nodes"], "entry_point": info["entry_point"]})
                with col2:
                    st.json({"edges": info["edges"], "tools": info["tools_available"]})
            except Exception as e:
                st.error(f"Error loading graph info: {e}")
    
    # Process search
    if search_button and user_input:
        # Enhance query based on options
        enhanced_query = user_input
        if bulgarian_focus:
            enhanced_query += " (focus on Bulgarian sources and .bg websites)"
        if current_events:
            enhanced_query += " (prioritize current and recent information)"
        
        if not openai_key:
            st.error("❌ OpenAI API key is required. Please add it to your .env file.")
            return
        
        # Results section
        st.markdown("---")
        st.subheader("📋 Search Results")
        
        if show_streaming:
            # Streaming results
            st.markdown("### 🔄 Live Agent Processing")
            with st.container():
                result_placeholder = st.empty()
                
                with st.spinner("🤖 Agents are working..."):
                    try:
                        result = run_graph_with_streaming(enhanced_query)
                    except Exception as e:
                        st.error(f"❌ Streaming error: {e}")
                        result = run_graph(enhanced_query)
        else:
            # Standard results
            with st.spinner("🔍 Searching and analyzing..."):
                try:
                    result = run_graph(enhanced_query)
                except Exception as e:
                    st.error(f"❌ Error during processing: {e}")
                    return
        
        # Display results
        if result:
            st.markdown("### 🎯 Analysis Results")
            
            # Split result into main content and references
            if "**References:**" in result:
                main_content, references = result.split("**References:**", 1)
                
                # Main content
                st.markdown(main_content)
                
                # References in expandable section
                with st.expander("📚 References & Sources", expanded=False):
                    st.markdown("**References:**" + references)
            else:
                st.markdown(result)
        else:
            st.warning("⚠️ No results generated. Please try a different query.")
    
    elif search_button and not user_input:
        st.warning("⚠️ Please enter a search query.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        Powered by LangGraph, OpenAI, and DuckDuckGo Search<br>
        🇧🇬 Enhanced for Bulgarian content and current information
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()