from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_processor import process_pdf
from services.vector_store import add_to_vector_store
import uuid
import os

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a PDF file
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Generate unique ID for the document
        document_id = str(uuid.uuid4())
        
        # Save file temporarily
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}.pdf")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process PDF
        text_chunks = await process_pdf(file_path)
        
        # Add to vector store
        await add_to_vector_store(document_id, text_chunks)

        return {"documentId": document_id, "message": "File processed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 