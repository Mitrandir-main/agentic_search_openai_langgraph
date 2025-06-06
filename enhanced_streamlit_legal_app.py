import streamlit as st
import time
import json
from dotenv import load_dotenv
from graph import (
    run_graph, 
    run_graph_with_streaming, 
    visualize_graph, 
    get_graph_info,
    get_config_options,
    format_top_sources
)
import os
import threading
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

def main():
    st.set_page_config(
        page_title="🇧🇬 Българска Правна Изследователска Система",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        padding: 1rem 0;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .config-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .source-card {
        background: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .progress-text {
        font-weight: 600;
        color: #495057;
    }
    .legal-response {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🇧🇬 Българска Правна Изследователска Система</h1>
        <p>Интелигентно търсене и анализ на българското законодателство</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state for configuration and query tracking
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    if 'search_config' not in st.session_state:
        st.session_state.search_config = {
            "query_depth": "medium",
            "complexity_level": "standard",
            "max_iterations": 3,
            "context_window": 5000,
            "crawling_depth": 2
        }
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

    # Sidebar with configuration and status
    with st.sidebar:
        st.title("🛠️ Конфигурация")
        
        # API status check
        openai_key = os.getenv('OPENAI_API_KEY')
        google_cse_key = os.getenv('GOOGLE_CSE_API_KEY')
        
        st.subheader("🔑 Статус на API")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("OpenAI", "🟢 Активно" if openai_key else "🔴 Неактивно")
        with col2:
            st.metric("Google CSE", "🟢 Активно" if google_cse_key else "🔴 Неактивно")
        
        st.divider()
        
        # Configuration options
        st.subheader("⚙️ Параметри на търсенето")
        config_options = get_config_options()
        
        # Query depth configuration
        st.session_state.search_config["query_depth"] = st.selectbox(
            "🔍 Дълбочина на търсенето:",
            options=list(config_options["query_depth"].keys()),
            format_func=lambda x: config_options["query_depth"][x],
            index=list(config_options["query_depth"].keys()).index(st.session_state.search_config["query_depth"])
        )
        
        # Complexity level
        st.session_state.search_config["complexity_level"] = st.selectbox(
            "🎯 Ниво на сложност:",
            options=list(config_options["complexity_level"].keys()),
            format_func=lambda x: config_options["complexity_level"][x],
            index=list(config_options["complexity_level"].keys()).index(st.session_state.search_config["complexity_level"])
        )
        
        # Max iterations
        st.session_state.search_config["max_iterations"] = st.selectbox(
            "🔄 Максимални итерации:",
            options=list(config_options["max_iterations"].keys()),
            format_func=lambda x: config_options["max_iterations"][x],
            index=list(config_options["max_iterations"].keys()).index(st.session_state.search_config["max_iterations"])
        )
        
        # Context window
        st.session_state.search_config["context_window"] = st.selectbox(
            "📄 Размер на контекста:",
            options=list(config_options["context_window"].keys()),
            format_func=lambda x: config_options["context_window"][x],
            index=list(config_options["context_window"].keys()).index(st.session_state.search_config["context_window"])
        )
        
        # Crawling depth
        st.session_state.search_config["crawling_depth"] = st.selectbox(
            "🕷️ Дълбочина на обхождане:",
            options=list(config_options["crawling_depth"].keys()),
            format_func=lambda x: config_options["crawling_depth"][x],
            index=list(config_options["crawling_depth"].keys()).index(st.session_state.search_config["crawling_depth"])
        )
        
        st.divider()
        
                # Domain focus options
        st.subheader("🏛️ Фокус върху домейни")
        domain_options = {
            'lex_bg': 'LexBG - Правна база данни',
            'vks_bg': 'ВКС - Върховен касационен съд',
            'vss_bg': 'ВАС - Върховен административен съд',
            'justice_bg': 'Министерство на правосъдието'
        }
        
        selected_domains = []
        for domain_key, domain_name in domain_options.items():
            if st.checkbox(domain_name, value=True, key=f"domain_{domain_key}"):
                selected_domains.append(domain_key)
        
        st.session_state.search_config["focus_domains"] = selected_domains
        
        st.divider()
        
        # System information
        if st.button("📊 Информация за системата"):
            info = get_graph_info()
            st.json(info)

    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📝 Правна заявка")
        user_input = st.text_area(
            "Въведете вашата правна заявка или въпрос:",
            value=st.session_state.user_input,
            height=120,
            placeholder="Пример: Какви са изискванията за регистрация на търговско дружество според българското право?",
            help="Бъдете специфични за по-добри резултати. Системата ще търси в български правни източници.",
            key="query_input"
        )
        
        # Update session state when input changes
        if user_input != st.session_state.user_input:
            st.session_state.user_input = user_input
        
        # Quick example queries
        st.write("**💡 Примерни заявки:**")
        col_ex1, col_ex2 = st.columns(2)
        
        with col_ex1:
            if st.button("📋 Регистрация на ООД в България", use_container_width=True):
                st.session_state.user_input = "Процедура за регистрация на ООД в България"
                st.rerun()
            if st.button("⚖️ Съдебна практика по данъчни нарушения", use_container_width=True):
                st.session_state.user_input = "Съдебна практика по данъчни нарушения 2024"
                st.rerun()
        
        with col_ex2:
            if st.button("🤕 Обезщетение при телесна повреда", use_container_width=True):
                st.session_state.user_input = "Какво е наказание и обезщетение при счупване на ръка"
                st.rerun()
            if st.button("🛡️ GDPR съответствие в България", use_container_width=True):
                st.session_state.user_input = "Изисквания за GDPR съответствие в България"
                st.rerun()

    with col2:
        st.write("")  # Spacing
        search_button = st.button("🔍 Започни изследване", type="primary", use_container_width=True)
        clear_button = st.button("🗑️ Изчисти", use_container_width=True)
        
        if clear_button:
            st.session_state.user_input = ""
            st.rerun()

    # Process search with enhanced progress tracking
    if search_button and st.session_state.user_input:
        if not openai_key:
            st.error("❌ OpenAI API ключ е необходим. Моля, добавете го в .env файла.")
            return
        
        # Add query to history
        query_time = time.strftime("%H:%M:%S")
        st.session_state.search_history.append({
            "query": st.session_state.user_input,
            "time": query_time,
            "config": st.session_state.search_config.copy()
        })
        
        st.markdown("---")
        st.subheader("📋 Резултати от правното изследване")
        
        # Enhanced progress tracking
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            agent_details = st.empty()
        
        # Results container
        results_container = st.container()
        
        # Define progress callback
        def update_progress(message, progress):
            progress_bar.progress(progress)
            status_text.markdown(f"<div class='progress-text'>{message}</div>", unsafe_allow_html=True)
        
        # Execute search with streaming
        with st.spinner("🤖 Стартирам българската правна изследователска система..."):
            try:
                # Run the enhanced legal research
                result = run_graph_with_streaming(
                    st.session_state.user_input, 
                    progress_callback=update_progress,
                    config=st.session_state.search_config
                )
                
                # Complete progress
                progress_bar.progress(1.0)
                status_text.markdown("<div class='progress-text'>✅ Правното изследване завършено успешно!</div>", unsafe_allow_html=True)
                
                # Display results with enhanced formatting
                with results_container:
                    if result:
                        # Parse and format the result for better display
                        st.markdown(f"""
                        <div class="legal-response">
                        <h3>📋 ПРАВЕН АНАЛИЗ: {st.session_state.user_input[:100]}{"..." if len(st.session_state.user_input) > 100 else ""}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display the formatted result
                        st.markdown(result)
                        
                        # Add download option for the result
                        col_download1, col_download2 = st.columns(2)
                        with col_download1:
                            st.download_button(
                                label="📄 Изтегли като текст",
                                data=result,
                                file_name=f"pravno_izsledvane_{query_time.replace(':', '-')}.txt",
                                mime="text/plain"
                            )
                        
                        with col_download2:
                            # Format as JSON for structured download
                            structured_result = {
                                "query": st.session_state.user_input,
                                "timestamp": query_time,
                                "config": st.session_state.search_config,
                                "result": result
                            }
                            st.download_button(
                                label="📊 Изтегли като JSON",
                                data=json.dumps(structured_result, ensure_ascii=False, indent=2),
                                file_name=f"pravno_izsledvane_{query_time.replace(':', '-')}.json",
                                mime="application/json"
                            )
                    else:
                        st.warning("⚠️ Не бяха генерирани резултати. Моля, опитайте с различна заявка.")
                        
            except Exception as e:
                st.error(f"❌ Грешка по време на изследването: {e}")
                status_text.markdown("<div class='progress-text'>❌ Грешка по време на обработката</div>", unsafe_allow_html=True)

    elif search_button and not st.session_state.user_input:
        st.warning("⚠️ Моля, въведете правна заявка.")

    # Search history section
    if st.session_state.search_history:
        st.markdown("---")
        st.subheader("📚 История на търсенията")
        
        with st.expander(f"Показване на {len(st.session_state.search_history)} предишни заявки", expanded=False):
            for i, entry in enumerate(reversed(st.session_state.search_history[-10:]), 1):  # Show last 10
                st.markdown(f"""
                **{i}. {entry['time']}** - *{entry['query'][:100]}{"..." if len(entry['query']) > 100 else ""}*
                
                Конфигурация: {entry['config']['query_depth']} дълбочина, {entry['config']['max_iterations']} итерации
                """)
                
                if st.button(f"🔄 Повтори заявка {i}", key=f"repeat_{i}"):
                    st.session_state.user_input = entry['query']
                    st.session_state.search_config = entry['config']
                    st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
        <h4>🇧🇬 Българска Правна Изследователска Система</h4>
        <p>Базирана на LangGraph, OpenAI и Google Custom Search Engine</p>
        <p>Специализирана за българско законодателство и съдебна практика</p>
        <small>Версия 2.0 - Подобрена за българския правен контекст</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 