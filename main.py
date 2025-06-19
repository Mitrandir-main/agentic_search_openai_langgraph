#!/usr/bin/env python3
"""
FastAPI Backend for Bulgarian Legal Search System
Modern AI Chatbot Interface with Real-time Updates
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import json
import time
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Import existing functionality
from enhanced_legal_tools import enhanced_bulgarian_legal_search_sync
from relevancy_scoring import BulgarianLegalRelevancyScorer
from tools import get_tools

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="🇧🇬 Bulgarian Legal Search AI",
    description="Advanced AI-powered Bulgarian legal research system with real-time search capabilities",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str = Field(..., description="Legal search query in Bulgarian")
    max_results: int = Field(default=15, ge=5, le=50, description="Maximum number of results")
    min_relevancy: float = Field(default=0.3, ge=0.1, le=0.9, description="Minimum relevancy score")
    methodology: str = Field(default="enhanced", description="Search methodology")
    domains: Optional[List[str]] = Field(default=None, description="Specific domains to search")

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    search_time: float
    status: str = "success"  # success, error, no_results, fallback_success
    message: str = ""
    metadata: Optional[Dict[str, Any]] = None

class StatusUpdate(BaseModel):
    status: str
    message: str
    progress: float
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    message: str
    response: str
    status: str
    processing_time: float
    model_used: Optional[str] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                await self.disconnect_safely(connection)

    async def disconnect_safely(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

manager = ConnectionManager()

# Main frontend route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main AI chatbot interface"""
    return templates.TemplateResponse("index.html", {"request": request})

