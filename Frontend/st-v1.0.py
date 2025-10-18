import streamlit as st
from datetime import datetime
import json
import requests
import base64

# Page configuration
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files_info" not in st.session_state:
    st.session_state.uploaded_files_info = {}

if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")

# Sidebar for file uploads and settings
with st.sidebar:
    st.title("🤖 AI Assistant")
    st.divider()
    
    # API Configuration
    st.subheader("🔧 API Configuration")
    api_base_url = st.text_input(
        "API Base URL",
        value="http://localhost:8000",
        help="Your backend API base URL"
    )
    api_key = st.text_input(
        "API Key (Optional)",
        type="password",
        help="Enter API key if required"
    )
    
    st.divider()
    
    st.subheader("📁 Upload Files for RAG")
    uploaded_files = st.file_uploader(
        "Upload documents (PDF, TXT, CSV, JSON)",
        type=["pdf", "txt", "csv", "json"],
        accept_multiple_files=True,
        help="Upload files to enable RAG capabilities"
    )
    
    # Process uploaded files
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) selected")
        
        if st.button("📤 Upload to Backend", use_container_width=True):
            with st.spinner("Uploading files..."):
                for file in uploaded_files:
                    try:
                        # Prepare file data
                        file_content = file.read()
                        file.seek(0)  # Reset file pointer
                        
                        # Prepare multipart form data
                        files = {
                            'file': (file.name, file_content, file.type)
                        }
                        
                        # Additional metadata
                        data = {
                            'session_id': st.session_state.session_id,
                            'filename': file.name
                        }
                        
                        # Set headers
                        headers = {}
                        if api_key:
                            headers['Authorization'] = f'Bearer {api_key}'
                        
                        # Upload file to backend
                        response = requests.post(
                            f"{api_base_url}/api/upload",
                            files=files,
                            data=data,
                            headers=headers,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.uploaded_files_info[file.name] = {
                                "file_id": result.get("file_id", file.name),
                                "size": file.size,
                                "type": file.type,
                                "uploaded_at": datetime.now().isoformat()
                            }
                            st.success(f"✅ Uploaded: {file.name}")
                        else:
                            st.error(f"❌ Failed to upload {file.name}: {response.text}")
                    
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Network error uploading {file.name}: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Error uploading {file.name}: {str(e)}")
        
        if st.session_state.uploaded_files_info:
            with st.expander("View Uploaded Files"):
                for filename, info in st.session_state.uploaded_files_info.items():
                    st.write(f"📄 **{filename}**")
                    st.caption(f"Type: {info['type']} | Size: {info['size']} bytes")
                    st.caption(f"Uploaded: {info['uploaded_at']}")
                    st.divider()
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # Clear files button
    if st.button("🗑️ Clear Uploaded Files", use_container_width=True):
        if st.session_state.uploaded_files_info:
            with st.spinner("Clearing files from backend..."):
                try:
                    headers = {}
                    if api_key:
                        headers['Authorization'] = f'Bearer {api_key}'
                    
                    response = requests.delete(
                        f"{api_base_url}/api/files",
                        json={"session_id": st.session_state.session_id},
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.session_state.uploaded_files_info = {}
                        st.success("Files cleared successfully")
                    else:
                        st.error(f"Failed to clear files: {response.text}")
                except Exception as e:
                    st.error(f"Error clearing files: {str(e)}")
        st.session_state.uploaded_files_info = {}
        st.rerun()
    
    st.divider()
    
    st.subheader("⚙️ Settings")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.slider("Max Tokens", 100, 4000, 1000, 100)
    use_rag = st.checkbox("Use RAG", value=True, help="Enable retrieval from uploaded documents")
    
    st.divider()
    st.caption(f"Session ID: {st.session_state.session_id}")

# Main chat interface
st.title("💬 Chat Assistant")
st.caption("Ask me anything! Upload documents for context-aware responses.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Call backend API for response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Prepare request payload
                payload = {
                    "message": user_input,
                    "session_id": st.session_state.session_id,
                    "settings": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "use_rag": use_rag
                    },
                    "file_ids": list(st.session_state.uploaded_files_info.keys()),
                    "chat_history": st.session_state.messages[:-1]  # Exclude current message
                }
                
                # Set headers
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers['Authorization'] = f'Bearer {api_key}'
                
                # Call chat API
                response = requests.post(
                    f"{api_base_url}/api/chat",
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_message = result.get("response", "No response from backend")
                    
                    # Display response
                    st.write(assistant_message)
                    
                    # Show sources if available
                    if "sources" in result and result["sources"]:
                        with st.expander("📚 Sources"):
                            for source in result["sources"]:
                                st.write(f"- {source}")
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    error_message = f"❌ API Error ({response.status_code}): {response.text}"
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message,
                        "timestamp": datetime.now().isoformat()
                    })
            
            except requests.exceptions.Timeout:
                error_message = "⏱️ Request timed out. Please try again."
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "timestamp": datetime.now().isoformat()
                })
            
            except requests.exceptions.ConnectionError:
                error_message = f"🔌 Cannot connect to backend at {api_base_url}. Please check the API URL."
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "timestamp": datetime.now().isoformat()
                })
            
            except Exception as e:
                error_message = f"❌ Error: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "timestamp": datetime.now().isoformat()
                })

# Footer information
if len(st.session_state.messages) == 0:
    st.info("👋 Welcome! Configure your API settings and start chatting.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**1️⃣ Configure API**")
        st.caption("Set your backend API URL in the sidebar")
    with col2:
        st.write("**2️⃣ Upload Files**")
        st.caption("Add documents for RAG capabilities")
    with col3:
        st.write("**3️⃣ Start Chatting**")
        st.caption("Ask questions and get AI responses")
    
    st.divider()
    
    with st.expander("📋 Expected API Endpoints"):
        st.code("""
POST /api/upload
- Upload files for RAG
- Body: multipart/form-data with 'file' and 'session_id'
- Response: {"file_id": "...", "status": "success"}

POST /api/chat
- Send chat messages
- Body: {
    "message": "user message",
    "session_id": "session_id",
    "settings": {"temperature": 0.7, "max_tokens": 1000, "use_rag": true},
    "file_ids": ["file1.txt", "file2.pdf"],
    "chat_history": [...]
  }
- Response: {"response": "...", "sources": [...]}

DELETE /api/files
- Clear uploaded files
- Body: {"session_id": "session_id"}
- Response: {"status": "success"}
        """, language="json")