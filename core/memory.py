import chromadb
from chromadb.utils import embedding_functions
from dataclasses import dataclass
from typing import Optional

@dataclass
class MemoryChunk:
    """A memory chunk with its source URL."""
    text: str
    source_url: Optional[str] = None
    topic: Optional[str] = None

class Memory:
    def __init__(self):
        # Use ephemeral in-memory client for session-scoped storage
        self.client = chromadb.Client()
        # Default to a simple collection
        self.collection = self.client.get_or_create_collection(name="research_session")
        # Use default embedding function for now (all-MiniLM-L6-v2)
        # In production, we should use GoogleGenAIEmbeddingFunction for better alignment
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
        
        # Simple ID generation
        doc_id = str(self.collection.count() + 1)
        metadata = {
            "source_url": source_url or "internal://research-notes",
            "topic": topic or "general"
        }
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def query(self, query_text: str, n_results: int = 3) -> list[MemoryChunk]:
        """Retrieves relevant context for a query WITH source information.
        
        Returns:
            List of MemoryChunk objects containing text and source URLs.
        """
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas"]
        )
        
        chunks = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            chunks.append(MemoryChunk(
                text=doc,
                source_url=metadata.get("source_url"),
                topic=metadata.get("topic")
            ))
        return chunks

    def clear(self):
        """Wipes the memory (session-scoped)."""
        self.client.delete_collection("research_session")
        self.collection = self.client.create_collection("research_session")

