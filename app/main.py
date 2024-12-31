from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.core.llm import LLMManager

app = FastAPI()
llm_manager = LLMManager()  # Single instance for all requests

# Mount the static directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class ChatMessage(BaseModel):
    message: str
    context: dict = {}  # For file context, etc.

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")

@app.post("/chat")
async def chat(message: str):
    response = await llm_manager.generate_response(message)
    return {"response": response}

@app.post("/api/chat")
async def chat_endpoint(chat_message: ChatMessage):
    """Direct chat endpoint for IDE integration"""
    try:
        response = await llm_manager.generate_response(
            chat_message.message,
            context=chat_message.context
        )
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 