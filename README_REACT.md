# Czech Political Advisor - React + FastAPI

Modern web application for analyzing Czech political proposals using AI.

## Architecture

- **Frontend**: Next.js 15 + React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **AI**: Google Gemini + ChromaDB + DuckDuckGo Search
- **Data**: Czech State Budget 2025, Legal Database, ČSÚ Macroeconomic Data

## Setup

### Backend (FastAPI)

1. Make sure all Python dependencies are installed:
```bash
pip install fastapi uvicorn python-dotenv google-generativeai chromadb sentence-transformers duckduckgo-search pandas openpyxl requests
```

2. Start the API server:
```bash
python api.py
```

The API will run on `http://localhost:8000`

### Frontend (React)

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies (if not already done):
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will run on `http://localhost:3000`

## Usage

1. Start both servers (backend and frontend)
2. Open `http://localhost:3000` in your browser
3. Enter political text to analyze
4. Click "Analyzovat" to get AI-powered analysis

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /api/analyze` - Analyze political text
  - Request body: `{ "text": "your political text here" }`
  - Response: Structured analysis with topics and claims

## Features

- ✅ Modern, minimalistic UI with Tailwind CSS
- ✅ Real-time analysis with loading states
- ✅ Topic-based organization
- ✅ Detailed claim analysis
- ✅ Responsive design
- ✅ Error handling
- ✅ Professional design language (Linear/Notion style)
