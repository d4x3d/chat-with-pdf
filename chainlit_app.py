"""Chainlit app to expose the RAG agent via UI.

Run with:
    chainlit run chainlit_app.py

This file wires incoming messages to the RetrievalQA chain defined in
`src.rag_agent` and returns the answer and (optionally) source snippets.
"""
import asyncio
from pathlib import Path

import chainlit as cl

from src import rag_agent, ingest


PDFS_DIR = Path("./pdfs")
PDFS_DIR.mkdir(exist_ok=True)


async def _process_and_index_file(file_obj, send_fn=None):
    """Save a Chainlit file object to disk and index it."""
    # file_obj may be a chainlit.File or similar; try to find a path or bytes
    try:
        # If file_obj has a 'path' attribute, it's already saved server-side
        path = getattr(file_obj, "path", None)
        if path:
            target = Path(path)
        else:
            # Otherwise, try to read bytes from content/url
            name = getattr(file_obj, "name", "uploaded.pdf")
            target = PDFS_DIR / name
            # file_obj may support .content or .read()
            content = None
            if hasattr(file_obj, "content"):
                content = file_obj.content
            elif hasattr(file_obj, "read"):
                # read may be coroutine
                maybe = file_obj.read()
                if asyncio.iscoroutine(maybe):
                    content = await maybe
                else:
                    content = maybe

            if content is not None:
                with open(target, "wb") as f:
                    f.write(content)
            else:
                raise RuntimeError("Uploaded file has no content attribute; cannot save.")

        if send_fn is None:
            await cl.Message(content=f"Saved uploaded file: {target.name}. Starting processing...").send()
        else:
            await send_fn(f"Saved uploaded file: {target.name}. Starting processing...")

        def _index():
            return ingest.index_pdf_file(target, persist_dir="./chroma_db")

        n = await asyncio.to_thread(_index)
        if send_fn is None:
            await cl.Message(content=f"Finished indexing {target.name}: {n} chunks added.").send()
        else:
            await send_fn(f"Finished indexing {target.name}: {n} chunks added.")
    except Exception as e:
        if send_fn is None:
            await cl.Message(content=f"Error while indexing uploaded file: {e}").send()
        else:
            await send_fn(f"Error while indexing uploaded file: {e}")


@cl.on_chat_start
async def start():
    """Ask the user to upload one or more PDFs before the conversation begins.

    This uses AskFileMessage.send() which waits for the user's upload and
    returns a list of uploaded files. We index each uploaded PDF and notify
    the user when indexing is complete.
    """
    files = None
    # Keep asking until user uploads or timeout/raises
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload one or more PDF files to begin.",
            accept={"application/pdf": [".pdf"]},
            max_files=10,
            max_size_mb=10,
            timeout=120,
            raise_on_timeout=False,
        ).send()

    if not files:
        await cl.Message(content="No files uploaded. You can upload later by typing '/upload'.").send()
        return

    # files is a list of AskFileResponse / File-like objects
    for f in files:
        # process each uploaded file and send messages to the user
        await _process_and_index_file(f)


@cl.on_message
async def main(message):
    # Chainlit passes a Message object; extract content
    text = getattr(message, "content", "")
    if text is None:
        text = ""
    text = text.strip()

    # Trigger upload flow when user types '/upload'
    if text.lower() in ("/upload", "upload"):
        ask = cl.AskFileMessage(content="Upload a PDF to index", accept=[".pdf"])
        files = await ask.send()
        # `files` is a list of uploaded File objects (or empty list)
        if files:
            for f in files:
                await _process_and_index_file(f)

        return

    # Otherwise treat as a query
    try:
        answer, sources = rag_agent.answer_query(text)
        await cl.Message(content=answer).send()
        
        if sources:
            seen = set()
            citations = []
            for d in sources:
                meta = getattr(d, "metadata", {}) or {}
                src = meta.get("source") or meta.get("source_id") or str(getattr(d, "id", ""))
                
                # Create a unique identifier using source + page + content hash
                content_hash = hash(d.page_content[:100])  # Use first 100 chars for uniqueness
                unique_id = f"{src}_{meta.get('page', '')}_{content_hash}"
                
                if not src or unique_id in seen:
                    continue
                seen.add(unique_id)
                
                # Extract user-friendly information
                filename = meta.get("filename", Path(src).name)
                page_num = meta.get("page", "Unknown")
                content_excerpt = d.page_content[:200] + "..." if len(d.page_content) > 200 else d.page_content
                
                # Format citation with readable information
                citation = f"*Source {len(citations) + 1}: {filename} (Page {page_num})*\n   {content_excerpt}"
                citations.append(citation)

            if citations:
                cite_text = "\n\n**Sources:**\n" + "\n\n".join(citations)
                await cl.Message(content=cite_text).send()
                
    except Exception as e:
        await cl.Message(content=f"Error answering query: {e}").send()
