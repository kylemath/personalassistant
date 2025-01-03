from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
from .core.llm import LLMManager
from .core.file_manager import FileManager

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class Command(BaseModel):
    command: str
    args: Optional[Dict[str, Any]] = None

class CalendarEvent(BaseModel):
    id: str
    title: str
    startTime: str
    endTime: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    calendar: str

# Initialize managers
llm_manager = LLMManager()
file_manager = FileManager()
llm_manager.register_file_manager(file_manager)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "calendar":
                # Handle calendar-specific actions
                action = data.get("action")
                if action == "request_add_event":
                    # Send back a message to show the add event form
                    await manager.send_message({
                        "type": "calendar",
                        "action": "show_add_form"
                    }, websocket)
                elif action == "add_event":
                    # Handle adding a new event
                    event_data = data.get("event", {})
                    try:
                        event_id = llm_manager.calendar.create_event(
                            summary=event_data.get("title"),
                            start_time=event_data.get("startTime"),
                            end_time=event_data.get("endTime"),
                            location=event_data.get("location"),
                            description=event_data.get("description")
                        )
                        # Broadcast the new event to all connected clients
                        for connection in manager.active_connections:
                            await manager.send_message({
                                "type": "calendar",
                                "action": "add",
                                "event": {
                                    "id": event_id,
                                    **event_data
                                }
                            }, connection)
                    except Exception as e:
                        await manager.send_message({
                            "type": "error",
                            "message": f"Failed to create event: {str(e)}"
                        }, websocket)
            
            elif "command" in data:
                # Handle command
                response = await llm_manager._handle_command(data["command"])
                await manager.send_message({
                    "type": "message",
                    "content": response
                }, websocket)
            else:
                # Handle regular message
                response = await llm_manager.generate_response(data["message"], data.get("context", {}))
                await manager.send_message({
                    "type": "message",
                    "content": response
                }, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await manager.send_message({
                "type": "error",
                "message": f"An error occurred: {str(e)}"
            }, websocket)
        except:
            pass

@app.post("/chat")
async def chat(message: Message):
    response = await llm_manager.generate_response(message.message, message.context or {})
    return {"response": response}

@app.post("/command")
async def execute_command(command: Command):
    response = await llm_manager._handle_command(command.command)
    return {
        "status": "success",
        "data": response
    }

@app.get("/calendar/events")
async def list_events(max_results: int = Query(default=10, ge=1, le=50)):
    try:
        events = llm_manager.calendar.list_upcoming_events(max_results)
        formatted_events = []
        
        for event in events:
            formatted_event = {
                "id": event["id"],
                "title": event["summary"],
                "startTime": event["start"].get("dateTime", event["start"].get("date")),
                "endTime": event["end"].get("dateTime", event["end"].get("date")) if "end" in event else None,
                "location": event.get("location"),
                "description": event.get("description"),
                "calendar": event.get("calendar", "Primary")
            }
            formatted_events.append(formatted_event)
            
        return formatted_events
    except Exception as e:
        return {"error": str(e)}, 500 

@app.get("/api/emails/recent")
async def get_recent_emails():
    """Get recent emails from Gmail."""
    try:
        print("Debug: Fetching recent emails from Gmail")
        emails = llm_manager.gmail.list_recent_emails(max_results=30)
        print(f"Debug: Found {len(emails)} emails")
        return {"emails": emails}
    except Exception as e:
        print(f"Error fetching recent emails: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e)) 

@app.get("/api/emails/starred")
async def get_starred_emails(max_results: int = 10):
    """Get starred emails from Gmail."""
    try:
        print("Debug: Fetching starred emails from Gmail")
        emails = llm_manager.gmail.get_starred_emails(max_results=max_results)
        print(f"Debug: Found {len(emails)} starred emails")
        return {"emails": emails}
    except Exception as e:
        print(f"Error fetching starred emails: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{email_id}/open")
async def open_email(email_id: str):
    """Open an email in Gmail and mark it as read."""
    try:
        url = f"https://mail.google.com/mail/u/0/#inbox/{email_id}"
        # Mark as read logic would go here if needed
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@app.post("/api/emails/{email_id}/mark-read")
async def mark_email_as_read(email_id: str):
    """Mark an email as read."""
    try:
        success = llm_manager.gmail.mark_as_read(email_id)
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to mark email as read")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{email_id}/star")
async def star_email(email_id: str):
    """Star an email."""
    try:
        success = llm_manager.gmail.star_email(email_id)
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to star email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{email_id}/unstar")
async def unstar_email(email_id: str):
    """Unstar an email."""
    try:
        success = llm_manager.gmail.unstar_email(email_id)
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to unstar email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{email_id}/read")
async def read_email(email_id: str):
    """Read an email and mark it as read."""
    try:
        # Get the email content
        email = llm_manager.gmail.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Mark it as read
        success = llm_manager.gmail.mark_as_read(email_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to mark email as read")
        
        return {"email": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 