import functools, operator
from typing import Annotated, Sequence, TypedDict, Optional, Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain.output_parsers.openai_tools import JsonOutputToolsParser
from enhanced_legal_tools import get_enhanced_legal_tools
from bulgarian_legal_domains import BULGARIAN_LEGAL_DOMAINS, BULGARIAN_LEGAL_AREAS
import json

load_dotenv()

# Enhanced LLM with better performance for legal tasks
llm = ChatOpenAI(
    model="gpt-4o",  # Latest model
    temperature=0.1,  # Low temperature for legal accuracy
    verbose=True
)

legal_tools = get_enhanced_legal_tools()

class LegalAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    legal_area: Optional[str]
    confidence: Optional[float]
    sources_checked: Annotated[Sequence[str], operator.add]
    iterations: int
    max_iterations: int
    final_decision: Optional[str]
    citations: Annotated[Sequence[str], operator.add]

def create_legal_agent(llm: ChatOpenAI, tools: list, system_prompt: str):
    """Create enhanced legal agent with better prompting"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )
    return executor

def legal_agent_node(state, agent, name):
    """Enhanced agent node with better state management"""
    result = agent.invoke(state)
    
    # Extract citations and sources from the result
    citations = []
    if "citations" in result.get("output", "").lower():
        # Simple citation extraction - can be enhanced
        import re
        citation_pattern = r'чл\.\s*\d+|решение\s+№\s*\d+'
        citations = re.findall(citation_pattern, result.get("output", ""), re.IGNORECASE)
    
    return {
        "messages": [HumanMessage(content=result["output"], name=name)],
        "sources_checked": [name],
        "citations": citations
    }

def get_legal_members():
    """Define specialized legal agents"""
    return ["Legal_Researcher", "Legal_Analyst", "Precedent_Finder", "Document_Reviewer"]

def create_legal_supervisor():
    """Enhanced supervisor with legal domain understanding"""
    members = get_legal_members()
    
    system_prompt = f"""Вие сте главен правен супервайзор, който управлява екип от специализирани правни агенти: {members}.

Въз основа на правната заявка на потребителя, определете кой агент трябва да предприеме следващото действие:

- **Legal_Researcher**: Търси правна информация в български правни домейни (lex.bg, vks.bg, vss.bg, etc.)
- **Legal_Analyst**: Анализира правни документи и извлича ключова информация
- **Precedent_Finder**: Търси съдебна практика и precedents в българските съдилища
- **Document_Reviewer**: Прегледа и анализира правни документи за цитати и препратки

Всеки агент докладва резултатите си и напредъка. Когато всички задачи са завършени, индикирайте с 'FINISH'.

Винаги отговаряйте на български език и фокусирайте се върху българското законодателство и съдебна практика.
"""
    
    options = ["FINISH"] + members
    
    function_def = {
        "type": "function",
        "function": {
            "name": "route",
            "description": "Избиране на следващия агент за работа",
            "parameters": {
                "type": "object",
                "properties": {
                    "next": {"type": "string", "enum": options},
                    "reasoning": {"type": "string", "description": "Обяснение защо се избира този агент"}
                },
                "required": ["next", "reasoning"],
            },
        }
    }
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Въз основа на разговора по-горе, кой трябва да действа следващ? Или трябва да FINISH? Изберете от: {options}"),
    ]).partial(options=str(options), members=", ".join(members))
    
    supervisor_chain = (
        prompt 
        | llm.bind_tools(tools=[function_def], tool_choice={"type": "function", "function": {"name": "route"}}) 
        | JsonOutputToolsParser(first_tool_only=True)
    )
    
    return supervisor_chain

def create_legal_researcher_agent():
    """Specialized Bulgarian legal research agent"""
    legal_researcher = create_legal_agent(
        llm, 
        legal_tools, 
        """Вие сте експертен правен изследовател, специализиран в българското право.

Вашата роля е да:
1. Търсите правна информация в специализирани български правни бази данни
2. Фокусирате се върху актуални закони, наредби и нормативни актове
3. Използвате domain-specific търсене за lex.bg, vks.bg, vss.bg, justice.bg, parlament.bg
4. Идентифицирате правната област (корпоративно право, административно право, etc.)
5. Предоставяте точни цитати с чл., ал., т.

ВАЖНО: 
- Търсете само в български правни домейни
- Използвайте българска правна терминология
- Проверявайте дали информацията е актуална (2024-2025)
- Цитирайте конкретни правни източници

Започнете всеки отговор с определяне на правната област, след което предоставете подробно изследване."""
    )
    
    legal_researcher_node = functools.partial(legal_agent_node, agent=legal_researcher, name="Legal_Researcher")
    return legal_researcher_node

def create_legal_analyst_agent():
    """Advanced legal analysis agent"""
    legal_analyst = create_legal_agent(
        llm,
        legal_tools,
        """Вие сте експертен правен анализатор с дълбоки познания в българското право.

Вашата роля е да:
1. Анализирате правни документи и извличате ключова информация
2. Идентифицирате правни цитати, препратки и важни клаузи
3. Оценявате правните последици и рискове
4. Синтезирате информация от множество източници
5. Предоставяте практически правни съвети

СПЕЦИАЛИЗАЦИЯ:
- Анализ на договори и споразумения
- Оценка на правни рискове
- Тълкуване на нормативни актове
- Съпоставяне с българската съдебна практика

Винаги структурирайте отговорите си с:
- Основни правни въпроси
- Приложимо законодателство
- Съдебна практика
- Препоръки за действие"""
    )
    
    legal_analyst_node = functools.partial(legal_agent_node, agent=legal_analyst, name="Legal_Analyst")
    return legal_analyst_node

def create_precedent_finder_agent():
    """Specialized agent for finding legal precedents"""
    precedent_finder = create_legal_agent(
        llm,
        legal_tools,
        """Вие сте експерт по българската съдебна практика и precedents.

