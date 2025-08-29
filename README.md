# Mind Mesh: Advanced Retrieval-Augmented Generation API

<div align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.109.0-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/LangChain-0.1.9-teal" alt="LangChain">
</div>


## 🚀 Overview

**Mind Mesh** is a production-ready Retrieval-Augmented Generation system built with FastAPI and Anthropic's Claude models. It enhances Large Language Model (LLM) outputs with relevant context from your own data sources, enabling more accurate, contextually-aware, and trustworthy AI responses.

The system allows for:

- 📄 Document ingestion (PDF, DOCX, TXT, MD)
- 🌐 Web scraping and crawling
- 💬 Context-enriched conversations
- 🔍 Semantic search across your knowledge base
- 📊 System analytics and monitoring

## 🏗️ Architecture

The backend follows a modular architecture:

```
backend/
├── src/
│   ├── api/            # FastAPI routes and API definition
│   │   ├── models/     # Pydantic models for request/response
│   │   └── routes/     # API endpoint implementations
│   ├── core/           # Core RAG functionality
│   │   ├── config.py   # Configuration management
│   │   ├── embeddings.py # Embedding models
│   │   ├── ingestion.py  # Document processing pipeline
│   │   ├── retrieval.py  # Context retrieval logic
│   │   └── vectorstore.py # Vector database interface
│   └── utils/          # Utility functions
│       ├── jobs.py     # Background job processing
│       ├── parser.py   # Document parsing
│       └── scraper.py  # Web scraping utilities
└── tests/             # Test suite
```

## ✨ Features

### Document Processing

- Multi-format document parsing (PDF, DOCX, TXT, MD)
- Intelligent chunking strategies
- Metadata extraction and preservation
- Background processing with status tracking

### Web Content Ingestion

- Single URL scraping
- Full website crawling with depth control
- HTML-to-markdown conversion
- Content cleaning and extraction

### Vector Storage

- Pinecone vector database for efficient similarity search
- Metadata filtering and hybrid search capabilities
- Google Gemini embedding models for high-quality text representations
- Optimized for speed and accuracy

### Retrieval System

- Context-aware retrieval
- Relevance ranking
- Re-ranking based on user queries
- Citation and source tracking

### LLM Integration

- Seamless integration with Google Gemini models
- Configurable generation parameters
- Prompt engineering utilities
- Token usage optimization

## 🛠️ Installation

### Prerequisites

- Python 3.11
- [Poetry](https://python-poetry.org/) (recommended) or pip
- Vector database (FAISS included by default)

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/mind-mesh.git
   cd mind-mesh
   ```

2. Set up a virtual environment:

   ```bash
   # With Poetry
   poetry install

   # With venv and pip
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables (create a .env file):

   ```env
   # API Keys
   PINECONE_API_KEY=your_pinecone_api_key
   GOOGLE_API_KEY=your_google_api_key
   FIRECRAWL_API_KEY=your_firecrawl_api_key

   # Pinecone Settings
   PINECONE_INDEX_NAME=rag-system
   PINECONE_ENVIRONMENT=us-east1-gcp

   # API Settings
   API_HOST=localhost
   API_PORT=8000
   STREAMLIT_PORT=8501

   # Document Processing
   CHUNK_SIZE=512
   CHUNK_OVERLAP=50
   TOP_K_RESULTS=5
   ```

4. Run the API:

   ```bash
   # Development
   uvicorn backend.src.api.main:app --reload --port 8000

   # Production
   uvicorn backend.src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

## 🔄 API Endpoints

### Health Check

```http
GET /api/v1/health
```

### Document Management

```http
# Upload a document
POST /api/v1/ingest/document
Content-Type: multipart/form-data

# Get list of documents
GET /api/v1/documents

# Get document details
GET /api/v1/documents/{document_id}

# Delete document
DELETE /api/v1/documents/{document_id}
```

### Web Content Ingestion

```http
# Scrape a single URL
POST /api/v1/ingest/url
Content-Type: application/json

{
  "url": "https://example.com/article",
  "options": {
    "extract_main_content": true
  }
}

# Crawl an entire website
POST /api/v1/ingest/website
Content-Type: application/json

{
  "url": "https://example.com",
  "options": {
    "max_pages": 50,
    "max_depth": 2
  }
}
```

### Index Management

```http
# List available indexes
GET /api/v1/indexes

# Create a new index
POST /api/v1/indexes
Content-Type: application/json

{
  "name": "my-knowledge-base",
  "description": "Company documentation"
}

# Delete an index
DELETE /api/v1/indexes/{index_id}
```

### Query Endpoints

```http
# Chat with documents
POST /api/v1/query/chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "What is RAG?"}
  ],
  "conversation_id": "optional-conversation-id",
  "options": {
    "temperature": 0.7,
    "use_retrieval": true,
    "retrieval_options": {
      "search_type": "similarity",
      "filters": {"source": "documentation"},
      "k": 5
    }
  }
}

