# Descart

**Czech Political Policy Advisor** - An AI-powered tool for analyzing political proposals and policies in the context of Czech Republic's Strategy 2035.

![Descart Interface](frontend/public/antique-judge.png)

## Overview

Descart is a sophisticated political analysis platform that combines deep research capabilities with Czech economic data to provide comprehensive policy analysis. It evaluates political proposals against Strategy 2035 goals, analyzes economic impacts, and provides evidence-based recommendations.

## Features

- 🔍 **Deep Research Analysis** - Multi-stage research pipeline with web search and data gathering
- 📊 **Economic Impact Assessment** - Integration with Czech Statistical Office (ČSÚ) data
- 🎯 **Strategy 2035 Alignment** - Evaluates proposals against national strategic goals
- 📈 **Budget Analysis** - Analyzes fiscal impacts using real Czech budget data
- 🇨🇿 **Czech Language** - Full Czech language support throughout the interface
- 🎨 **Modern UI** - Clean, professional interface with neoclassical design elements

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - High-performance API server
- **Google Gemini** - LLM for analysis and research
- **Tavily** - Web search integration
- **Pydantic** - Data validation and modeling

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Vercel** - Deployment platform

### Data Sources
- Czech Statistical Office (ČSÚ) API
- Czech budget data (2025)
- Macroeconomic indicators
- Legal documents and policy texts

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Google Gemini API key
- Tavily API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/descart.git
   cd descart
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

### Running Locally

1. **Start the backend server**
   ```bash
   python api.py
   ```
   Backend will run on `http://localhost:8000`

2. **Start the frontend (in a new terminal)**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will run on `http://localhost:3000`

3. **Open your browser**
   Navigate to `http://localhost:3000` to use the application

### Quick Start (Windows)

Use the provided batch file:
```bash
start.bat
```

## Project Structure

```
descart/
├── frontend/              # Next.js frontend application
│   ├── app/              # App router pages and components
│   ├── public/           # Static assets
│   └── package.json      # Frontend dependencies
├── data/                 # Data files and databases
│   ├── codelists/       # ČSÚ codelists
│   ├── budget_2025.csv  # Czech budget data
│   └── macro_real.json  # Macroeconomic data
├── Gathered data/        # Agent-accessible research data
├── api.py               # FastAPI server
├── deep_orchestrator.py # Deep research pipeline
├── orchestrator.py      # Main orchestration logic
├── llm_client.py        # LLM client wrapper
├── tools.py             # Tool definitions for agent
├── prompts.py           # System prompts
├── models.py            # Pydantic data models
├── retrieval.py         # Data retrieval logic
├── calculations.py      # Economic calculations
├── csu_client.py        # ČSÚ API client
└── requirements.txt     # Python dependencies
```

## Documentation

- [STATUS.md](STATUS.md) - Project status and progress
- [CSU_INTEGRATION.md](CSU_INTEGRATION.md) - ČSÚ API integration guide
- [DATA_GATHERING.md](DATA_GATHERING.md) - Data gathering documentation
- [FORMULA_LIBRARY.md](FORMULA_LIBRARY.md) - Economic formula reference
- [STAGE3_EXPLANATION.md](STAGE3_EXPLANATION.md) - Stage 3 implementation details

## API Endpoints

### POST `/api/analyze`
Analyzes a political proposal or policy.

**Request:**
```json
{
  "text": "Zavedení školného na VŠ (5000 Kč/semestr)"
}
```

**Response:**
```json
{
  "executive_summary": {
    "plan_name": "...",
    "strategic_verdict_2035": "...",
    "main_benefits": [...],
    "main_risks": [...],
    "recommendations": [...]
  },
  "topics": [...],
  "sources": [...]
}
```

## Deployment

### Vercel (Frontend)

1. Push your code to GitHub
2. Import project in Vercel
3. Configure environment variables (if needed for frontend)
4. Deploy

### Backend Hosting

The backend can be deployed to:
- **Railway** - Easy Python deployment
- **Render** - Free tier available
- **Google Cloud Run** - Serverless container deployment
- **AWS Lambda** - Serverless with API Gateway

Set the `NEXT_PUBLIC_API_URL` environment variable in Vercel to point to your backend.

## Environment Variables

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### Frontend (Vercel)
```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Czech Statistical Office (ČSÚ) for providing open data APIs
- Google Gemini for LLM capabilities
- Tavily for web search integration
- Czech Republic's Strategy 2035 framework

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Built with ❤️ for better policy analysis in the Czech Republic
