import os
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from sse_starlette.sse import EventSourceResponse
from dotenv import dotenv_values

# Initialize FastAPI App
app = FastAPI(title="Library Management AI Service")

# Setup CORS for the Django frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to get the client at request time so dotenv has time to load
def get_client() -> AsyncOpenAI:
    # Uvicorn workers sometimes strip environment variables passed via docker env_file.
    # Fallback to reading the .env file directly from the disk.
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env_vars = dotenv_values(env_path) if os.path.exists(env_path) else {}
    
    api_key = os.environ.get("DEEPSEEK_API_KEY") or env_vars.get("DEEPSEEK_API_KEY", "")
    base_url = os.environ.get("DEEPSEEK_BASE_URL") or env_vars.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    print(f"DEBUG - Resolving API Key... Found: {bool(api_key)}")
    print(f"DEBUG - Resolving Base URL... Found: {base_url}")

    if not api_key:
        print("Warning: DEEPSEEK_API_KEY is missing from environment Variables and .env file!")
        api_key = "DUMMY_KEY_TO_PREVENT_CRASH"
        
    return AsyncOpenAI(api_key=api_key, base_url=base_url)

# Define request models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

# System prompt defining bot behaviour
SYSTEM_PROMPT = """You are LibraBot, a helpful assistant for a Library Management System. 
You help users with information about borrowing books, returning books, fines, finding books in the catalogue, and library opening hours.
Keep your answers concise, friendly, and formatted nicely in HTML-compatible markdown. 
If a user asks something unrelated to the library or books, politely steer them back to library topics."""

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Endpoint that accepts a chat history array and streams back the 
    DeepSeek response using Server-Sent Events (SSE).
    """
    
    # Prepare messages payload
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in request.messages:
        api_messages.append({"role": msg.role, "content": msg.content})

    async def event_generator():
        client = get_client()
        try:
            # Create a streaming response from the DeepSeek model
            stream = await client.chat.completions.create(
                model="deepseek-chat",
                messages=api_messages,
                stream=True
            )
            
            async for chunk in stream:
                # The content delta for this chunk
                delta = chunk.choices[0].delta.content
                if delta:
                    # SSE formats data with `data: ... \n\n`
                    yield {"event": "message", "data": json.dumps({"content": delta})}
                    
        except Exception as e:
            # Handle API errors gracefully in the stream
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            yield {"event": "error", "data": json.dumps({"content": error_msg})}
            
        finally:
            yield {"event": "done", "data": json.dumps({"content": "[DONE]"})}

    return EventSourceResponse(event_generator())

@app.get("/health")
def health_check():
    return {"status": "healthy"}
