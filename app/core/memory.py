from chromadb import Client, Settings
from datetime import datetime
import json
from typing import List

class MemoryManager:
    def __init__(self):
        print("Initializing MemoryManager")  # Debug print
        self.client = Client(Settings(is_persistent=True, persist_directory="data/memory"))
        print("ChromaDB client created")  # Debug print
        
        # List existing collections
        print(f"Existing collections: {self.client.list_collections()}")  # Debug print
        
        # Separate collections for different types of memory
        self.conversations = self.client.get_or_create_collection("conversation_history")
        self.personal_info = self.client.get_or_create_collection("personal_info")
        self.long_term_memory = self.client.get_or_create_collection("long_term_facts")
        
        # Check collection sizes
        print(f"Long term memory count: {self.long_term_memory.count()}")  # Debug print
        
    def add_interaction(self, user_message: str, assistant_response: str):
        timestamp = datetime.now().isoformat()
        self.conversations.add(
            documents=[f"User: {user_message}\nAssistant: {assistant_response}"],
            metadatas=[{"timestamp": timestamp, "type": "conversation"}],
            ids=[f"interaction_{timestamp}"]
        )
        
        # Try to extract personal information from the conversation
        self._extract_personal_info(user_message)
    
    def add_personal_info(self, category: str, info: str):
        timestamp = datetime.now().isoformat()
        self.personal_info.add(
            documents=[info],
            metadatas=[{"category": category, "timestamp": timestamp}],
            ids=[f"personal_{category}_{timestamp}"]
        )
    
    def add_long_term_fact(self, fact: str, category: str = "general"):
        timestamp = datetime.now().isoformat()
        fact_id = f"fact_{timestamp}"
        print(f"Adding fact with ID: {fact_id}")  # Debug print
        try:
            self.long_term_memory.add(
                documents=[fact],
                metadatas=[{"category": category, "timestamp": timestamp}],
                ids=[fact_id]
            )
            print(f"Successfully added fact: {fact}")  # Debug print
            
            # Verify it was added
            results = self.long_term_memory.query(
                query_texts=[""],
                n_results=100
            )
            print(f"Current facts: {results}")  # Debug print
        except Exception as e:
            print(f"Error adding fact: {e}")
    
    def get_recent_history(self, limit: int = 5) -> str:
        results = self.conversations.query(
            query_texts=[""],
            n_results=limit
        )
        
        if results and results['documents']:
            return "\n\n".join(results['documents'][0])
        return ""
    
    def get_personal_info(self, category: str = None) -> str:
        if category:
            results = self.personal_info.query(
                query_texts=[""],
                where={"category": category},
                n_results=10
            )
        else:
            results = self.personal_info.query(
                query_texts=[""],
                n_results=10
            )
            
        if results and results['documents']:
            return "\n".join(results['documents'][0])
        return ""
    
    def get_relevant_facts(self, query: str, limit: int = 3) -> str:
        results = self.long_term_memory.query(
            query_texts=[query],
            n_results=limit
        )
        
        if results and results['documents']:
            return "\n".join(results['documents'][0])
        return ""
    
    def _extract_personal_info(self, message: str):
        """
        Simple rule-based personal information extraction.
        In a production system, you might want to use NLP here.
        """
        # Example rules for personal info extraction
        if "my name is" in message.lower():
            name = message.lower().split("my name is")[-1].strip()
            self.add_personal_info("name", name)
        elif "i am from" in message.lower():
            location = message.lower().split("i am from")[-1].strip()
            self.add_personal_info("location", location)
        # Add more rules as needed 

    def list_facts(self, category: str = None) -> List[str]:
        """List all facts, optionally filtered by category."""
        try:
            print(f"Attempting to list facts with category: {category}")  # Debug print
            results = self.long_term_memory.query(
                query_texts=[""],
                where={"category": category} if category else None,
                n_results=100  # Increase number of results
            )
            
            print(f"Query results: {results}")  # Debug print
            
            if not results or not results['ids'] or not results['ids'][0]:
                print("No results found")  # Debug print
                return []
            
            facts = []
            for i, (fact_id, doc, meta) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0]
            )):
                fact_str = f"[{fact_id}] ({meta.get('category', 'general')}) {doc}"
                facts.append(fact_str)
                print(f"Found fact: {fact_str}")  # Debug print
            
            return facts
        except Exception as e:
            print(f"Error listing facts: {e}")
            return []

    def delete_fact(self, fact_id: str) -> bool:
        try:
            self.long_term_memory.delete(ids=[fact_id])
            return True
        except Exception as e:
            print(f"Error deleting fact: {e}")
            return False 