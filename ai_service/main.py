import os
import json
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Library Management AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Note: Production url here. 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to get the client at request time so dotenv has time to load
def get_client() -> AsyncOpenAI:
    """
    Get the DeepSeek client.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL")
    
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
