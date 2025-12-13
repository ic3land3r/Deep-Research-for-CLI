try:
    import chromadb
    from chromadb.utils import embedding_functions
    _HAS_CHROMA = True
except ImportError:
    chromadb = None
    embedding_functions = None
    _HAS_CHROMA = False
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
    
    _client = None
    _collection = None
    
    def __init__(self, session_id: str = None):
        global _HAS_CHROMA
        if _HAS_CHROMA:
            if Memory._client is None:
                try:
                    Memory._client = chromadb.Client()
                    Memory._collection = Memory._client.get_or_create_collection(name="research_sessions")
                except Exception as e:
                    print(f"Warning: Failed to init ChromaDB: {e}")
                    _HAS_CHROMA = False
        
        self.session_id = session_id or str(uuid.uuid4())
        self._doc_counter = 0
        
        if _HAS_CHROMA:
            try:
                self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            except Exception:
                self.embedding_fn = None

    def add(self, text: str, source_url: str = None, topic: str = None):
        if not text:
            return
        
        if not _HAS_CHROMA:
            return

        self._doc_counter += 1
        doc_id = f"{self.session_id}_{self._doc_counter}"
        metadata = {
            "session_id": self.session_id,
            "source_url": source_url or "internal://research-notes",
            "topic": topic or "general"
        }
        try:
            Memory._collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
        except Exception:
            pass

    def query(self, query_text: str, n_results: int = 3) -> list[MemoryChunk]:
        if not _HAS_CHROMA or Memory._collection is None or Memory._collection.count() == 0:
            return []
        
        try:
            results = Memory._collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"session_id": self.session_id},
                include=["documents", "metadatas"]
            )
        except Exception:
            return []
        
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
        if not _HAS_CHROMA or Memory._collection is None or Memory._collection.count() == 0:
            return
            
        try:
            results = Memory._collection.get(
                where={"session_id": self.session_id},
                include=[]
            )
            if results['ids']:
                Memory._collection.delete(ids=results['ids'])
        except Exception:
            pass
        
        self._doc_counter = 0
