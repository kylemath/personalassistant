from chromadb import Client, Settings
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TodoManager:
    def __init__(self):
        self.client = Client(Settings(is_persistent=True, persist_directory="data/memory"))
        self.todos = self.client.get_or_create_collection("todos")

    def add_todo(self, 
                task: str, 
                priority: str = "medium",
                category: str = "general",
                due_date: Optional[str] = None,
                notes: Optional[str] = None) -> str:
        """Add a new todo item."""
        timestamp = datetime.now().isoformat()
        todo_id = f"todo_{timestamp}"
        
        # Ensure all metadata values are strings
        metadata = {
            "priority": priority.lower(),
            "category": category,
            "due_date": due_date if due_date else "",  # Convert None to empty string
            "notes": notes if notes else "",  # Convert None to empty string
            "status": "pending",
            "created_at": timestamp
        }
        
        self.todos.add(
            documents=[task],
            metadatas=[metadata],
            ids=[todo_id]
        )
        return todo_id

    def list_todos(self, 
                  status: str = "pending", 
                  category: Optional[str] = None, 
                  priority: Optional[str] = None) -> List[Dict]:
        """List todos with optional filters."""
        where = {"status": status}
        if category:
            where["category"] = category
        if priority:
            where["priority"] = priority.lower()

        results = self.todos.query(
            query_texts=[""],
            where=where
        )
        
        todos = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                todo = {
                    'id': results['ids'][0][i],
                    'task': doc,
                    **results['metadatas'][0][i]
                }
                todos.append(todo)
        return todos

    def complete_todo(self, todo_id: str) -> bool:
        """Mark a todo as completed."""
        try:
            # Get existing metadata
            results = self.todos.query(
                query_texts=[""],
                where={"status": "pending"},
                ids=[todo_id]
            )
            
            if not results['metadatas']:
                return False
                
            metadata = results['metadatas'][0][0]
            metadata['status'] = 'completed'
            metadata['completed_at'] = datetime.now().isoformat()
            
            # Update the todo
            self.todos.update(
                ids=[todo_id],
                metadatas=[metadata]
            )
            return True
        except Exception:
            return False

    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo item."""
        try:
            self.todos.delete(ids=[todo_id])
            return True
        except Exception:
            return False 