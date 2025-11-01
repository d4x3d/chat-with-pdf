"""Ingest PDFs into a Chroma vector store for RAG.

Usage:
    python -m src.ingest --pdf-dir ./pdfs --persist-dir ./chroma_db

This script is intentionally conservative about provider choice: it will try
to use OpenAI embeddings if OPENAI_API_KEY is set, otherwise it will fall back
to any embedding class available (user can adapt to Groq embeddings if desired).
"""
import os
from pathlib import Path
import argparse
from typing import List, Tuple

# Import Pdf reader with fallbacks to support different installed packages
try:
    # preferred modern package
    from pypdf import PdfReader
except Exception:
    try:
        # older packaging name
        from PyPDF2 import PdfReader
    except Exception:
        PdfReader = None


def _ensure_langchain_imports():
    """Try several import locations used across LangChain versions and return the classes.

    This gives friendlier errors when LangChain refactors move symbols between modules.
    """
    errors = []

    # RecursiveCharacterTextSplitter from langchain-text-splitters
    RecursiveCharacterTextSplitter = None
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception as e:
        errors.append(f"langchain_text_splitters.RecursiveCharacterTextSplitter: {e}")

    # Document from langchain-core
    Document = None
    try:
        from langchain_core.documents import Document
    except Exception as e:
        errors.append(f"langchain_core.documents.Document: {e}")

    # Embeddings: prefer Groq/OpenAI wrappers at runtime
    OpenAIEmbeddings = None
    try:
        from langchain_community.embeddings import OpenAIEmbeddings
    except Exception as e:
        errors.append(f"langchain_community.embeddings.OpenAIEmbeddings: {e}")

    # Vector store: Chroma from langchain-chroma (modern version)
    Chroma = None
    try:
        from langchain_chroma import Chroma
    except Exception as e:
        # Fallback to community version
        try:
            from langchain_community.vectorstores import Chroma
        except Exception as e2:
            errors.append(f"langchain_chroma.Chroma: {e}, langchain_community.vectorstores.Chroma: {e2}")

    if not (RecursiveCharacterTextSplitter and Document and OpenAIEmbeddings and Chroma):
        raise RuntimeError(
            "Missing required langchain symbols. Errors: \n" + "\n".join(errors)
            + "\nInstall the packages listed in requirements.txt and ensure they are available in the active environment."
        )

    return RecursiveCharacterTextSplitter, Document, OpenAIEmbeddings, Chroma


def extract_text_from_pdf(path: Path) -> List[Tuple[str, int]]:
    """Extract text from PDF with page numbers."""
    if PdfReader is None:
        raise RuntimeError("No PDF reader available. Install 'pypdf' or 'PyPDF2'.")
    reader = PdfReader(str(path))
    out = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            if text.strip():
                out.append((text, i + 1))  # page numbers start from 1
        except Exception:
            # best effort
            continue
    return out


def index_pdfs(pdf_dir: str = "./pdfs", persist_dir: str = "./chroma_db"):
    pdf_dir_path = Path(pdf_dir)
    persist_dir_path = Path(persist_dir)
    files: List[Path] = list(pdf_dir_path.glob("**/*.pdf"))
    if not files:
        print(f"No PDF files found in {pdf_dir_path}. Put PDFs there and run again.")
        return

    docs = []
    for f in files:
        page_texts = extract_text_from_pdf(f)
        if not page_texts:
            continue
        
        # Create documents for each page with page metadata
        for text, page_num in page_texts:
            if text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={
                        "source": str(f),
                        "page": page_num,
                        "filename": f.name
                    }
                ))

    RecursiveCharacterTextSplitter, Document, OpenAIEmbeddings, Chroma = _ensure_langchain_imports()

    # Use very small chunk size to prevent engine.io payload errors
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,  # Smaller chunks
        chunk_overlap=25,  # Minimal overlap
        length_function=len,
        is_separator_regex=False
    )
    split_docs = splitter.split_documents(docs)

    # Use Mistral embeddings
    try:
        from langchain_mistralai import MistralAIEmbeddings
        if "MISTRAL_API_KEY" not in os.environ:
            raise RuntimeError("MISTRAL_API_KEY not found in environment. Please set it in your .env file.")
        embeddings = MistralAIEmbeddings(model="mistral-embed")
    except Exception as e:
        raise RuntimeError(f"Mistral embeddings not available. Install 'langchain-mistralai' and ensure MISTRAL_API_KEY is set. Error: {e}")

    vectordb = Chroma.from_documents(split_docs, embeddings, persist_directory=str(persist_dir_path))
    print(f"Indexed {len(split_docs)} document chunks to {persist_dir_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", default="./pdfs")
    parser.add_argument("--persist-dir", default="./chroma_db")
    args = parser.parse_args()
    index_pdfs(args.pdf_dir, args.persist_dir)


if __name__ == "__main__":
    main()


def index_pdf_file(file_path: str | Path, persist_dir: str = "./chroma_db"):
    """Index a single PDF file into the Chroma vector store.

    This is useful for interactive flows (upload one PDF from the UI).
    """
    RecursiveCharacterTextSplitter, Document, OpenAIEmbeddings, Chroma = _ensure_langchain_imports()

    p = Path(file_path)
    if not p.exists():
        raise RuntimeError(f"PDF file not found: {p}")

    page_texts = extract_text_from_pdf(p)
    if not page_texts:
        print(f"No text extracted from {p}; skipped.")
        return 0

    docs = []
    for text, page_num in page_texts:
        if text.strip():
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": str(p),
                    "page": page_num,
                    "filename": p.name
                }
            ))
    # Use very small chunk size to prevent engine.io payload errors
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,  # Smaller chunks
        chunk_overlap=25,  # Minimal overlap
        length_function=len,
        is_separator_regex=False
    )
    split_docs = splitter.split_documents(docs)

    # Use Mistral embeddings
    try:
        from langchain_mistralai import MistralAIEmbeddings
        if "MISTRAL_API_KEY" not in os.environ:
            raise RuntimeError("MISTRAL_API_KEY not found in environment. Please set it in your .env file.")
        embeddings = MistralAIEmbeddings(model="mistral-embed")
    except Exception as e:
        raise RuntimeError(f"Mistral embeddings not available. Install 'langchain-mistralai' and ensure MISTRAL_API_KEY is set. Error: {e}")

    # Convert persist_dir to Path for operations, but keep as string for Chroma
    persist_dir_path = Path(persist_dir)
    persist_dir_path.mkdir(parents=True, exist_ok=True)

    # Load existing Chroma or create new one and add documents
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    vectordb.add_documents(split_docs)
    print(f"Indexed {len(split_docs)} chunks from {p} into {persist_dir}")
    return len(split_docs)
