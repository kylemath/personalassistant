from chromadb import Client, Settings
from datetime import datetime
import json

class MemoryManager:
    def __init__(self):
        self.client = Client(Settings(is_persistent=True, persist_directory="data/memory"))
        # Separate collections for different types of memory
        self.conversations = self.client.get_or_create_collection("conversation_history")
        self.personal_info = self.client.get_or_create_collection("personal_info")
        self.long_term_memory = self.client.get_or_create_collection("long_term_facts")
        
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
        self.long_term_memory.add(
            documents=[fact],
            metadatas=[{"category": category, "timestamp": timestamp}],
            ids=[f"fact_{timestamp}"]
        )
    
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

    def list_facts(self, category: str = None) -> list:
        try:
            if category:
                results = self.long_term_memory.query(
                    query_texts=[""],
                    where={"category": category}
                )
            else:
                results = self.long_term_memory.query(
                    query_texts=[""],
                    n_results=100  # Adjust limit as needed
                )
            
            if results and results['documents']:
                # Format facts with their IDs for reference
                facts = []
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    fact_id = results['ids'][0][i]
                    category = metadata.get('category', 'general')
                    facts.append(f"[{fact_id}] ({category}) {doc}")
                return facts
            return []
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