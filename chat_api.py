from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from mcp_service import mcp_service
from llm_engine import llm_engine
from models import Message
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Chat API with OpenAI")

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
        logger.info(f"Received message: {request.message}")
        
        # Try MCP first
        try:
            result = await mcp_service.process_with_mcp(request.message)
            logger.info(f"MCP result: {result}")
            
            if result and len(result) > 0:
                # Get final answer from LLM with tool context
                final_response_data = await llm_engine.chat_completion(
                    result, 
                    session_id="chat_final"
                )
                final_response = final_response_data["choices"][0]["message"]["content"]
                logger.info(f"Final response generated")
                return ChatResponse(response=final_response)
        except Exception as mcp_error:
            logger.warning(f"MCP processing failed: {mcp_error}")
            import traceback
            traceback.print_exc()
        
        # Fallback to direct LLM without tools
        logger.info("Falling back to direct LLM...")
        messages = [
            Message(role="system", content="אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד."),
            Message(role="user", content=request.message)
        ]
        
        response_data = await llm_engine.chat_completion(messages, session_id="chat_direct")
        final_response = response_data["choices"][0]["message"]["content"]
        logger.info(f"Direct response generated")
        return ChatResponse(response=final_response)
            
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming endpoint for chat responses"""
    async def generate():
        try:
            logger.info(f"Received streaming message: {request.message}")
            
            # Try MCP first
            try:
                result = await mcp_service.process_with_mcp(request.message)
                logger.info(f"MCP result: {result}")
                
                if result and len(result) > 0:
                    # Stream the final response from LLM
                    async for chunk in llm_engine.chat_stream(result, session_id="chat_final"):
                        yield chunk
                    return
            except Exception as mcp_error:
                logger.warning(f"MCP processing failed: {mcp_error}")
            
            # Fallback to direct LLM with streaming
            logger.info("Falling back to streaming LLM...")
            messages = [
                Message(role="system", content="אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד."),
                Message(role="user", content=request.message)
            ]
            
            async for chunk in llm_engine.chat_stream(messages, session_id="chat_direct"):
                yield chunk
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            import traceback
            traceback.print_exc()
            yield f'data: {{"error": "Internal server error"}}\n\n'
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
