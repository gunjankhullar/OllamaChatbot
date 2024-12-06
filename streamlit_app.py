import streamlit as st
import httpx
import uuid

# API Base URL
API_URL = "http://localhost:8000"

# Initialize session state for tracking chats and current chat session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None  
if "temp_user_input" not in st.session_state:
    st.session_state.temp_user_input = ""  

# Function to start a new chat
def start_new_chat():
    new_chat_id = f"Chat {len(st.session_state.chat_history) + 1}"
    
    if new_chat_id not in st.session_state.chat_history:
        session_id = str(uuid.uuid4())  
        st.session_state.chat_history[new_chat_id] = {"session_id": session_id, "messages": []} 
    st.session_state.current_chat = new_chat_id  
    st.session_state.temp_user_input = "" 

# Function to get assistant's response from FastAPI (server-side logic for chat)
def get_assistant_response(user_message):
    if st.session_state.current_chat:
      
        chat_session_id = st.session_state.chat_history[st.session_state.current_chat]["session_id"]
        payload = {"message": user_message, "session_id": chat_session_id}
        try:
            response = httpx.post(f"{API_URL}/chat", json=payload, timeout=500.0)
            if response.status_code == 200:
                response_data = response.json()
                return response_data["answer"]
            else:
                return "Sorry, there was an error with the model response."
        except Exception as e:
            return f"Error: {str(e)}"

# Function to handle message sending
def send_message():
    if st.session_state.current_chat:
        message = st.session_state.temp_user_input.strip()
        if message:
            st.session_state.chat_history[st.session_state.current_chat]["messages"].append(
                {"role": "user", "content": message}
            )

            assistant_response = get_assistant_response(message)
            st.session_state.chat_history[st.session_state.current_chat]["messages"].append(
                {"role": "assistant", "content": assistant_response}
            )

        st.session_state.temp_user_input = ""  # Clear the input field

# Sidebar for managing chat sessions
st.sidebar.title("Chat Sessions")
if st.sidebar.button("Start New Chat"):
    start_new_chat()

# List existing chats in the sidebar
for chat_id in st.session_state.chat_history.keys():
    if st.sidebar.button(chat_id):
        st.session_state.current_chat = chat_id

# Main conversation UI
if st.session_state.current_chat:
    st.title(f"Chat - {st.session_state.current_chat}")

    # Display the chat history for the current chat
    for msg in st.session_state.chat_history[st.session_state.current_chat]["messages"]:
        if "role" in msg:
            role = msg['role']
            content = msg['content']
            st.markdown(f"**{role.capitalize()}**: {content}")

    # Text input for user message
    st.text_input("Your message:", key="temp_user_input", on_change=send_message)

# Display "Create New Chat" heading when no chat has been started, centered
if st.session_state.current_chat is None:
    st.markdown("<h1 style='text-align: center;'>Create New Chat</h1>", unsafe_allow_html=True)
