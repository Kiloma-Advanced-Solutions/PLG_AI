from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from mcp_client import mcp_service
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MCP Chat API")

# Initialize OpenAI client for fallback
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"Received message: {request.message}")
        
        # Try MCP first
        try:
            result = await mcp_service.process_with_mcp(request.message)
            print(f"MCP result: {result}")
            
            if result and len(result) > 0:
                # Extract the final response from the last message
                final_response = result[-1]["content"]
                return ChatResponse(response=final_response)
        except Exception as mcp_error:
            print(f"MCP processing failed: {mcp_error}")
        
        # Fallback to direct OpenAI
        print("Falling back to direct OpenAI...")
        messages = [
            {"role": "system", "content": "אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד."},
            {"role": "user", "content": request.message}
        ]
        
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        final_response = response.choices[0].message.content
        print(f"Final response from OpenAI: {final_response}")
        return ChatResponse(response=final_response)
            
    except Exception as e:
        print(f"Error processing chat request: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
