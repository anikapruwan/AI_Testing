# QA Search Bot

RAG-powered QA Copilot with Groq and OpenCode integration for VWO testing.

## Features

- **Chat with your data**: Ask questions about test cases, code, and documentation
- **Hybrid LLM support**: Use Groq (fast) or OpenCode (high quality)
- **Multiple data sources**: CSV test cases, PDF docs, GitHub code
- **Advanced RAG**: Hybrid search with semantic + keyword matching
- **Settings UI**: Configure API keys and model selection from frontend

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Vector DB | ChromaDB |
| Embeddings | Sentence Transformers |
| LLMs | Groq (Llama3) + OpenCode (GPT-4) |
| Frontend | React + Vite |

## Quick Start

### 1. Clone and setup

```bash
cd RAG_Project_QA_Copilot
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure .env
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Backend

```bash
uvicorn app.main:app --reload
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Open Browser

Visit `http://localhost:5173`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/with-keys` | POST | Main chat endpoint |
| `/api/search` | POST | Vector search |
| `/api/settings` | GET/POST | Settings management |
| `/api/models` | GET | List available models |
| `/api/ingest/csv` | POST | Ingest CSV test cases |
| `/api/ingest/pdf` | POST | Ingest PDF docs |
| `/api/ingest/github` | POST | Ingest GitHub code |
| `/api/rebuild-index` | POST | Rebuild vector index |

## Data Sources

| Source | Default Path |
|--------|-------------|
| CSV Test Cases | `/Users/.../RAG:Advance_RAG/data/uploads/testcases_vwo.csv` |
| PDF Docs | `/Users/.../Live_Class/.../Product Requirements Document_VWO.pdf` |
| GitHub Repo | `https://github.com/PramodDutta/AdvanceSeleniumFrameworkTTA` |

## Available Models

### Groq
- `llama-3.3-70b-versatile` (Recommended)
- `llama-3.1-8b-instant`
- `mixtral-8x7b-32768`

### OpenCode
- `gpt-4o` (Best Quality)
- `gpt-4o-mini` (Cheap)
- `gpt-4-turbo`

## Docker Deployment

```bash
# Build and run
docker-compose up --build
```

## Project Structure

```
QA_Search_Bot/
├── backend/
│   ├── app/
│   │   ├── api/        # API endpoints
│   │   ├── models/     # Pydantic models
│   │   ├── services/    # Business logic
│   │   ├── config.py   # Configuration
│   │   └── main.py    # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── api/        # API calls
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Usage

1. Open the app in your browser
2. Click **Settings** to configure API keys
3. Select a model from the dropdown
4. Start chatting with your test data!