from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from services.pdf_processor import TextChunk
from typing import List, Dict
import os

# Initialize embeddings model
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Vector store persistence directory
VECTOR_STORE_DIR = "vector_store"
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

class VectorStore:
    def __init__(self):
        self.vector_store = Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding_function=embeddings
        )

    async def add_documents(self, document_id: str, chunks: List[TextChunk]):
        """
        Add document chunks to the vector store
        """
        texts = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "page": chunk.page,
                **chunk.metadata
            }
            for chunk in chunks
        ]

        self.vector_store.add_texts(texts=texts, metadatas=metadatas)
        self.vector_store.persist()

    async def search(self, query: str, document_id: str, k: int = 3) -> List[Dict]:
        """
        Search for relevant document chunks
        """
        # Filter for specific document
        filter = {"document_id": document_id}
        
        # Search vector store
        results = self.vector_store.similarity_search_with_score(
            query,
            k=k,
            filter=filter
        )

        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "text": doc.page_content,
                "page": doc.metadata.get("page", 1),
                "score": score
            })

        return formatted_results

# Global vector store instance
vector_store = VectorStore()

async def add_to_vector_store(document_id: str, chunks: List[TextChunk]):
    """
    Add document chunks to the vector store
    """
    await vector_store.add_documents(document_id, chunks)

async def search_vector_store(query: str, document_id: str, k: int = 3) -> List[Dict]:
    """
    Search for relevant document chunks
    """
    return await vector_store.search(query, document_id, k) 