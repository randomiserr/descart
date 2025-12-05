from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from deep_orchestrator import DeepResearchOrchestrator
from models import PlanAnalysis
import uvicorn

app = FastAPI(
    title="Czech Political Advisor API",
    description="AI-powered political and economic advisor for Czech Republic",
    version="2.0.0"
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator
orchestrator = DeepResearchOrchestrator()

class AnalyzeRequest(BaseModel):
    text: str

@app.post("/api/analyze", response_model=PlanAnalysis)
async def analyze_policy(request: AnalyzeRequest):
    try:
        # Run the deep research pipeline and return raw result
        result = await orchestrator.run_pipeline(request.text)
        return result
    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
