# st v1.0
1. POST /api/upload
- Upload file
` Request: multipart/form-data with 'file' and 'session_id'
 Response: {"file_id": "abc123", "status": "success"}`
2. POST /api/chat
 Send chat message
 `Request: {
   "message": "user question",
   "session_id": "20240101120000",
   "settings": {"temperature": 0.7, "max_tokens": 1000, "use_rag": true},
   "file_ids": ["file1.txt"],
   "chat_history": [{"role": "user", "content": "..."}]
 }
 Response: {"response": "AI answer", "sources": ["doc1.pdf", "doc2.txt"]}`
3. DELETE /api/files
Clear files for session
 `Request: {"session_id": "20240101120000"}
 Response: {"status": "success"}`

To Run:
bashpip install streamlit requests
streamlit run app.py