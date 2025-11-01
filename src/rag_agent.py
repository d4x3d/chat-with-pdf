"""RAG agent and retrieval helpers.

Provides:
- get_retriever(persist_dir, k)
- answer_query(query)
- a small retrieval tool wrapper (retrieve_context) that returns serialized context

This module prefers OpenAI Chat model / embeddings if available; it is easy to adapt
to other LLMs (Groq, Ollama, etc.) by swapping the imports in get_llm / get_embeddings.
"""
from typing import List, Tuple
from pathlib import Path

from src import config


# Lightweight optional decorator: if langchain.tools.tool is available, use it,
# otherwise return the function unchanged so imports won't fail at module load.
def _optional_tool_decorator():
    def _noop(f):
        return f

    try:
        from langchain.tools import tool

        def _apply_tool(f):
            return tool(response_format="content_and_artifact")(f)

        return _apply_tool
    except Exception:
        return _noop


_tool = _optional_tool_decorator()


_PERSIST_DIR = Path("./chroma_db")
_K = 2  # Reduce number of documents retrieved to prevent large payloads


def _ensure_langchain_parts():
    """Import required langchain parts lazily and raise helpful errors if missing."""
    try:
        from langchain_community.embeddings import OpenAIEmbeddings
        from langchain_core.documents import Document
        from langchain_core.language_models import BaseLanguageModel
        _ChatClass = BaseLanguageModel
        
        # Try modern Chroma first, then fallback to community version
        Chroma = None
        try:
            from langchain_chroma import Chroma
        except Exception:
            try:
                from langchain_community.vectorstores import Chroma
            except Exception:
                raise RuntimeError("Could not import Chroma from langchain_chroma or langchain_community")
    except Exception as e:
        raise RuntimeError(
            "Missing required langchain components. Install langchain and provider packages (see requirements.txt)."
        ) from e

    return OpenAIEmbeddings, Chroma, Document, _ChatClass


def get_embeddings():
    # Only Mistral provider is supported in this repo (per user preference).
    provider = config.preferred_provider()
    OpenAIEmbeddings, Chroma, Document, ChatClass = _ensure_langchain_parts()

    if provider != "mistral":
        raise RuntimeError(
            "No MISTRAL_API_KEY found in environment. This project is configured to use Mistral embeddings/LLM. "
            "Set MISTRAL_API_KEY in your .env or environment to proceed."
        )

    try:
        from langchain_mistralai import MistralAIEmbeddings
        return MistralAIEmbeddings(model="mistral-embed")
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize MistralAIEmbeddings. Install 'langchain-mistralai' and ensure MISTRAL_API_KEY is valid. Error: {e}"
        )


def get_vectorstore(persist_dir: str | Path | None = None):
    OpenAIEmbeddings, Chroma, Document, _ = _ensure_langchain_parts()
    pd = Path(persist_dir or _PERSIST_DIR)
    if not pd.exists():
        raise RuntimeError(f"Vector DB directory not found: {pd}. Run the ingest script first.")
    embeddings = get_embeddings()
    vectordb = Chroma(persist_directory=str(pd), embedding_function=embeddings)
    return vectordb


def get_retriever(persist_dir: str | Path | None = None, k: int | None = None):
    vs = get_vectorstore(persist_dir)
    return vs.as_retriever(search_kwargs={"k": k or _K})


@_tool
def retrieve_context(query: str, persist_dir: str | Path | None = None):
    """Retrieve top documents and return a serialized string and the raw docs.

    The function is decorated with langchain.tools.tool when available; otherwise
    it behaves as a plain function.
    """
    retriever = get_retriever(persist_dir)
    docs = retriever.invoke(query)
    serialized = "\n\n".join(
        f"Source: {getattr(d, 'metadata', {}).get('source')}\nContent: {getattr(d, 'page_content', '')[:1000]}"
        for d in docs
    )
    return serialized, docs


def get_qa_chain(persist_dir: str | Path | None = None):
    OpenAIEmbeddings, Chroma, Document, ChatClass = _ensure_langchain_parts()

    # Only Mistral supported here. Require MISTRAL_API_KEY and langchain-mistralai.
    provider = config.preferred_provider()
    if provider != "mistral":
        raise RuntimeError(
            "This project is configured to use Mistral as the LLM/embeddings provider. Set MISTRAL_API_KEY in your environment."
        )

    try:
        from langchain_mistralai import ChatMistralAI
        llm = ChatMistralAI(model="mistral-small", temperature=0)
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize Mistral LLM. Install 'langchain-mistralai' and ensure MISTRAL_API_KEY is valid. Error: {e}"
        )
    retriever = get_retriever(persist_dir)
    
    # Create an optimized RAG pipeline with caching and better prompt structure
    def rag_pipeline(query):
        # Retrieve relevant documents with optimized search parameters
        docs = retriever.invoke(query)
        
        # Limit context size to prevent excessive token usage and WebSocket payload issues
        max_context_length = 1000  # Reduce further to prevent payload errors
        context_parts = []
        current_length = 0
        
        for doc in docs:
            doc_content = doc.page_content[:500]  # Limit each document to 500 chars
            if current_length + len(doc_content) <= max_context_length:
                context_parts.append(doc_content)
                current_length += len(doc_content)
            else:
                # Add partial content if we have space
                remaining_space = max_context_length - current_length
                if remaining_space > 30:  # Only add if meaningful content fits
                    context_parts.append(doc_content[:remaining_space] + "...")
                    break
        
        context = "\n\n".join(context_parts)
        
        # Create optimized prompt with clear instructions
        prompt = f"""Based on the following context, provide a concise answer to the question.

Context:
{context}

Question: {query}

Answer concisely:"""
        
        response = llm.invoke(prompt)
        return response.content, docs
    
    return rag_pipeline


def answer_query(query: str, persist_dir: str | Path | None = None):
    rag_pipeline = get_qa_chain(persist_dir)
    # Call the RAG pipeline
    answer, source_docs = rag_pipeline(query)
    return answer, source_docs


if __name__ == "__main__":
    print("This module provides RAG helpers. Use its functions from your app.")
