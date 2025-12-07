import chromadb
from chromadb.utils import embedding_functions
from dataclasses import dataclass
from typing import Optional
import uuid

@dataclass
class MemoryChunk:
    """A memory chunk with its source URL."""
    text: str
    source_url: Optional[str] = None
    topic: Optional[str] = None

class Memory:
    """Session-scoped vector memory with efficient clearing via session_id metadata."""
    
    # Shared client and collection across all Memory instances
    _client: chromadb.Client = None
    _collection = None
    
    def __init__(self, session_id: str = None):
        """Initialize memory with a session ID for scoping.
        
        Args:
            session_id: Unique session identifier. Auto-generated if not provided.
        """
        # Lazy initialization of shared client
        if Memory._client is None:
            Memory._client = chromadb.Client()
            Memory._collection = Memory._client.get_or_create_collection(name="research_sessions")
        
        self.session_id = session_id or str(uuid.uuid4())
        self._doc_counter = 0
        
        # Use default embedding function (all-MiniLM-L6-v2)
        # NOTE: For air-gapped environments, consider using host embedding API
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    def add(self, text: str, source_url: str = None, topic: str = None):
        """Adds a text chunk to the memory with source tracking.
        
        Args:
            text: The content to store.
            source_url: The URL where this information was found.
            topic: The sub-question this chunk answers.
        """
        if not text:
            return
        
        self._doc_counter += 1
        doc_id = f"{self.session_id}_{self._doc_counter}"
        metadata = {
            "session_id": self.session_id,
            "source_url": source_url or "internal://research-notes",
            "topic": topic or "general"
        }
        Memory._collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def query(self, query_text: str, n_results: int = 3) -> list[MemoryChunk]:
        """Retrieves relevant context for a query WITH source information.
        
        Only returns results from the current session.
        
        Returns:
            List of MemoryChunk objects containing text and source URLs.
        """
        if Memory._collection.count() == 0:
            return []
        
        # Filter by session_id to only get results from this session
        results = Memory._collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"session_id": self.session_id},
            include=["documents", "metadatas"]
        )
        
        chunks = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                chunks.append(MemoryChunk(
                    text=doc,
                    source_url=metadata.get("source_url"),
                    topic=metadata.get("topic")
                ))
        return chunks

    def clear(self):
        """Clears memory for current session only (efficient - no collection recreation)."""
        if Memory._collection.count() == 0:
            return
            
        # Get all document IDs for this session
        try:
            results = Memory._collection.get(
                where={"session_id": self.session_id},
                include=[]
            )
            if results['ids']:
                Memory._collection.delete(ids=results['ids'])
        except Exception:
            # Collection might be empty or have no matching documents
            pass
        
        self._doc_counter = 0