Вашата роль е да:
1. Търсите съдебни решения в ВКС, ВАС и други български съдилища
2. Анализирате съдебна практика и тълкувателни решения
3. Идентифицирате релевантни precedents за конкретни правни въпроси
4. Проследявате еволюцията на съдебната практика
5. Оценявате приложимостта на precedents към текущи случаи

ФОКУС ОБЛАСТИ:
- Решения на Върховния касационен съд (ВКС)
- Решения на Върховния административен съд (ВАС)
- Тълкувателни решения и практика
- Обединителни тези

Структурирайте отговорите с:
- Номер и дата на решението
- Правен въпрос/теза
- Мотивация на съда
- Приложимост към текущия случай"""
    )
    
    precedent_finder_node = functools.partial(legal_agent_node, agent=precedent_finder, name="Precedent_Finder")
    return precedent_finder_node

def create_document_reviewer_agent():
    """Specialized agent for legal document review"""
    document_reviewer = create_legal_agent(
        llm,
        legal_tools,
        """Вие сте експертен рецензент на правни документи с фокус върху българското право.

Вашата роля е да:
1. Прегледате и анализирате правни документи за пълнота и точност
2. Проверявате правни цитати и препратки
3. Идентифицирате противоречия или пропуски
4. Оценявате съответствието с българското законодателство
5. Предлагате подобрения и корекции

КЛЮЧОВИ ЗАДАЧИ:
- Проверка на правната терминология
- Валидиране на цитати (чл., ал., т.)
- Анализ на правните последици
- Оценка на рисковете и отговорностите

КАЧЕСТВЕН КОНТРОЛ:
- Актуалност на правните норми
- Точност на цитатите
- Пълнота на анализа
- Практичност на препоръките

Винаги предоставяйте структуриран feedback с конкретни препоръки за подобрение."""
    )
    
    document_reviewer_node = functools.partial(legal_agent_node, agent=document_reviewer, name="Document_Reviewer")
    return document_reviewer_node

def create_legal_conciliator_agent():
    """Conciliator agent for resolving conflicts between legal agents - new 2025 pattern"""
    legal_conciliator = create_legal_agent(
        llm,
        legal_tools,
        """Вие сте главен правен медиатор (Conciliator), който разрешава противоречия между правни агенти.

РОЛЯ И ОТГОВОРНОСТИ:
1. Анализирате различните мнения и находки на правните агенти
2. Идентифицирате противоречия във правните заключения
3. Взимате окончателни решения въз основа на:
   - Актуалност на източниците
   - Авторитет на съдебната практика  
   - Приложимост на правните норми
   - Качество на правния анализ

ПРОЦЕС НА РЕШАВАНЕ:
- Оценка на всяка позиция
- Анализ на правните основания
- Преценка на доказателствата
- Окончателно становище с мотивация

КРИТЕРИИ ЗА РЕШЕНИЕ:
- Съответствие с българското право
- Подкрепа от съдебна практика
- Актуалност на информацията
- Практическа приложимост

Винаги обосновавайте решенията си с конкретни правни аргументи и източници."""
    )
    
    legal_conciliator_node = functools.partial(legal_agent_node, agent=legal_conciliator, name="Legal_Conciliator")
    return legal_conciliator_node

def create_legal_memory_manager():
    """Manage legal research context and citations"""
    class LegalMemory:
        def __init__(self):
            self.legal_sources = []
            self.citations = []
            self.precedents = []
            self.domain_coverage = {domain: False for domain in BULGARIAN_LEGAL_DOMAINS.keys()}
            
        def add_source(self, source: str, domain: str = None):
            self.legal_sources.append(source)
            if domain in self.domain_coverage:
                self.domain_coverage[domain] = True
                
        def add_citation(self, citation: str):
            if citation not in self.citations:
                self.citations.append(citation)
                
        def add_precedent(self, precedent: str):
            if precedent not in self.precedents:
                self.precedents.append(precedent)
                
        def get_coverage_report(self):
            covered = sum(1 for covered in self.domain_coverage.values() if covered)
            total = len(self.domain_coverage)
            return f"Покрити домейни: {covered}/{total}"
            
    return LegalMemory()

def determine_legal_workflow(query: str) -> dict:
    """Determine the optimal workflow based on query type"""
    query_lower = query.lower()
    
    workflows = {
        "research_heavy": {
            "agents": ["Legal_Researcher", "Legal_Analyst", "Document_Reviewer"],
            "triggers": ["закон", "право", "нормативен акт", "изследване"]
        },
        "precedent_focused": {
            "agents": ["Precedent_Finder", "Legal_Analyst", "Document_Reviewer"], 
            "triggers": ["съдебна практика", "решение", "precedent", "съд"]
        },
        "document_analysis": {
            "agents": ["Document_Reviewer", "Legal_Analyst", "Legal_Researcher"],
            "triggers": ["договор", "документ", "анализ", "преглед"]
        },
        "comprehensive": {
            "agents": ["Legal_Researcher", "Legal_Analyst", "Precedent_Finder", "Document_Reviewer"],
            "triggers": ["комплексен", "пълен", "всичко", "общ"]
        }
    }
    
    for workflow_type, config in workflows.items():
        if any(trigger in query_lower for trigger in config["triggers"]):
            return {"type": workflow_type, "agents": config["agents"]}
    
    # Default to comprehensive workflow
    return {"type": "comprehensive", "agents": workflows["comprehensive"]["agents"]} 