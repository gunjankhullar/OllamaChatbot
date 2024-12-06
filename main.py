from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import uuid
import requests
from typing import Optional
from db import save_chat, get_all_chats, delete_chat_by_id, get_chat_history_by_session_id  # Extend database functions

# Initialize FastAPI app
app = FastAPI()

# Initialize Ollama client (instead of OpenAI)
class Conversation:
    def __init__(self):
        self.sessions = {}

    def add_message(self, session_id, role, content):
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": "You are a helpful assistant."}
            ]
        self.sessions[session_id].append({"role": role, "content": content})

    def get_messages(self, session_id):
        return self.sessions.get(session_id, [
            {"role": "system", "content": "You are a helpful assistant."}
        ])

    def get_response(self, session_id, user_message):
        # Append user's message
        self.add_message(session_id, "user", user_message)

        # Set up Ollama's API request to generate a response using the local model
        payload = {
            "model": "llama3.2:3b",  # Use the Ollama model
            "messages": self.get_messages(session_id)
        }

        # Call Ollama API
        response = requests.post(
            'http://localhost:11434/v1/chat/completions',  # Ollama's local API endpoint
            json=payload
        )

        # Check if the response is valid
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to connect to Ollama API")

        # Extract the assistant's response
        assistant_message = response.json()['choices'][0]['message']['content']
        self.add_message(session_id, "assistant", assistant_message)
        return assistant_message

# Instantiate conversation object
conversation = Conversation()

# Pydantic model for the request and response data
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    session_id: str

# FastAPI routes
@app.post("/chat", response_model=QueryResponse)
async def chat(data: ChatMessage):
    """API endpoint to handle chat interactions with session management."""
    user_message = data.message
    session_id = data.session_id or str(uuid.uuid4())
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message content is required")
    
    try:
        # Get response from assistant using Ollama
        response = conversation.get_response(session_id, user_message)
        
        # Save the chat log to MongoDB
        save_chat(user_message, response, session_id)
        
        return QueryResponse(answer=response, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI route for getting chat history
@app.get("/history")
async def get_history(session_id: str = None):
    """Retrieve chat history for a session or all sessions."""
    try:
        if session_id:
            chat_history = get_chat_history_by_session_id(session_id)
            if not chat_history:
                raise HTTPException(status_code=404, detail="No chat history found for the session.")
            return {"session_id": session_id, "history": [chat_history]}
        else:
            # Return all chat histories if no session_id is provided
            all_histories = get_all_chats()  # Ensure this function returns all chat histories
            return {"history": all_histories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_session(data: ChatMessage):
    """Reset in-memory chat session for a specific session_id."""
    session_id = data.session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
    try:
        conversation.sessions[session_id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        return {"message": "Chat session reset successfully.", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_chat")
async def delete_chat(data: ChatMessage):
    """Delete a specific chat log."""
    chat_id = data.message  # Assuming the message here represents the chat ID
    
    if not chat_id:
        raise HTTPException(status_code=400, detail="Chat ID is required")
    
    try:
        deleted = delete_chat_by_id(chat_id)
        if deleted:
            return {"message": "Chat deleted successfully."}
        else:
            raise HTTPException(status_code=404, detail="Chat not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def home():
    """Home route for testing."""
    return {"message": "Welcome to the FastAPI Chatbot API!"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
