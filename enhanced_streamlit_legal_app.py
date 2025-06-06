import streamlit as st
from dotenv import load_dotenv
from enhanced_legal_graph import (
    run_legal_research,
    run_legal_research_with_streaming,
    visualize_legal_graph,
    get_legal_graph_info
)
# Domain configurations moved inline to avoid dependencies
import os
import json
from datetime import datetime
import pandas as pd

load_dotenv()

def main():
    st.set_page_config(
        page_title="🏛️ Enhanced Bulgarian Legal Research System",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for legal styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2e6da4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .legal-domain {
        background: #f8f9fa;
        padding: 1rem;
        border-left: 4px solid #1f4e79;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .agent-status {
        background: #e8f4f8;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ Enhanced Bulgarian Legal Research System</h1>
        <p>Специализирана система за изследване на българското право с мултиагентна архитектура</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.title("🛠️ Конфигурация на изследването")
        
        # API Status
        st.subheader("🔑 API Статус")
        openai_key = os.getenv('OPENAI_API_KEY')
        st.write("✅ OpenAI:" if openai_key else "❌ OpenAI:", "Конфигуриран" if openai_key else "Липсва")
        
        # Legal Domain Selection
        st.subheader("🌐 Избор на правни домейни")
        st.write("Изберете специфични български правни домейни за търсене:")
        
        selected_domains = {}
        
        # Simple domain selection with fallback
        domain_options = {
            'lex_bg': 'LexBG - Bulgarian Legal Database',
            'vks_bg': 'Supreme Court of Cassation (ВКС)',
            'vss_bg': 'Supreme Administrative Court (ВАС)', 
            'justice_bg': 'Ministry of Justice',
            'parliament_bg': 'National Assembly',
            'cpc_bg': 'Data Protection Commission (КЗЛД)',
            'dv_bg': 'State Gazette'
        }
        
        for domain_key, domain_name in domain_options.items():
            selected = st.checkbox(
                f"**{domain_name}**", 
                value=True,
                key=f"domain_{domain_key}",
                help=f"Search in {domain_key.replace('_', '.')} domain"
            )
            selected_domains[domain_key] = selected
        
        # Legal Area Focus
        st.subheader("⚖️ Правна област")
        
        # Simple legal area options
        legal_area_options = {
            "auto": "Автоматично определяне",
            "civil_law": "Гражданско право",
            "criminal_law": "Наказателно право", 
            "administrative_law": "Административно право",
            "constitutional_law": "Конституционно право",
            "commercial_law": "Търговско право",
            "labor_law": "Трудово право",
            "tax_law": "Данъчно право",
            "data_protection": "Защита на данните"
        }
        
        legal_area = st.selectbox(
            "Изберете специализирана правна област:",
            list(legal_area_options.keys()),
            format_func=lambda x: legal_area_options[x]
        )
        
        # Search Options
        st.subheader("🎯 Опции за търсене")
        workflow_type = st.selectbox(
            "Тип на работния поток:",
            ["auto", "research_heavy", "precedent_focused", "document_analysis", "comprehensive"],
            help="Автоматично определяне на оптималния workflow въз основа на заявката"
        )
        
        show_streaming = st.checkbox("📡 Показване на streaming резултати", value=True)
        show_agent_details = st.checkbox("🤖 Детайли за агентите", value=False)
        show_citations = st.checkbox("📚 Извличане на цитати", value=True)
        
        # Advanced Options
        st.subheader("⚙️ Разширени настройки")
        max_iterations = st.slider("Максимум итерации", 3, 10, 6)
        confidence_threshold = st.slider("Праг на доверие", 0.1, 1.0, 0.7)
        
        # Graph Visualization
        if st.button("🎨 Генериране на визуализация"):
            with st.spinner("Генериране на визуализация..."):
                try:
                    mermaid_syntax = visualize_legal_graph()
                    st.success("✅ Визуализация генерирана!")
                    with st.expander("📊 Mermaid код"):
                        st.code(mermaid_syntax, language="text")
                except Exception as e:
                    st.error(f"❌ Грешка: {e}")
    
    # Initialize session state for user input
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📝 Правна заявка")
        user_input = st.text_area(
            "Въведете вашата правна заявка или въпрос:",
            value=st.session_state.user_input,
            height=120,
            placeholder="Пример: Какви са изискванията за регистрация на търговско дружество според българското право? Какви са последните изменения в Търговския закон?",
            help="Бъдете специфични за по-добри резултати. Системата ще търси само в български правни източници.",
            key="main_input"
        )
        
        # Update session state when user types
        st.session_state.user_input = user_input
        
        # Quick examples with better layout
        st.write("**Примерни заявки (кликнете за използване):**")
        example_queries = [
            "Процедура за регистрация на ООД в България",
            "Какво е наказание и обещетение при счупване на ръка", 
            "Съдебна практика по данъчни нарушения 2024",
            "Изисквания за GDPR съответствие в България",
            "Трудово законодателство - прекратяване на договор",
            "Административно обжалване на данъчни актове"
        ]
        
        # Create example buttons in a 2-column grid
        cols = st.columns(2)
        for i, example in enumerate(example_queries):
            col_idx = i % 2
            with cols[col_idx]:
                if st.button(f"📋 {example}", key=f"example_{i}", use_container_width=True):
                    st.session_state.user_input = example
                    st.rerun()
    
    with col2:
        st.subheader("📊 Статистики на системата")
        
        # Display selected domains
        active_domains = [k for k, v in selected_domains.items() if v]
        st.metric("Активни домейни", len(active_domains), len(domain_options))
        
        # Simple system info
        st.metric("Агенти в системата", 6)  # Known agent count
        st.metric("Правни области", len(legal_area_options) - 1)  # Exclude 'auto'
        
        # Show active domains
        if active_domains:
            st.write("**Активни домейни:**")
            for domain in active_domains:
                domain_name = domain_options.get(domain, domain)
                domain_url = domain.replace('_', '.')
                st.markdown(f"""
                <div class="legal-domain">
                    <strong>{domain_name}</strong><br>
                    <small>{domain_url}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # Search execution
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_button = st.button("🔍 Започване на правно изследване", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Изчистване", use_container_width=True)
    
    with col3:
        if st.button("📊 Информация за графа", use_container_width=True):
            simple_info = {
                "agents": 6,
                "domains": len(domain_options),
                "legal_areas": len(legal_area_options) - 1,
                "active_domains": active_domains
            }
            st.json(simple_info)
    
    if clear_button:
        st.session_state.user_input = ""
        st.rerun()
    
    # Process legal research
    if search_button and user_input:
        if not openai_key:
            st.error("❌ OpenAI API ключ е необходим. Моля, добавете го във вашия .env файл.")
            return
        
        # Filter query based on selected domains
        domain_context = ""
        if active_domains:
            domain_names = [domain_options.get(d, d) for d in active_domains]
            domain_context = f" (Фокус върху: {', '.join(domain_names)})"
        
        enhanced_query = user_input + domain_context
        
        # Results section
        st.markdown("---")
        st.subheader("📋 Резултати от правното изследване")
        
        if show_streaming:
            # Streaming results
            st.markdown("### 🔄 Обработка в реално време")
            
            with st.container():
                result_placeholder = st.empty()
                
                with st.spinner("🏛️ Агентите работят върху вашата заявка..."):
                    try:
                        if show_agent_details:
                            # Show detailed streaming
                            result = run_legal_research_with_streaming(enhanced_query)
                        else:
                            # Regular processing with progress
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            status_text.text("🔍 Инициализиране на агентите...")
                            progress_bar.progress(20)
                            
                            status_text.text("📚 Търсене в правни бази данни...")
                            progress_bar.progress(40)
                            
                            status_text.text("🧠 Анализ на правната информация...")
                            progress_bar.progress(60)
                            
                            status_text.text("⚖️ Търсене на съдебна практика...")
                            progress_bar.progress(80)
                            
                            result = run_legal_research(enhanced_query, workflow_type)
                            
                            status_text.text("✅ Завършване на анализа...")
                            progress_bar.progress(100)
                            
                            # Clear progress indicators
                            progress_bar.empty()
                            status_text.empty()
                            
                    except Exception as e:
                        st.error(f"❌ Грешка при обработката: {e}")
                        return
        else:
            # Standard processing
            with st.spinner("🔍 Извършване на правно изследване..."):
                try:
                    result = run_legal_research(enhanced_query, workflow_type)
                except Exception as e:
                    st.error(f"❌ Грешка при обработката: {e}")
                    return
        
        # Display results
        if result:
            st.markdown("### 🎯 Резултати от анализа")
            
            # Parse and display structured results
            if "**ПРАВНО ИЗСЛЕДВАНЕ - РЕЗУЛТАТИ**" in result:
                # Enhanced results format
                sections = result.split("##")
                
                for section in sections:
                    if section.strip():
                        section_lines = section.strip().split("\n")
                        section_title = section_lines[0].strip()
                        section_content = "\n".join(section_lines[1:]).strip()
                        
                        if section_title and section_content:
                            if "Метаданни" in section_title:
                                with st.expander("📅 Метаданни на изследването", expanded=False):
                                    st.markdown(section_content)
                            elif "цитати" in section_title.lower():
                                with st.expander("📚 Правни цитати", expanded=show_citations):
                                    st.markdown(section_content)
                            elif "Източници" in section_title:
                                with st.expander("🌐 Използвани източници", expanded=False):
                                    st.markdown(section_content)
                            elif "ОСНОВЕН АНАЛИЗ" in section_title:
                                st.markdown("### 🎯 Основен анализ")
                                st.markdown(section_content)
                            elif "агенти" in section_title.lower():
                                if show_agent_details:
                                    with st.expander("🤖 Детайли за агентите", expanded=False):
                                        st.markdown(section_content)
                            elif "Качество" in section_title:
                                with st.expander("📊 Качество на изследването", expanded=False):
                                    st.markdown(section_content)
            else:
                # Simple result format
                st.markdown(result)
                
        else:
            st.warning("⚠️ Няма генерирани резултати. Моля, опитайте с различна заявка.")
    
    elif search_button and not user_input:
        st.warning("⚠️ Моля, въведете правна заявка.")
    
    # Footer with system information
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🏛️ Система информация:**
        - Специализирана за българското право
        - Мултиагентна архитектура
        - Conciliator pattern за разрешаване на конфликти
        """)
    
    with col2:
        st.markdown("""
        **🌐 Покрити домейни:**
        - lex.bg, vks.bg, vss.bg
        - justice.bg, parliament.bg
        - cpc.bg, dv.bg
        """)
    
    with col3:
        st.markdown("""
        **🤖 Агенти:**
        - Legal Researcher
        - Legal Analyst  
        - Precedent Finder
        - Document Reviewer
        - Legal Conciliator
        """)
    
    st.markdown("""
    <div style='text-align: center; color: #666; margin-top: 2rem;'>
        Powered by Enhanced LangGraph, OpenAI, and specialized Bulgarian legal tools<br>
        🇧🇬 Фокусирана върху българското законодателство и съдебна практика
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 