# Semantic search
POST /api/v1/query/search
Content-Type: application/json

{
  "query": "advanced RAG techniques",
  "filters": {
    "document_type": ["pdf", "website"]
  },
  "limit": 10
}
```

### Job Status

```http
# Check status of a background job
GET /api/v1/jobs/{job_id}
```

## 🔧 Configuration

The system can be configured through environment variables or a `.env` file. See the [Installation](#installation) section for the main configuration options.

### Advanced Configuration

For more advanced configuration options, edit the `backend/src/core/config.py` file. This includes:

- Chunking strategies
- Retrieval parameters
- Embedding options
- Vector store settings
- LLM configurations

## 📊 System Requirements

- **Minimum**: 4GB RAM, 2 CPU cores
- **Recommended**: 8GB+ RAM, 4+ CPU cores
- **Storage**: Depends on your document volume; plan for 2-3x the size of your raw documents

## 🐳 Docker Deployment

A Dockerfile and docker-compose.yml are provided for containerized deployment:

```bash
# Build and run with Docker Compose
docker-compose up -d
```

The Docker setup includes:

- Backend API service
- Pinecone vector database connection
- Reverse proxy with rate limiting
- Auto-reload for development

## 🧪 Testing

Run the test suite to ensure everything is working correctly:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=backend

# Run specific test modules
pytest backend/tests/test_ingestion.py
```

## 🧩 Extending the System

### Adding New Document Types

Extend the parser capabilities in `backend/src/utils/parser.py`:

```python
from .base_parser import BaseParser

class MyCustomFormatParser(BaseParser):
    """Parser for custom document format"""

    def __init__(self):
        super().__init__()

    def parse(self, file_path, metadata=None):
        # Custom parsing logic
        ...
        return documents
```

Register your parser in the factory:

```python
PARSER_REGISTRY = {
    ".pdf": PDFParser,
    ".docx": DocxParser,
    ".txt": TextParser,
    ".md": MarkdownParser,
    ".mycustom": MyCustomFormatParser,
}
```

### Custom Embedding Models

Configure a custom embedding model in `backend/src/core/embeddings.py`:

```python
from langchain.embeddings import HuggingFaceEmbeddings

# Example: Using a custom HuggingFace model
custom_embeddings = HuggingFaceEmbeddings(
    model_name="your-custom-model",
    model_kwargs={"device": "cuda"},
    encode_kwargs={"normalize_embeddings": True}
)
```

### Custom Retrieval Logic

Extend the retriever in `backend/src/core/retrieval.py` to implement custom retrieval logic:

```python
class CustomRetriever(BaseRetriever):
    """Custom retrieval implementation"""

    def get_relevant_documents(self, query):
        # Custom retrieval logic
        ...
        return documents
```

## 🔒 Security Considerations

- API authentication is handled via API keys
- Rate limiting is implemented to prevent abuse
- Input validation is performed on all endpoints
- Document access can be restricted based on user permissions
- All external connections use HTTPS

## 📚 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Google](https://ai.google.dev/) for Gemini models and embeddings
- [LlamaIndex](https://www.llamaindex.ai/) for the retrieval framework
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [Firecrawl](https://firecrawl.dev/) for web scraping capabilities
- [Pinecone](https://www.pinecone.io/) for vector database
- [Streamlit](https://streamlit.io/) for the frontend framework
- All open-source contributors who made this project possible

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/yourusername">Your Name</a>
</p>

