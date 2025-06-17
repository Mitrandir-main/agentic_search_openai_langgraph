# 🏗️ Bulgarian Legal Search AI - System Architecture

## 📋 Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Component Breakdown](#component-breakdown)
- [Data Flow](#data-flow)
- [API Documentation](#api-documentation)
- [Frontend Architecture](#frontend-architecture)
- [Real-time Communication](#real-time-communication)
- [Search Engine Components](#search-engine-components)
- [Deployment Architecture](#deployment-architecture)
- [Performance Considerations](#performance-considerations)
- [Security Measures](#security-measures)

## 🔭 Overview

The Bulgarian Legal Search AI is a modern, AI-powered legal research system built with FastAPI and featuring a real-time chat interface. The system provides advanced search capabilities across Bulgarian legal databases with intelligent ranking, relevancy scoring, and multi-domain analysis.

### Key Features
- 🚀 **FastAPI Backend** - High-performance, async API
- 💬 **Real-time Chat Interface** - WebSocket-powered live updates
- 🧠 **AI-Powered Search** - Enhanced relevancy scoring with OpenAI
- 📊 **Multi-Domain Analysis** - Searches across 3 legal domains
- 🔍 **Advanced Filtering** - BM25 + Semantic + RRF ranking
- 📱 **Responsive Design** - Modern OpenAI-like interface

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Modern Web Interface (HTML/CSS/JS)                            │
│  ├── Real-time Chat UI                                         │
│  ├── Search Controls                                           │
│  ├── Progress Indicators                                       │
│  └── WebSocket Client                                          │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Application (main.py)                                 │
│  ├── HTTP REST Endpoints                                       │
│  ├── WebSocket Handlers                                        │
│  ├── CORS Middleware                                           │
│  ├── Request Validation (Pydantic)                             │
│  └── Static File Serving                                       │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  Enhanced Legal Tools (enhanced_legal_tools.py)                │
│  ├── Search Orchestration                                      │
│  ├── Query Processing & Expansion                              │
│  ├── Multi-Domain Coordination                                 │
│  ├── Content Extraction                                        │
│  └── Result Formatting                                         │
│                                                                 │
│  Relevancy Scoring (relevancy_scoring.py)                      │
│  ├── BM25 Algorithm                                            │
│  ├── Semantic Analysis (OpenAI)                                │
│  ├── RRF (Reciprocal Rank Fusion)                              │
│  └── Legal Content Classification                              │
│                                                                 │
│  Search Tools (tools.py)                                       │
│  ├── Google CSE Integration                                    │
│  ├── DuckDuckGo Search                                         │
│  ├── Content Processing                                        │
│  └── Citation Extraction                                       │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  External APIs & Services                                      │
│  ├── Google Custom Search Engine                               │
│  ├── DuckDuckGo Search API                                     │
│  ├── OpenAI API (GPT-4)                                        │
│  └── Legal Domain Scrapers                                     │
│                                                                 │
│  Bulgarian Legal Domains                                       │
│  ├── ciela.net (Authority: 95%)                                │
│  ├── apis.bg (Authority: 90%)                                  │
│  └── lakorda.com (Authority: 75%)                              │
└─────────────────────────────────────────────────────────────────┘
```

## 🧩 Component Breakdown

### 1. **FastAPI Backend (main.py)**
- **Purpose**: HTTP API server and WebSocket handler
- **Responsibilities**:
  - Request routing and validation
  - Real-time communication management
  - Static file serving
  - Error handling and logging
  - CORS policy enforcement

### 2. **Enhanced Legal Tools (enhanced_legal_tools.py)**
- **Purpose**: Core search intelligence and orchestration
- **Key Functions**:
  - `enhanced_bulgarian_legal_search_sync()` - Main search coordinator
  - `bulgarian_legal_search()` - Domain-specific search
  - `legal_citation_extractor()` - Extract legal references
  - `legal_document_analyzer()` - Document analysis

### 3. **Relevancy Scoring (relevancy_scoring.py)**
- **Purpose**: Advanced ranking and relevancy calculation
- **Components**:
  - **BM25 Scorer**: Statistical relevance calculation
  - **Semantic Analyzer**: OpenAI-powered content understanding
  - **RRF Combiner**: Reciprocal Rank Fusion algorithm
  - **Legal Classifier**: Domain-specific content classification

### 4. **Search Tools (tools.py)**
- **Purpose**: External search service integration
- **Tools**:
  - Google Custom Search Engine wrapper
  - DuckDuckGo search integration
  - Web content extraction and processing
  - Multi-domain search coordination

### 5. **Frontend Interface (templates/index.html)**
- **Purpose**: Modern chat-based user interface
- **Features**:
  - Real-time chat interface
  - Search parameter controls
  - Progress indicators and status updates
  - Responsive design (mobile-friendly)
  - WebSocket integration for live updates

## 🌊 Data Flow

### Search Request Flow
```
1. User Input
   └── Frontend validates and sends request

2. API Reception
   └── FastAPI receives POST /api/search
   └── Pydantic validates request model
   └── WebSocket broadcasts search_start

3. Search Processing
   └── enhanced_bulgarian_legal_search_sync()
   └── Query preprocessing and expansion
   └── Multi-domain parallel search
   └── Content extraction and processing

4. Relevancy Analysis
   └── BM25 statistical scoring
   └── OpenAI semantic analysis
   └── RRF rank fusion
   └── Legal classification

5. Response Formation
   └── Results formatting and aggregation
   └── Metadata compilation
   └── Performance metrics calculation

6. Client Delivery
   └── HTTP response with structured data
   └── WebSocket broadcasts search_complete
   └── Frontend renders results
```

### Real-time Communication Flow
```
WebSocket Connection
├── Client connects to /ws
├── Connection stored in ConnectionManager
├── Real-time status updates:
│   ├── search_start
│   ├── search_progress (future enhancement)
│   ├── search_complete
│   └── search_error
└── Automatic reconnection on disconnect
```

## 📡 API Documentation

### Core Endpoints

#### `POST /api/search`
**Purpose**: Execute legal search query
```json
{
  "query": "обезщетение за трудова злополука",
  "max_results": 15,
  "min_relevancy": 0.3,
  "methodology": "enhanced",
  "domains": ["ciela.net", "apis.bg"]
}
```

**Response**:
```json
{
  "query": "обезщетение за трудова злополука",
  "results": "formatted search results...",
  "metadata": {
    "max_results": 15,
    "min_relevancy": 0.3,
    "methodology": "enhanced",
    "domains_searched": ["ciela.net", "apis.bg", "lakorda.com"]
  },
  "processing_time": 2.34,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /api/health`
**Purpose**: System health check
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "2.0.0"
}
```

#### `GET /api/stats`
**Purpose**: System statistics
```json
{
  "active_connections": 5,
  "available_domains": ["ciela.net", "apis.bg", "lakorda.com"],
  "search_methodologies": ["enhanced", "standard", "experimental"],
  "system_status": "operational"
}
```

#### `GET /api/domains`
**Purpose**: Available legal domains information
```json
{
  "ciela.net": {
    "authority": 0.95,
    "description": "Водеща българска правна платформа",
    "pages": "19,300+",
    "specialties": ["laws", "regulations", "case_law"]
  }
}
```

#### `WebSocket /ws`
**Purpose**: Real-time communication channel
- Connection management
- Search progress updates
- System status notifications
- Client-server heartbeat

## 🎨 Frontend Architecture

### Modern Chat Interface Design
- **Design Philosophy**: OpenAI ChatGPT-inspired interface
- **Color Scheme**: Professional blue gradients with white accents
- **Typography**: Inter font family for modern readability
- **Layout**: Responsive flexbox design

### Key UI Components
1. **Chat Header**: Status indicator and system branding
2. **Message Area**: Scrollable chat history with user/assistant messages
3. **Search Controls**: Advanced search parameter configuration
4. **Input Area**: Multi-line textarea with send button
5. **Status Indicators**: Connection status, typing indicators, progress bars

### Real-time Features
- **WebSocket Integration**: Live connection status and updates
- **Typing Indicators**: Visual feedback during search processing
- **Progress Bars**: Search operation progress visualization
- **Auto-scroll**: Automatic message area scrolling
- **Responsive Design**: Mobile-friendly adaptive layout

## ⚡ Real-time Communication

### WebSocket Implementation
```python
class ConnectionManager:
    - Manages active WebSocket connections
    - Handles connection lifecycle
    - Broadcasts messages to all clients
    - Provides personal messaging capabilities
```

### Message Types
- `search_start`: Search operation initiated
- `search_complete`: Search finished successfully
- `search_error`: Search encountered error
- `ping/pong`: Connection health checks

### Auto-reconnection
- Client automatically reconnects on disconnect
- 3-second reconnection delay
- Connection status indicator updates

## 🔍 Search Engine Components

### Multi-Domain Search Strategy
1. **Primary Domains** (Bulgarian Legal):
   - **ciela.net**: Authority 95% - Comprehensive legal database
   - **apis.bg**: Authority 90% - Legal commentary and analysis
   - **lakorda.com**: Authority 75% - Legal news and updates

2. **Search Methods**:
   - Google Custom Search Engine (primary)
   - DuckDuckGo Search (fallback)
   - Domain-specific optimizations

### Relevancy Scoring Pipeline
1. **BM25 Statistical Scoring**: Term frequency analysis
2. **Semantic Analysis**: OpenAI-powered content understanding
3. **RRF Combination**: Reciprocal Rank Fusion for optimal ranking
4. **Legal Classification**: Domain-specific content categorization

### Content Processing
- HTML content extraction
- Legal citation identification
- Bulgarian text processing
- Metadata extraction and enrichment

## 🚀 Deployment Architecture

### Development Setup
```bash
# Install dependencies
pip install -r requirements_fastapi.txt

# Create directories
mkdir -p static templates

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment
```bash
# Using Docker (recommended)
docker build -t bulgarian-legal-ai .
docker run -p 8000:8000 bulgarian-legal-ai

# Or direct deployment
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Environment Configuration
Required environment variables:
- `OPENAI_API_KEY`: OpenAI API access
- `GOOGLE_CSE_API_KEY`: Google Custom Search Engine
- `GOOGLE_CSE_ID`: Search Engine ID
- `TAVILY_API_KEY`: Alternative search service (optional)

## ⚡ Performance Considerations

### Async Operations
- FastAPI async request handling
- Concurrent search operations across domains
- Non-blocking WebSocket communications
- Parallel content processing

### Caching Strategy
- Search result caching (planned)
- Static file caching
- Browser-side caching headers
- WebSocket connection pooling

### Optimization Techniques
- Request/response compression
- Efficient HTML parsing
- Minimal DOM updates on frontend
- Connection reuse for external APIs

## 🔒 Security Measures

### API Security
- CORS policy configuration
- Request validation with Pydantic
- Rate limiting (future enhancement)
- Input sanitization

### Data Protection
- No sensitive data storage
- Secure API key management
- HTTPS enforcement (in production)
- WebSocket secure connections

### Content Security
- XSS prevention in HTML rendering
- Safe content extraction from external sources
- Legal citation validation
- Error message sanitization

## 📊 Monitoring and Logging

### System Monitoring
- Health check endpoints
- Connection status tracking
- Performance metrics collection
- Error rate monitoring

### Logging Strategy
- Structured logging with timestamps
- Request/response logging
- Error stack traces
- WebSocket connection tracking

## 🔄 Future Enhancements

### Planned Features
1. **Advanced Analytics**: Search pattern analysis
2. **User Authentication**: Personal search history
3. **Advanced Caching**: Redis-based result caching
4. **AI Summarization**: Automatic legal summary generation
5. **Multi-language Support**: English interface option
6. **Mobile App**: Native mobile application
7. **API Rate Limiting**: Request throttling
8. **Advanced Search Filters**: Date ranges, document types
9. **Export Functionality**: PDF/Word result export
10. **Legal Citation Verification**: Automatic citation validation

---

## 🛠️ Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | HTML5, CSS3, JavaScript | Modern chat interface |
| **Backend** | FastAPI, Python 3.9+ | High-performance async API |
| **Real-time** | WebSockets | Live communication |
| **Search** | Google CSE, DuckDuckGo | External search integration |
| **AI/ML** | OpenAI GPT-4, scikit-learn | Relevancy scoring |
| **Web Scraping** | BeautifulSoup, requests | Content extraction |
| **Deployment** | Uvicorn, Docker | Production deployment |
| **Templates** | Jinja2 | Server-side rendering |

This architecture provides a robust, scalable, and maintainable foundation for the Bulgarian Legal Search AI system, with clear separation of concerns and modern web development best practices. 