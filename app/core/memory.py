from chromadb import Client, Settings
from datetime import datetime, timedelta
import math
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from typing import List, Dict, Any
import json

class MemoryManager:
    def __init__(self):
        # Initialize ChromaDB
        self.client = Client(Settings(is_persistent=True, persist_directory="data/memory"))
        
        # Initialize collections
        self.system_config = self.client.get_or_create_collection("system_config")
        self.user_facts = self.client.get_or_create_collection("user_facts")
        self.contextual = self.client.get_or_create_collection("contextual")
        self.reference = self.client.get_or_create_collection("reference")
        
        # Initialize NLTK resources
        self._initialize_nltk()
        
        # Memory constants
        self.MEMORY_THRESHOLD = 0.3
        self.RECENCY_WEIGHT = 0.5
        self.MAX_CONTEXT_ITEMS = 5

    def _initialize_nltk(self):
        """Initialize all required NLTK resources with better error handling."""
        try:
            # First try to download all required resources
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('wordnet', quiet=True)
            
            # Verify the downloads worked
            self.stop_words = set(stopwords.words('english'))
            
            # Set up tokenizers with error handling
            def safe_word_tokenize(text):
                try:
                    return word_tokenize(text)
                except LookupError:
                    return text.split()
                    
            def safe_sent_tokenize(text):
                try:
                    return sent_tokenize(text)
                except LookupError:
                    return [s.strip() for s in text.split('.') if s.strip()]
            
            # Store the safe tokenizers
            self.word_tokenize = safe_word_tokenize
            self.sent_tokenize = safe_sent_tokenize
            
        except Exception as e:
            print(f"Warning: NLTK initialization using basic tokenization: {e}")
            # Define fallback tokenizers
            self.word_tokenize = str.split
            self.sent_tokenize = lambda x: [s.strip() for s in x.split('.') if s.strip()]
            self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to'}

    def add_system_config(self, key: str, value: Any):
        """Store system configuration."""
        self.system_config.upsert(
            documents=[json.dumps(value)],
            metadatas=[{'timestamp': datetime.now().isoformat()}],
            ids=[key]
        )

    def add_user_fact(self, fact: str, category: str = "general"):
        """Store important user information."""
        fact_id = f"fact_{datetime.now().isoformat()}"
        self.user_facts.add(
            documents=[fact],
            metadatas=[{
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'type': 'user_fact'
            }],
            ids=[fact_id]
        )

    def add_interaction(self, user_message: str, assistant_response: str = None):
        """Store an interaction with proper type detection."""
        # Handle both old and new formats
        if isinstance(user_message, dict):
            # Old format where first argument is a dict
            interaction = user_message
        else:
            # New format with separate user message and assistant response
            interaction = {
                'type': 'conversation',
                'content': f"User: {user_message}\nAssistant: {assistant_response}",
                'timestamp': datetime.now().isoformat()
            }
        
        # Calculate significance and store
        significance = self._calculate_significance(interaction)
        if significance > self.MEMORY_THRESHOLD:
            metadata = {
                'timestamp': interaction.get('timestamp', datetime.now().isoformat()),
                'type': interaction.get('type', 'conversation'),
                'significance': significance,
                'keywords': ','.join(self._extract_keywords(interaction['content']))
            }
            
            self.contextual.add(
                documents=[interaction['content']],
                metadatas=[metadata],
                ids=[f"interaction_{metadata['timestamp']}"]
            )

    def get_context(self, query: str) -> Dict:
        """Assemble relevant context for a query."""
        context = {
            'system': self._get_system_context(),
            'user': self._get_relevant_user_facts(query),
            'recent': self._get_relevant_interactions(query),
            'reference': []
        }
        
        # Add reference material if needed
        if self._needs_reference_context(query):
            context['reference'] = self._get_reference_material(query)
        
        return context

    def _calculate_significance(self, interaction: Dict) -> float:
        """Calculate how important an interaction is to remember."""
        content = interaction['content']
        
        # Factor 1: Length and complexity
        words = self.word_tokenize(content)
        length_score = min(len(words) / 100, 0.5)  # Cap at 0.5
        
        # Factor 2: Key terms presence
        key_terms = ['remember', 'important', 'note', 'save', 'schedule', 'meeting', 
                    'family', 'work', 'deadline', 'appointment']
        term_score = sum(term in content.lower() for term in key_terms) * 0.2
        
        # Factor 3: Interaction type weight
        type_weights = {
            'command': 0.3,
            'question': 0.5,
            'statement': 0.4,
            'email': 0.6,
            'calendar': 0.7
        }
        type_score = type_weights.get(interaction['type'], 0.3)
        
        return min(1.0, length_score + term_score + type_score)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from text."""
        words = self.word_tokenize(text.lower())
        return [word for word in words if word not in self.stop_words]

    def _summarize_content(self, text: str) -> str:
        """Create a concise summary using first two sentences."""
        sentences = self.sent_tokenize(text)
        return " ".join(sentences[:2])

    def _get_system_context(self) -> Dict:
        """Get current system configuration."""
        results = self.system_config.get()
        return {id_: json.loads(doc) for id_, doc in zip(results['ids'], results['documents'])}

    def _get_relevant_user_facts(self, query: str, limit: int = 5) -> List[str]:
        """Get user facts relevant to the query."""
        results = self.user_facts.query(
            query_texts=[query],
            n_results=limit
        )
        return results['documents'][0] if results['documents'] else []

    def _get_relevant_interactions(self, query: str) -> List[str]:
        """Get recent relevant interactions."""
        results = self.contextual.query(
            query_texts=[query],
            n_results=self.MAX_CONTEXT_ITEMS
        )
        return results['documents'][0] if results['documents'] else []

    def _needs_reference_context(self, query: str) -> bool:
        """Determine if query needs reference material."""
        reference_keywords = ['email', 'message', 'sent', 'received', 'calendar', 'event']
        return any(keyword in query.lower() for keyword in reference_keywords)

    def _get_reference_material(self, query: str, limit: int = 2) -> List[str]:
        """Get relevant reference material."""
        results = self.reference.query(
            query_texts=[query],
            n_results=limit
        )
        return results['documents'][0] if results['documents'] else []

    def cleanup_duplicates(self):
        """Remove duplicate entries while keeping the most significant ones."""
        for collection in [self.contextual, self.reference, self.user_facts]:
            try:
                # Get all documents from collection
                results = collection.get()
                if not results['ids']:
                    continue
                    
                seen_content = {}
                to_delete = []
                
                # Check for duplicates
                for doc_id, content, metadata in zip(
                    results['ids'], 
                    results['documents'], 
                    results['metadatas']
                ):
                    if content in seen_content:
                        # Compare significance if available
                        old_sig = seen_content[content].get('significance', 0)
                        new_sig = metadata.get('significance', 0)
                        
                        if new_sig > old_sig:
                            # Keep new, delete old
                            to_delete.append(seen_content[content]['id'])
                            seen_content[content] = {
                                'id': doc_id,
                                'significance': new_sig
                            }
                        else:
                            # Keep old, delete new
                            to_delete.append(doc_id)
                    else:
                        seen_content[content] = {
                            'id': doc_id,
                            'significance': metadata.get('significance', 0)
                        }
                
                # Delete duplicates
                if to_delete:
                    collection.delete(ids=to_delete)
                    
            except Exception as e:
                print(f"Error cleaning up duplicates in collection: {e}")
                continue

    def add_long_term_fact(self, fact: str, category: str = "general") -> None:
        """Add a fact to long-term memory, preventing duplicates."""
        try:
            # First check if this exact fact already exists
            results = self.user_facts.get()
            if results['documents']:
                for existing_fact in results['documents']:
                    if fact == existing_fact:
                        return  # Fact already exists
            
            # If we get here, fact doesn't exist, so add it
            fact_id = f"fact_{datetime.now().isoformat()}"
            self.user_facts.add(
                documents=[fact],
                metadatas=[{
                    'category': category,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'long_term_fact',
                    'significance': 1.0  # Long-term facts are always significant
                }],
                ids=[fact_id]
            )
        except Exception as e:
            print(f"Error adding long-term fact: {e}")
    
    def get_recent_history(self, limit: int = 5) -> str:
        """Get recent conversation history."""
        try:
            # Query recent interactions from contextual memory
            results = self.contextual.query(
                query_texts=[""],  # Empty query to get all
                n_results=limit,
                where={"type": "conversation"}  # Only get conversation type interactions
            )
            
            if results and results['documents'] and results['documents'][0]:
                # Sort by timestamp if available
                interactions = list(zip(results['documents'][0], results['metadatas'][0]))
                interactions.sort(key=lambda x: x[1].get('timestamp', ''), reverse=True)
                
                # Format the history
                history = []
                for content, metadata in interactions:
                    history.append(content)
                
                return "\n\n".join(history)
            
            return ""
            
        except Exception as e:
            print(f"Error getting recent history: {e}")
        return ""
    
    def add_conversation(self, user_message: str, assistant_response: str):
        """Add a conversation interaction."""
        interaction = {
            'type': 'conversation',
            'content': f"User: {user_message}\nAssistant: {assistant_response}"
        }
        self.add_interaction(interaction)
    
    def get_personal_info(self, category: str = None) -> str:
        """Get stored personal information about the user."""
        try:
            where = {"type": "user_fact"}
            if category:
                where["category"] = category
            
            results = self.user_facts.query(
                query_texts=[""],
                n_results=10,
                where=where
            )
            
            if results and results['documents'] and results['documents'][0]:
                return "\n".join(results['documents'][0])
            return ""
        except Exception as e:
            print(f"Error getting personal info: {e}")
            return ""
    
    def get_relevant_facts(self, query: str, limit: int = 3) -> str:
        """Get facts relevant to the current query."""
        try:
            results = self.user_facts.query(
                query_texts=[query],
                n_results=limit
            )
            if results and results['documents'] and results['documents'][0]:
                return "\n".join(results['documents'][0])
            return ""
        except Exception as e:
            print(f"Error getting relevant facts: {e}")
            return ""

    def list_facts(self, category: str = None) -> List[str]:
        """List all facts, optionally filtered by category."""
        try:
            where = {"type": "long_term_fact"}
            if category:
                where["category"] = category
            
            results = self.user_facts.get(where=where)
            
            if not results or not results['ids']:
                return []
            
            facts = []
            for fact_id, doc, meta in zip(
                results['ids'],
                results['documents'],
                results['metadatas']
            ):
                facts.append(f"[{fact_id}] ({meta.get('category', 'general')}) {doc}")
            
            return facts
        except Exception as e:
            print(f"Error listing facts: {e}")
            return []

    def delete_fact(self, fact_id: str) -> bool:
        """Delete a fact by its ID."""
        try:
            self.user_facts.delete(ids=[fact_id])
            return True
        except Exception as e:
            print(f"Error deleting fact: {e}")
            return False 