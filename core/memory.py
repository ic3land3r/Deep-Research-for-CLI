import chromadb
from chromadb.utils import embedding_functions

class Memory:
    def __init__(self):
        # Use ephemeral in-memory client for session-scoped storage
        self.client = chromadb.Client()
        # Default to a simple collection
        self.collection = self.client.get_or_create_collection(name="research_session")
        # Use default embedding function for now (all-MiniLM-L6-v2)
        # In production, we should use GoogleGenAIEmbeddingFunction for better alignment
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    def add(self, text: str, metadata: dict = None):
        """Adds a text chunk to the memory."""
        if not text:
            return
        
        # Simple ID generation
        doc_id = str(self.collection.count() + 1)
        self.collection.add(
            documents=[text],
            metadatas=[metadata] if metadata else None,
            ids=[doc_id]
        )

    def query(self, query_text: str, n_results: int = 3) -> list[str]:
        """Retrieves relevant context for a query."""
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count())
        )
        return results['documents'][0]

    def clear(self):
        """Wipes the memory (session-scoped)."""
        self.client.delete_collection("research_session")
        self.collection = self.client.create_collection("research_session")