# API Routes
@app.post("/api/search", response_model=SearchResponse)
async def search_legal_content(request: SearchRequest):
    """Enhanced legal content search with comprehensive error handling and status updates"""
    
    try:
        # Broadcast search start status
        await manager.broadcast({
            "type": "search_status",
            "status": "starting",
            "message": f"🔍 Започвам търсене за: '{request.query}'",
            "query": request.query
        })
        
        # Validate query
        if not request.query or len(request.query.strip()) < 3:
            error_response = SearchResponse(
                query=request.query,
                results=[],
                total_results=0,
                search_time=0.0,
                status="error",
                message="❌ Моля, въведете по-дълга заявка (минимум 3 символа)"
            )
            await manager.broadcast({
                "type": "search_complete",
                "status": "error",
                "message": "Заявката е твърде кратка"
            })
            return error_response
        
        start_time = time.time()
        
        # Check environment configuration
        await manager.broadcast({
            "type": "search_status", 
            "status": "checking_config",
            "message": "🔧 Проверявам конфигурацията на API ключовете..."
        })
        
        google_configured = bool(os.getenv('GOOGLE_CSE_API_KEY') and os.getenv('GOOGLE_CSE_ID'))
        openai_configured = bool(os.getenv('OPENAI_API_KEY'))
        
        config_status = []
        if google_configured:
            config_status.append("✅ Google CSE")
        else:
            config_status.append("⚠️ Google CSE (ще използвам DuckDuckGo)")
            
        if openai_configured:
            config_status.append("✅ OpenAI")
        else:
            config_status.append("⚠️ OpenAI (ограничени AI функции)")
        
        await manager.broadcast({
            "type": "search_status",
            "status": "config_checked", 
            "message": f"🔧 Конфигурация: {' | '.join(config_status)}"
        })
        
        # Start search with methodology selection
        methodology = request.methodology or "enhanced"
        
        await manager.broadcast({
            "type": "search_status",
            "status": "searching",
            "message": f"🚀 Стартирам {methodology} търсене с до {request.max_results} резултата..."
        })
        
        try:
            if methodology == "enhanced":
                # Use the enhanced search with AI
                await manager.broadcast({
                    "type": "search_status",
                    "status": "ai_analysis",
                    "message": "🧠 AI анализира заявката и генерира интелигентни търсения..."
                })
                
                from enhanced_legal_tools import enhanced_bulgarian_legal_search_sync
                search_results = enhanced_bulgarian_legal_search_sync(
                    query=request.query,
                    max_results=request.max_results,
                    min_relevancy=request.min_relevancy
                )
                
            elif methodology == "vks":
                # VKS (Supreme Court) search - No progress messages, direct execution
                from enhanced_legal_tools import vks_bg_search, analyze_vks_documents
                
                # Get VKS results
                vks_results = vks_bg_search(request.query, request.max_results)
                
                if vks_results:
                    # Analyze VKS documents with GPT-4o-mini
                    analysis = await analyze_vks_documents(request.query, vks_results)
                    
                    # Format VKS results with AI analysis
                    search_results = format_enhanced_vks_results(request.query, analysis)
                else:
                    search_results = format_no_vks_results(request.query)
                
            elif methodology == "lex_bg":
                # LEX.BG specialized search
                await manager.broadcast({
                    "type": "search_status",
                    "status": "lex_bg_search", 
                    "message": "🏛️ Търся директно в базата данни на LEX.BG..."
                })
                
                from enhanced_legal_tools import lex_bg_search
                search_results = lex_bg_search(request.query, request.max_results)
                
            elif methodology == "multi_domain":
                # Multi-domain search
                await manager.broadcast({
                    "type": "search_status", 
                    "status": "multi_domain",
                    "message": "🌐 Търся в множество правни домейни..."
                })
                
                from enhanced_legal_tools import google_domain_search
                raw_results = google_domain_search(request.query, request.max_results)
                
                if raw_results:
                    # Format results for display
                    search_results = format_basic_results(request.query, raw_results)
                else:
                    search_results = "❌ Няма намерени резултати от мулти-домейн търсенето"
                    
            else:
                # Basic search fallback
                await manager.broadcast({
                    "type": "search_status",
                    "status": "basic_search", 
                    "message": "🔍 Извършвам основно търсене..."
                })
                
                from enhanced_legal_tools import fallback_ddg_search
                raw_results = fallback_ddg_search(request.query)
                
                if raw_results:
                    search_results = format_basic_results(request.query, raw_results)
                else:
                    search_results = "❌ Няма намерени резултати от основното търсене"
            
            search_time = time.time() - start_time
            
            # Analyze results
            if isinstance(search_results, str):
                if "❌" in search_results or "Няма намерени" in search_results:
                    # No results found
                    await manager.broadcast({
                        "type": "search_status",
                        "status": "no_results",
                        "message": "⚠️ Няма намерени релевантни резултати. Опитайте с различни ключови думи."
                    })
                    
                    response = SearchResponse(
                        query=request.query,
                        results=[],
                        total_results=0,
                        search_time=search_time,
                        status="no_results",
                        message=f"Няма намерени резултати за '{request.query}'. Опитайте с:\n• По-общи термини\n• Синоними\n• Различна формулировка"
                    )
                else:
                    # Results found - extract count from response
                    result_count = extract_result_count(search_results)
                    
                    await manager.broadcast({
                        "type": "search_status",
                        "status": "results_found",
                        "message": f"✅ Намерени {result_count} релевантни резултата за {search_time:.1f}с"
                    })
                    
                    response = SearchResponse(
                        query=request.query,
                        results=[{"content": search_results}],
                        total_results=result_count,
                        search_time=search_time,
                        status="success",
                        message=f"Успешно намерени {result_count} резултата"
                    )
            else:
                # Unexpected result format
                await manager.broadcast({
                    "type": "search_status",
                    "status": "format_error",
                    "message": "⚠️ Неочакван формат на резултатите"
                })
                
                response = SearchResponse(
                    query=request.query,
                    results=[],
                    total_results=0,
                    search_time=search_time,
                    status="error",
                    message="Грешка във формата на резултатите"
                )
            
        except ImportError as e:
            # Module import error
            error_msg = f"❌ Грешка при зареждане на модул: {str(e)}"
            logger.error(error_msg)
            
            await manager.broadcast({
                "type": "search_status",
                "status": "import_error",
                "message": f"⚠️ Проблем с модулите: {str(e)}"
            })
            
            response = SearchResponse(
                query=request.query,
                results=[],
                total_results=0,
                search_time=time.time() - start_time,
                status="error",
                message=f"Грешка при зареждане: {str(e)}"
            )
            
        except Exception as search_error:
            # Search execution error
            error_msg = f"❌ Грешка при търсене: {str(search_error)}"
            logger.error(error_msg)
            
            await manager.broadcast({
                "type": "search_status",
                "status": "search_error",
                "message": f"⚠️ Грешка при търсене: {str(search_error)}"
            })
            
            # Try fallback search
            try:
                await manager.broadcast({
                    "type": "search_status",
                    "status": "fallback",
                    "message": "🔄 Опитвам резервно търсене..."
                })
                
                from enhanced_legal_tools import fallback_ddg_search
                fallback_results = fallback_ddg_search(request.query)
                
                if fallback_results:
                    fallback_formatted = format_basic_results(request.query, fallback_results)
                    response = SearchResponse(
                        query=request.query,
                        results=[{"content": fallback_formatted}],
                        total_results=len(fallback_results),
                        search_time=time.time() - start_time,
                        status="fallback_success",
                        message=f"Резервно търсене намери {len(fallback_results)} резултата"
                    )
                else:
                    response = SearchResponse(
                        query=request.query,
                        results=[],
                        total_results=0,
                        search_time=time.time() - start_time,
                        status="error",
                        message=f"Грешка при търсене и резервното търсене не намери резултати: {str(search_error)}"
                    )
                    
            except Exception as fallback_error:
                response = SearchResponse(
                    query=request.query,
                    results=[],
                    total_results=0,
                    search_time=time.time() - start_time,
                    status="error",
                    message=f"Грешка при търсене и резервно търсене: {str(search_error)} | {str(fallback_error)}"
                )
        
        # Final status broadcast
        await manager.broadcast({
            "type": "search_complete",
            "status": response.status,
            "message": response.message,
            "total_results": response.total_results,
            "search_time": response.search_time
        })
        
        return response
        
    except Exception as e:
        # Top-level error handling
        error_msg = f"❌ Критична грешка: {str(e)}"
        logger.error(error_msg)
        
        await manager.broadcast({
            "type": "search_complete",
            "status": "critical_error",
            "message": error_msg
        })
        
        return SearchResponse(
            query=request.query or "",
            results=[],
            total_results=0,
            search_time=0.0,
            status="error",
            message=error_msg
        )

