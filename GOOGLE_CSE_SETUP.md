# Google Custom Search Engine (CSE) Setup Guide

This guide will help you set up Google Custom Search Engine to solve the DuckDuckGo rate limiting issues and enable powerful domain-specific searching for Bulgarian legal content.

## Why Google CSE?

✅ **Higher rate limits** - 100 free queries/day, then $5 per 1000 queries  
✅ **Domain-specific search** - Target specific legal domains like lex.bg, vks.bg  
✅ **Bulgarian language support** - Built-in language and country targeting  
✅ **Better reliability** - No rate limiting like DuckDuckGo  
✅ **Advanced filtering** - Site restriction, date filtering, content types  

## Step 1: Create a Google Custom Search Engine

1. **Go to Google Custom Search**: https://cse.google.com/
2. **Click "Add"** to create a new search engine
3. **Configure your search engine**:
   - **Sites to search**: Leave blank or add `*.bg` for Bulgarian sites
   - **Language**: Bulgarian
   - **Name**: "Bulgarian Legal Research Engine"
   - **Search engine keywords**: law, legal, българско право

4. **Enable "Search the entire web"**:
   - Go to **Setup** → **Basics**
   - Turn **ON** "Search the entire web"
   - Click **Update**

5. **Get your Search Engine ID**:
   - Go to **Setup** → **Basics**
   - Copy the **Search engine ID** (looks like: `012345678901234567890:abcdefghijk`)

## Step 2: Get Google API Key

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create or select a project**
3. **Enable the Custom Search API**:
   - Go to **APIs & Services** → **Library**
   - Search for "Custom Search API"
   - Click **Enable**

4. **Create API Key**:
   - Go to **APIs & Services** → **Credentials**
   - Click **+ CREATE CREDENTIALS** → **API key**
   - Copy your API key (looks like: `AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q`)

## Step 3: Configure Environment Variables

Add these lines to your `.env` file:

```bash
# Google Custom Search Engine Configuration
GOOGLE_CSE_API_KEY=AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q
GOOGLE_CSE_ID=012345678901234567890:abcdefghijk

# Your existing API keys
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here  # Optional fallback
```

## Step 4: Install Dependencies

```bash
pip install google-api-python-client>=2.0.0
```

## Step 5: Test the Integration

Create a test file `test_google_cse.py`:

```python
import os
from dotenv import load_dotenv
from tools import google_cse_search, google_domain_search

load_dotenv()

# Test general search
print("=== Testing General Search ===")
results = google_cse_search("обезщетение за телесна повреда")
print(f"Found {len(results)} results")
for i, result in enumerate(results[:3]):
    print(f"{i+1}. {result['title']}")
    print(f"   {result['href']}")

# Test domain-specific search
print("\n=== Testing Domain Search ===")
domain_results = google_domain_search("съдебна практика", domains=['lex.bg', 'vks.bg'])
print(f"Found {len(domain_results)} domain results")
for i, result in enumerate(domain_results[:3]):
    print(f"{i+1}. {result['title']} - {result['source_domain']}")
```

Run the test:
```bash
python test_google_cse.py
```

## Available Search Functions

### 1. **google_cse_search()** - Primary search function
```python
# Basic search
results = google_cse_search("българско право")

# Domain-specific search
results = google_cse_search("решение", site_search="vks.bg")

# With language/country targeting
results = google_cse_search("закон", country="bg", language="lang_bg")
```

### 2. **google_domain_search()** - Multi-domain search
```python
# Search specific domains
results = google_domain_search("обезщетение", domains=['lex.bg', 'vks.bg'])

# Search all Bulgarian legal domains (default)
results = google_domain_search("съдебна практика")
```

### 3. **Enhanced Legal Tools** - Use Google CSE
```python
# Bulgarian legal search with CSE
from enhanced_legal_tools import bulgarian_legal_search
results = bulgarian_legal_search("счупване на ръка", specific_domain="lex_bg")

# Legal precedent search
from enhanced_legal_tools import legal_precedent_search
precedents = legal_precedent_search("обезщетение", court_level="ВКС")
```

## Domain Targeting

The system supports these Bulgarian legal domains:

| Domain Key | URL | Description |
|------------|-----|-------------|
| `lex_bg` | lex.bg | LexBG - Comprehensive Bulgarian legal database |
| `vks_bg` | vks.bg | Supreme Court of Cassation |
| `vss_bg` | vss.bg | Supreme Administrative Court |
| `justice_bg` | justice.bg | Ministry of Justice |
| `parliament_bg` | parliament.bg | National Assembly |
| `cpc_bg` | cpc.bg | Commission for Personal Data Protection |
| `dv_bg` | dv.bg | State Gazette |

## Rate Limiting & Costs

- **Free tier**: 100 queries per day
- **Paid tier**: $5 per 1,000 queries (up to 10,000/day max)
- **Rate limiting**: Built-in delays between domain searches
- **Fallback**: Automatic fallback to DuckDuckGo if CSE fails

## Troubleshooting

### Common Issues:

1. **"Google CSE not configured"**
   - Check your `.env` file has the correct API key and Search Engine ID
   - Ensure no extra spaces or quotes around the values

2. **"API key invalid"**
   - Verify the API key is correct
   - Check that Custom Search API is enabled in Google Cloud Console

3. **"Search engine not found"**
   - Verify the Search Engine ID is correct
   - Ensure the search engine exists and is public

4. **No results returned**
   - System automatically falls back to DuckDuckGo
   - Check logs for specific error messages

### Enable Debug Logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Configuration

### Site-Restricted Search Engine (No daily limit)
For unlimited queries on specific domains, create a Site-Restricted CSE:

1. Create a new CSE with only specific sites (≤10 domains)
2. Add: `lex.bg`, `vks.bg`, `vss.bg`, `justice.bg`, etc.
3. Do NOT enable "Search the entire web"
4. Use the Site Restricted API endpoint

**Note**: Site-restricted API will be discontinued January 8, 2025. Migrate to Vertex AI Search.

## Integration Status

✅ **Primary search**: Google CSE with DuckDuckGo fallback  
✅ **Domain targeting**: Specific Bulgarian legal domains  
✅ **Language support**: Bulgarian language and country targeting  
✅ **Rate limiting**: Intelligent delays and error handling  
✅ **Legal tools**: Enhanced Bulgarian legal search capabilities  
✅ **Citation extraction**: Bulgarian legal citation patterns  
✅ **Multi-provider**: CSE → Tavily → DuckDuckGo fallback chain  

The system now prioritizes Google CSE for better reliability and rate limits, with automatic fallbacks to ensure search always works! 