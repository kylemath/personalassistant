from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core.llm import LLMManager
from app.core.docs_generator import DocsGenerator
from app.core.file_manager import FileManager
from typing import List

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
llm = LLMManager()
file_manager = FileManager()

# Pass file_manager to LLM manager
llm.register_file_manager(file_manager)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_json({"message": message})

manager = ConnectionManager()

class ChatMessage(BaseModel):
    message: str
    context: dict = {}  # For file context, etc.

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    try:
        response = await llm.generate_response(
            chat_message.message,
            context=chat_message.context
        )
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            response = await llm.generate_response(data["message"])
            await manager.send_message(response, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Update documentation on startup
@app.on_event("startup")
async def startup_event():
    """Run on app startup."""
    try:
        docs_generator = DocsGenerator()
        docs_generator.update_files()
        print("Documentation updated successfully!")
    except Exception as e:
        print(f"Warning: Could not update documentation: {e}")

# Mount the static directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize docs generator for /help endpoint
docs_generator = DocsGenerator()

@app.get("/help")
async def get_help():
    """Return help content as HTML."""
    return HTMLResponse(docs_generator.generate_html()) 