def extract_result_count(search_results: str) -> int:
    """Extract the number of results from the search response text"""
    import re
    
    # Look for patterns like "15 резултата", "5 източници", etc.
    patterns = [
        r'(\d+)\s+резултат',
        r'(\d+)\s+източник',
        r'Статистика.*?(\d+)\s+резултат',
        r'Намерени\s+(\d+)',
        r'TOP\s+(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, search_results, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    # Fallback: count the number of numbered items (1., 2., etc.)
    numbered_items = re.findall(r'^\*\*\d+\.', search_results, re.MULTILINE)
    if numbered_items:
        return len(numbered_items)
    
    # Default fallback
    return 1 if search_results and len(search_results) > 100 else 0

def format_basic_results(query: str, results: List[Dict]) -> str:
    """Format basic search results for display"""
    
    if not results:
        return f"❌ Няма намерени резултати за '{query}'"
    
    formatted_parts = []
    
    # Header
    formatted_parts.append(f"🔍 **РЕЗУЛТАТИ ЗА: '{query}'**")
    formatted_parts.append(f"📊 Намерени {len(results)} резултата")
    formatted_parts.append("=" * 60)
    
    # Results
    for i, result in enumerate(results[:15], 1):
        title = result.get('title', 'Без заглавие')
        url = result.get('href', result.get('url', ''))
        snippet = result.get('body', result.get('snippet', ''))[:200]
        source = result.get('source_domain', 'Неизвестен източник')
        
        formatted_parts.append(f"\n**{i}. {title}**")
        formatted_parts.append(f"🏛️ *{source}*")
        formatted_parts.append(f"📄 {snippet}...")
        if url:
            formatted_parts.append(f"🔗 {url}")
    
    formatted_parts.append(f"\n" + "=" * 60)
    formatted_parts.append(f"✅ Показани {min(len(results), 15)} от {len(results)} резултата")
    
    return "\n".join(formatted_parts)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics"""
    return {
        "active_connections": len(manager.active_connections),
        "available_domains": ["ciela.net", "apis.bg", "lakorda.com", "vks.bg"],
        "search_methodologies": ["enhanced", "vks", "standard", "experimental"],
        "system_status": "operational",
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Additional API endpoints for enhanced functionality
@app.post("/api/analyze")
async def analyze_legal_document(url: str):
    """Analyze a specific legal document URL"""
    try:
        # Use existing tools to analyze document
        from tools import process_content
        
        result = process_content(url)
        return {
            "url": url,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/domains")
async def get_available_domains():
    """Get list of available legal domains with statistics"""
    domains = {
        "ciela.net": {
            "authority": 0.95,
            "description": "Водеща българска правна платформа",
            "pages": "19,300+",
            "specialties": ["laws", "regulations", "case_law"]
        },
        "apis.bg": {
            "authority": 0.90,
            "description": "Апис - специализирано правно издателство",
            "pages": "4,190+",
            "specialties": ["legal_commentary", "analysis", "practice"]
        },
        "lakorda.com": {
            "authority": 0.75,
            "description": "Правни новини и анализи",
            "pages": "11+",
            "specialties": ["news", "analysis", "current_events"]
        }
    }
    return domains

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Enhanced AI chat with comprehensive error handling and status updates"""
    
    try:
        # Broadcast chat start status
        await manager.broadcast({
            "type": "chat_status",
            "status": "starting",
            "message": f"🤖 Започвам AI разговор за: '{request.message[:50]}...'"
        })
        
        # Validate message
        if not request.message or len(request.message.strip()) < 2:
            error_response = ChatResponse(
                message=request.message,
                response="❌ Моля, въведете по-дълго съобщение",
                status="error"
            )
            await manager.broadcast({
                "type": "chat_complete",
                "status": "error",
                "message": "Съобщението е твърде кратко"
            })
            return error_response
        
        start_time = time.time()
        
        # Check OpenAI configuration
        await manager.broadcast({
            "type": "chat_status",
            "status": "checking_config",
            "message": "🔧 Проверявам OpenAI конфигурацията..."
        })
        
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            error_response = ChatResponse(
                message=request.message,
                response="❌ OpenAI API ключът не е конфигуриран. Моля, добавете OPENAI_API_KEY в .env файла.",
                status="config_error"
            )
            await manager.broadcast({
                "type": "chat_complete",
                "status": "config_error",
                "message": "OpenAI API ключът липсва"
            })
            return error_response
        
        # Initialize OpenAI client
        try:
            await manager.broadcast({
                "type": "chat_status",
                "status": "initializing",
                "message": "🚀 Инициализирам AI модела..."
            })
            
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            
        except Exception as init_error:
            error_response = ChatResponse(
                message=request.message,
                response=f"❌ Грешка при инициализация на OpenAI: {str(init_error)}",
                status="init_error"
            )
            await manager.broadcast({
                "type": "chat_complete",
                "status": "init_error",
                "message": f"Грешка при инициализация: {str(init_error)}"
            })
            return error_response
        
        # Prepare context and system message
        await manager.broadcast({
            "type": "chat_status",
            "status": "preparing",
            "message": "📝 Подготвям контекста за разговора..."
        })
        
        system_message = """Ти си експертен български правен консултант и асистент. 
        Твоята роля е да помагаш на потребителите с въпроси свързани с българското законодателство.
        
        Важни указания:
        - Отговаряй винаги на български език
        - Бъди точен и професионален
        - Цитирай конкретни закони и разпоредби когато е възможно
        - Ако не си сигурен за нещо, кажи го ясно
        - Предоставяй практични съвети когато е уместно
        - Обяснявай сложни правни концепции с прости думи
        """
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Add context if provided
        if request.context:
            context_message = f"Контекст от предишно търсене:\n{request.context}"
            messages.append({"role": "user", "content": context_message})
        
        # Add user message
        messages.append({"role": "user", "content": request.message})
        
        # Make OpenAI API call
        try:
            await manager.broadcast({
                "type": "chat_status",
                "status": "processing",
                "message": "🧠 AI обработва заявката..."
            })
            
            response = client.chat.completions.create(
                model=request.model or "gpt-4o-mini",
                messages=messages,
                max_tokens=request.max_tokens or 1000,
                temperature=0.7,
                stream=False
            )
            
            ai_response = response.choices[0].message.content
            processing_time = time.time() - start_time
            
            await manager.broadcast({
                "type": "chat_status",
                "status": "success",
                "message": f"✅ AI отговори за {processing_time:.1f}с"
            })
            
            chat_response = ChatResponse(
                message=request.message,
                response=ai_response,
                status="success",
                processing_time=processing_time,
                model_used=request.model or "gpt-3.5-turbo"
            )
            
        except Exception as api_error:
            error_msg = str(api_error)
            
            # Handle specific OpenAI errors
            if "rate_limit" in error_msg.lower():
                user_message = "❌ Достигнат е лимитът на заявки. Моля, опитайте отново след малко."
            elif "insufficient_quota" in error_msg.lower():
                user_message = "❌ Недостатъчна квота за OpenAI API. Моля, проверете вашия акаунт."
            elif "invalid_api_key" in error_msg.lower():
                user_message = "❌ Невалиден OpenAI API ключ. Моля, проверете конфигурацията."
            else:
                user_message = f"❌ Грешка при комуникация с AI: {error_msg}"
            
            await manager.broadcast({
                "type": "chat_status",
                "status": "api_error",
                "message": f"⚠️ API грешка: {error_msg}"
            })
            
            chat_response = ChatResponse(
                message=request.message,
                response=user_message,
                status="api_error",
                processing_time=time.time() - start_time
            )
        
        # Final status broadcast
        await manager.broadcast({
            "type": "chat_complete",
            "status": chat_response.status,
            "message": "Разговорът завърши",
            "processing_time": chat_response.processing_time
        })
        
        return chat_response
        
    except Exception as e:
        # Top-level error handling
        error_msg = f"❌ Критична грешка в чата: {str(e)}"
        logger.error(error_msg)
        
        await manager.broadcast({
            "type": "chat_complete",
            "status": "critical_error",
            "message": error_msg
        })
        
        return ChatResponse(
            message=request.message or "",
            response=error_msg,
            status="error",
            processing_time=0.0
        )

@app.post("/api/vks-search")
async def vks_search_endpoint(request: SearchRequest):
    """
    Dedicated VKS (Supreme Court) search endpoint with enhanced AI analysis
    """
    try:
        start_time = time.time()
        
        # Import VKS functions
        from enhanced_legal_tools import vks_bg_search, analyze_vks_documents
        
        # Execute VKS search (no progress messages)
        vks_results = vks_bg_search(request.query, request.max_results)
        
        if not vks_results:
            response = SearchResponse(
                query=request.query,
                results=[{"content": format_no_vks_results(request.query)}],
                total_results=0,
                search_time=time.time() - start_time,
                status="no_results",
                message=f"Няма намерени решения от ВКС за '{request.query}'"
            )
        else:
            # Analyze VKS documents with GPT-4o-mini
            analysis = await analyze_vks_documents(request.query, vks_results)
            
            # Format results with enhanced formatting
            formatted_results = format_enhanced_vks_results(request.query, analysis)
            
            response = SearchResponse(
                query=request.query,
                results=[{"content": formatted_results, "vks_analysis": analysis}],
                total_results=len(vks_results),
                search_time=time.time() - start_time,
                status="success" if analysis.get('found_exact_match') else "partial_match",
                message=f"Намерени {len(vks_results)} документа от ВКС" + 
                       (" с точни съвпадения" if analysis.get('found_exact_match') else " с частични съвпадения"),
                metadata={
                    "search_method": "vks_bg_integration",
                    "court_level": "supreme",
                    "best_documents_count": len(analysis.get("best_documents", [])),
                    "legal_areas": list(set([doc.get('legal_area', 'общо право') for doc in vks_results])),
                    "found_exact_match": analysis.get('found_exact_match', False),
                    "ai_confidence": analysis.get('ai_confidence', 'medium')
                }
            )
        
        return response
        
    except Exception as e:
        logger.error(f"VKS search error: {e}")
        
        return SearchResponse(
            query=request.query,
            results=[{"content": f"❌ Грешка при търсене в ВКС: {str(e)}"}],
            total_results=0,
            search_time=time.time() - start_time if 'start_time' in locals() else 0.0,
            status="error",
            message=f"Грешка при търсене в ВКС: {str(e)}"
        )

def format_enhanced_vks_results(query: str, analysis: Dict[str, Any]) -> str:
    """
    Format enhanced VKS results with GPT-4o-mini analysis and fallback options.
    """
    if analysis.get('found_exact_match'):
        # Exact match found - show success format
        formatted_result = f"✅ **Намерена е точна информация за запитването: '{query}'**\n\n"
        
        # Add AI analysis
        formatted_result += f"{analysis.get('analysis', '')}\n\n"
        
        # Add best documents with links
        best_docs = analysis.get('best_documents', [])
        if best_docs:
            formatted_result += "**📋 Релевантни решения на ВКС:**\n\n"
            for i, doc in enumerate(best_docs, 1):
                formatted_result += f"**{i}. {doc.get('title', 'Решение на ВКС')}**\n"
                formatted_result += f"📄 {doc.get('document_type', 'неизвестен').title()}\n"
                formatted_result += f"⚖️ {doc.get('legal_area', 'неизвестна област')}\n"
                formatted_result += f"🎯 Релевантност: {doc.get('relevance_score', 0):.0%}\n"
                formatted_result += f"📝 {doc.get('body', 'Няма налично съдържание')}\n"
                
                if doc.get('href') and doc.get('href') != 'No URL':
                    formatted_result += f"🔗 [Виж решението]({doc['href']})\n"
                
                formatted_result += "\n"
            
        formatted_result += f"🏛️ **Източник:** Върховен касационен съд на България\n"
        
    else:
        # No exact match - show alternatives and fallback options
        formatted_result = f"⚠️ **Не е намерена точна информация за: '{query}'**\n\n"
        
        best_docs = analysis.get('best_documents', [])
        if best_docs:
            formatted_result += "**📋 Най-близки резултати от ВКС:**\n\n"
            for i, doc in enumerate(best_docs, 1):
                formatted_result += f"**{i}. {doc.get('title', 'Решение на ВКС')}**\n"
                formatted_result += f"📄 {doc.get('document_type', 'неизвестен').title()}\n"
                formatted_result += f"⚖️ {doc.get('legal_area', 'неизвестна област')}\n"
                formatted_result += f"🎯 Релевантност: {doc.get('relevance_score', 0):.0%}\n"
                formatted_result += f"📝 {doc.get('body', 'Няма налично съдържание')[:200]}...\n"
                
                if doc.get('href') and doc.get('href') != 'No URL':
                    formatted_result += f"🔗 [Виж решението]({doc['href']})\n"
                
                formatted_result += "\n"
        
        # Add fallback options
        fallback_options = analysis.get('fallback_options', [])
        if fallback_options:
            formatted_result += "**🔄 Предложения за подобряване на търсенето:**\n"
            for option in fallback_options:
                formatted_result += f"• {option}\n"
            formatted_result += "\n"
        
        # Add dig deeper options
        dig_deeper = analysis.get('dig_deeper_options', [])
        if dig_deeper:
            formatted_result += "**🔍 Опции за по-задълбочено търсене:**\n"
            for option in dig_deeper:
                formatted_result += f"• {option}\n"
            formatted_result += "\n"
        
        formatted_result += "💡 **Съвет:** Опитайте с по-общи или по-специфични термини\n"
    
    return formatted_result

def format_no_vks_results(query: str) -> str:
    """Format response when no VKS results are found."""
    return f"""❌ **Няма намерени решения от ВКС за: '{query}'**

**🔄 Възможни причини:**
• Твърде специфични термини
• Правописни грешки
• Използвани термини, които не се срещат в решенията на ВКС

**💡 Препоръки:**
• Опитайте с по-общи правни термини
• Използвайте синоними (напр. "договор" вместо "споразумение")
• Търсете с основни правни понятия
• Проверете правописа на българските думи

**🔍 Алтернативи:**
• Използвайте методологията "Напредна" за търсене в повече правни бази
• Търсете в други правни източници
• Консултирайте се с правен експерт

🏛️ **Източник:** Върховен касационен съд на България"""

def format_vks_results(query: str, vks_results: List[Dict], analysis: Dict[str, Any]) -> str:
    """Legacy format function - redirects to enhanced version"""
    return format_enhanced_vks_results(query, analysis)

if __name__ == "__main__":
    import uvicorn
    
    # Create necessary directories
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 