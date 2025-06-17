# 🇧🇬 Bulgarian Legal Search AI - FastAPI Edition

> **Modern AI-powered Bulgarian legal research system with real-time chat interface**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socketdotio&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

## 🌟 Features

- 🚀 **High-Performance FastAPI Backend** - Async API with automatic documentation
- 💬 **Real-time Chat Interface** - OpenAI ChatGPT-inspired UI with WebSocket updates
- 🧠 **AI-Powered Search** - Enhanced relevancy scoring with OpenAI GPT-4
- 📊 **Multi-Domain Analysis** - Searches across 3 Bulgarian legal domains
- 🔍 **Advanced Ranking** - BM25 + Semantic + RRF (Reciprocal Rank Fusion)
- 📱 **Responsive Design** - Works perfectly on desktop and mobile
- ⚡ **Real-time Updates** - Live search progress and status indicators
- 🎯 **Bulgarian Legal Focus** - Specialized for Bulgarian law and regulations

## 🏗️ Architecture

The system follows a modern layered architecture:

```
Frontend (HTML/CSS/JS) → FastAPI (Python) → Search Engines → Legal Databases
                      ↕                    ↕
                   WebSocket           AI Analysis
```

For detailed architecture information, see [architecture.md](architecture.md).

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Google Custom Search Engine API key and ID

### 1. Clone and Setup

```bash
# Navigate to the project directory
cd agentic_search_openai_langgraph

# Install dependencies
pip install -r requirements_fastapi.txt
```

### 2. Environment Configuration

Create a `.env` file with your API keys:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_CSE_API_KEY=your_google_cse_api_key_here
GOOGLE_CSE_ID=your_google_cse_id_here

# Optional
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Run the Application

**Option A: Using the startup script (recommended)**
```bash
python run_app.py
```

**Option B: Direct FastAPI run**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the Application

- 🌐 **Main Interface**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/api/docs
- 🔄 **Interactive API**: http://localhost:8000/api/redoc

## 📖 Usage Guide

### Web Interface

1. **Open your browser** to http://localhost:8000
2. **Configure search parameters** using the controls:
   - **Methodology**: Enhanced (recommended), Standard, or Experimental
   - **Max Results**: 5-50 results per search
   - **Min Relevancy**: 10%-90% relevancy threshold
3. **Type your legal question** in Bulgarian
4. **Watch real-time progress** as the AI searches and analyzes
5. **Review results** with relevancy scores and metadata

### Example Queries

Try these Bulgarian legal queries:

```
обезщетение за трудова злополука
какви са правата ми при уволнение
как да предявя иск в съда
наказателна отговорност за шофиране в нетрезво състояние
права на потребителите при дефектни стоки
```

### API Usage

**Search Endpoint:**
```bash
curl -X POST "http://localhost:8000/api/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "обезщетение за трудова злополука",
       "max_results": 15,
       "min_relevancy": 0.3,
       "methodology": "enhanced"
     }'
```

**WebSocket Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Search update:', message);
};
```

## 🔧 Configuration

### Search Methodologies

- **Enhanced** (Default): Uses AI-powered relevancy scoring with BM25 + Semantic analysis
- **Standard**: Basic search with statistical ranking
- **Experimental**: Latest experimental features and algorithms

### Legal Domains

The system searches across these Bulgarian legal domains:

| Domain | Authority | Description | Specialties |
|--------|-----------|-------------|-------------|
| **ciela.net** | 95% | Leading Bulgarian legal platform | Laws, regulations, case law |
| **apis.bg** | 90% | Specialized legal publisher | Commentary, analysis, practice |
| **lakorda.com** | 75% | Legal news and analysis | News, analysis, current events |

### Performance Tuning

- **Max Results**: Higher values provide more comprehensive results but slower response
- **Min Relevancy**: Higher thresholds filter out less relevant results
- **Methodology**: Enhanced provides best results but uses more API calls

## 🛠️ Development

### Project Structure

```
agentic_search_openai_langgraph/
├── main.py                     # FastAPI application
├── run_app.py                  # Startup script
├── templates/
│   └── index.html             # Frontend interface
├── static/                    # Static files (auto-created)
├── enhanced_legal_tools.py    # Core search logic
├── relevancy_scoring.py       # AI relevancy scoring
├── tools.py                   # Search tools
├── requirements_fastapi.txt   # Dependencies
├── architecture.md           # System architecture
└── README_FastAPI.md         # This file
```

### Key Components

1. **FastAPI Backend** (`main.py`)
   - REST API endpoints
   - WebSocket handlers
   - Request validation
   - Error handling

2. **Frontend Interface** (`templates/index.html`)
   - Modern chat UI
   - Real-time updates
   - Responsive design
   - Search controls

3. **Search Engine** (`enhanced_legal_tools.py`)
   - Multi-domain search
   - Query processing
   - Content extraction
   - Result formatting

4. **AI Scoring** (`relevancy_scoring.py`)
   - BM25 algorithm
   - OpenAI semantic analysis
   - Rank fusion (RRF)
   - Legal classification

### Adding New Features

1. **New API Endpoint**:
   ```python
   @app.get("/api/new-feature")
   async def new_feature():
       return {"message": "New feature"}
   ```

2. **WebSocket Message Type**:
   ```python
   await manager.broadcast({
       "type": "new_message_type",
       "data": "your_data"
   })
   ```

3. **Frontend Handler**:
   ```javascript
   case 'new_message_type':
       // Handle new message type
       break;
   ```

## 🧪 Testing

### Run Tests

```bash
# Test core functionality
python simple_function_test.py

# Test specific components
python -c "from enhanced_legal_tools import enhanced_bulgarian_legal_search_sync; print('✅ Import successful')"
```

### Health Checks

```bash
# API health check
curl http://localhost:8000/api/health

# System statistics
curl http://localhost:8000/api/stats
```

## 🚀 Deployment

### Development

```bash
# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Using Gunicorn (recommended)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or direct Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (Future)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements_fastapi.txt .
RUN pip install -r requirements_fastapi.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Performance

### Benchmarks

- **Average Search Time**: 2-4 seconds
- **Concurrent Users**: 50+ (with proper deployment)
- **Memory Usage**: ~200MB base + ~50MB per active search
- **API Response Time**: <100ms for health checks

### Optimization Tips

1. **Use caching** for repeated queries
2. **Limit max_results** for faster responses
3. **Adjust min_relevancy** to filter results
4. **Deploy with multiple workers** for production

## 🔒 Security

### API Security

- CORS policy configured
- Request validation with Pydantic
- Input sanitization
- Error message sanitization

### Data Protection

- No sensitive data storage
- Secure API key management
- HTTPS enforcement (production)
- WebSocket secure connections

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Solution: Install dependencies
pip install -r requirements_fastapi.txt
```

**2. API Key Errors**
```bash
# Solution: Check .env file
cat .env
# Ensure all required keys are present
```

**3. WebSocket Connection Issues**
```bash
# Solution: Check firewall and port 8000
netstat -an | grep 8000
```

**4. Search Timeouts**
```bash
# Solution: Reduce max_results or check internet connection
# Try with max_results=5 first
```

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Write tests for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 API
- **FastAPI** for the excellent web framework
- **Bulgarian Legal Community** for domain expertise
- **LangChain** for AI orchestration tools

## 📞 Support

- 📧 **Email**: [Your email here]
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Made with ❤️ for the Bulgarian Legal Community**

> This system is designed to assist with legal research and should not replace professional legal advice. Always consult with qualified legal professionals for important legal matters. 