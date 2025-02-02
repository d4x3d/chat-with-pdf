from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os

router = APIRouter()

UPLOAD_DIR = "uploads"

class Document(BaseModel):
    id: str
    name: str
    created_at: str

@router.get("/documents", response_model=List[Document])
async def get_documents():
    """
    Get list of processed documents
    """
    try:
        documents = []
        for filename in os.listdir(UPLOAD_DIR):
            if filename.endswith('.pdf'):
                doc_id = filename.replace('.pdf', '')
                doc_path = os.path.join(UPLOAD_DIR, filename)
                created_at = os.path.getctime(doc_path)
                
                documents.append(Document(
                    id=doc_id,
                    name=filename,
                    created_at=created_at
                ))
                
        return sorted(documents, key=lambda x: x.created_at, reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a processed document
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}.pdf")
        if os.path.exists(file_path):
            os.remove(file_path)
            # TODO: Remove from vector store
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 