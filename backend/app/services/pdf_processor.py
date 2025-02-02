from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
import asyncio

class TextChunk:
    def __init__(self, text: str, page: int, metadata: Dict = None):
        self.text = text
        self.page = page
        self.metadata = metadata or {}

async def process_pdf(file_path: str) -> List[TextChunk]:
    """
    Process a PDF file and return chunks of text with metadata
    """
    # Read PDF file
    pdf = PdfReader(file_path)
    text_chunks = []

    # Extract text from each page
    for page_num in range(len(pdf.pages)):
        page = pdf.pages[page_num]
        text = page.extract_text()
        
        if text.strip():  # Only process non-empty pages
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            chunks = text_splitter.split_text(text)
            
            # Create TextChunk objects with metadata
            for chunk in chunks:
                text_chunks.append(TextChunk(
                    text=chunk,
                    page=page_num + 1,  # 1-based page numbering
                    metadata={
                        "page": page_num + 1,
                        "source": file_path
                    }
                ))

    return text_chunks

async def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract all text from a PDF file
    """
    pdf = PdfReader(file_path)
    text = ""
    
    for page in pdf.pages:
        text += page.extract_text()
    
    return text 