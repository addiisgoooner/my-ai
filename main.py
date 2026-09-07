from typing import List
 
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
 
app = FastAPI(title="Ollama AI API")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "devstral-small-2"
 
memories: List[dict] = []
 
 
class ChatRequest(BaseModel):
    message: str
 
 
@app.get("/")
async def root():
    return {"message": "Ollama AI API is running"}
 
 
@app.get("/memories")
async def get_memories():
    return {"memories": memories}
 
 
@app.post("/chat")
async def chat(request: ChatRequest):
    memories.append(
        {
            "role": "user",
            "content": request.message,
        }
    )
 
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": memories,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
 
    assistant_message = data["message"]
    memories.append(assistant_message)
 
    return {
        "response": assistant_message["content"],
        "memories": memories,
    }  