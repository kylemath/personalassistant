from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.llm import LLMManager

app = FastAPI()
llm_manager = LLMManager()

# Mount the static directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")

@app.post("/chat")
async def chat(message: str):
    response = await llm_manager.generate_response(message)
    return {"response": response} 