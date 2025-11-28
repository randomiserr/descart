from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from orchestrator import AdvisorOrchestrator
import uvicorn

app = FastAPI(
    title="Czech Political Advisor API",
    description="AI-powered political and economic advisor for Czech Republic",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator once at startup
orchestrator = AdvisorOrchestrator()

class AnalysisRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    topics: list
    debug_context: dict = None

@app.get("/")
def read_root():
    return {
        "message": "Czech Political Advisor API",
        "status": "running",
        "endpoints": {
            "analyze": "/api/analyze",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_text(request: AnalysisRequest):
    """
    Analyze political text and return structured analysis
    """
    try:
        if not request.text or len(request.text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Text must be at least 10 characters long"
            )
        
        # Process request through orchestrator
        result = orchestrator.process_request(request.text)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
