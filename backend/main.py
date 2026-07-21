import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.agent import factify_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("factify-main")

app = FastAPI(
    title="Factify API",
    description="Multi-Agent Corrective RAG Engine API",
    version="1.0.0"
)

# Enable CORS for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows local dev frontend (e.g., http://localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class ChatRequest(BaseModel):
    message: str

# Response schema
class ChatResponse(BaseModel):
    answer: str
    status: str = "success"

@app.get("/")
def read_root():
    return {"status": "online", "service": "Factify Corrective RAG API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip()
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message string cannot be empty.")
        
    try:
        logger.debug(f"Incoming API Request: '{user_message}'")
        
        # Invoke our compiled LangGraph Corrective RAG Agent
        inputs = {"question": user_message}
        final_state = factify_agent.invoke(inputs)
        
        answer = final_state.get("generation", "I was unable to synthesize an answer.")
        
        return ChatResponse(answer=answer)
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Factify Engine Error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    # Run server locally on port 8000
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)