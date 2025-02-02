from langchain_groq import ChatGroq
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from services.vector_store import search_vector_store
from typing import Dict, List
import os

# Initialize LLM
groq_api_key = os.getenv('GROQ_API_KEY')
llm = ChatGroq(
    groq_api_key=groq_api_key,
    model_name='llama-3.3-70b-versatile'
)

# Store conversation histories
conversations: Dict[str, ConversationBufferMemory] = {}

async def get_chat_response(message: str, document_id: str) -> Dict:
    """
    Get a response from the chat model using relevant document context
    """
    try:
        # Get relevant document chunks
        context_chunks = await search_vector_store(message, document_id)
        
        # Format context for the prompt
        context = "\n\n".join([
            f"Content from page {chunk['page']}:\n{chunk['text']}"
            for chunk in context_chunks
        ])

        # Get or create conversation memory
        if document_id not in conversations:
            conversations[document_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        memory = conversations[document_id]

        # Create prompt with context
        prompt = f"""You are a helpful AI assistant that answers questions about PDF documents.
        Use the following context to answer the question. If you don't know the answer, say so.
        Don't make up information that's not in the context.

        Context:
        {context}

        Question: {message}

        Answer:"""

        # Get response from LLM
        response = await llm.apredict(prompt)

        # Update conversation memory
        memory.chat_memory.add_user_message(message)
        memory.chat_memory.add_ai_message(response)

        # Format response with sources
        return {
            "message": response,
            "sources": [
                {
                    "text": chunk["text"][:200] + "...",  # Truncate long texts
                    "page": chunk["page"]
                }
                for chunk in context_chunks
            ]
        }

    except Exception as e:
        raise Exception(f"Error getting chat response: {str(e)}")

async def clear_conversation(document_id: str):
    """
    Clear the conversation history for a document
    """
    if document_id in conversations:
        del conversations[document_id] 