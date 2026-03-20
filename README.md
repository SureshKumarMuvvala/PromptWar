# 🚑 Emergency Health Assistant

A production-ready AI-powered emergency medical triage system that accepts **multimodal input** (text, voice, image), performs structured assessment via **Google Gemini**, validates against medical protocols using **FAISS RAG**, and generates real-world emergency actions.

## Features

- **Multimodal Input** — Text description, voice recording (WebRTC), and image upload (drag & drop)
- **AI-Powered Triage** — Google Gemini 2.0 Flash for understanding emergencies across all modalities
- **Structured Output** — Converts unstructured input into validated JSON with ICD-10 codes, severity levels, and triage colors
- **RAG Validation** — FAISS-backed retrieval against 15+ emergency protocols to cross-check and correct assessments
- **Real-World Actions** — Generates prioritized actions: ambulance dispatch, first-aid instructions, hospital suggestions
- **Cloud-Native** — Dockerized, deployable on Google Cloud Run with auto-scaling

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Google Gemini 2.0 Flash |
| Backend | FastAPI (Python 3.11) |
| Frontend | React 18 (Vite) |
| Vector DB | FAISS (CPU) |
| Embeddings | Gemini text-embedding-004 |
| Containerization | Docker + Docker Compose |
| Deployment | Google Cloud Run |
| CI/CD | Cloud Build / GitHub Actions |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Google Gemini API key ([Get one free](https://aistudio.google.com/apikey))

### 1. Clone & Configure

```bash
git clone <repo-url> && cd emergency-health-assistant

# Backend
cp backend/.env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Run Locally (Development)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 4. Build FAISS Index

```bash
cd backend
python -m app.rag.indexer
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/emergency/assess` | Multimodal triage assessment |
| `POST` | `/api/v1/emergency/validate` | RAG-backed clinical validation |
| `POST` | `/api/v1/emergency/actions` | Generate emergency actions |
| `GET` | `/api/v1/hospitals?lat=&lng=` | Nearby hospital lookup |
| `GET` | `/api/v1/status` | Health check |

## Deploy to Cloud Run

```bash
# Using Cloud Build
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_GEMINI_API_KEY=your-key
```

## Project Structure

```
emergency-health-assistant/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── models/    # Pydantic schemas
│   │   ├── services/  # Gemini, ingestion, structuring, actions
│   │   ├── rag/       # FAISS indexer, retriever, knowledge base
│   │   └── utils/     # Logger, exceptions
│   ├── tests/
│   └── Dockerfile
├── frontend/          # React SPA
│   ├── src/
│   │   ├── components/  # TextInput, VoiceRecorder, ImageUploader, ActionPanel
│   │   └── services/    # API client
│   └── Dockerfile
├── docker-compose.yml
├── cloudbuild.yaml
└── README.md
```

## License

MIT
