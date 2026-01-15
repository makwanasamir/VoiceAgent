import os
import sys
import logging
import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
from knowledge_base import KnowledgeBase

load_dotenv()

# --- Logging Setup ---
class InterceptHandler(logging.Handler):
    """Redirects standard logging to Loguru."""
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(os.path.join(LOG_DIR, "voice_agent_{time}.log"), rotation="100 MB", level="DEBUG")
logging.basicConfig(handlers=[InterceptHandler()], level=0)
logging.getLogger("uvicorn").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]

# --- FastAPI App ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Azure Configuration ---
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, DEPLOYMENT_NAME]):
    logger.error("Missing required environment variables. Please check .env file.")
    raise ValueError("Missing required environment variables.")

hostname = AZURE_OPENAI_ENDPOINT.replace("https://", "").replace("http://", "").rstrip("/")
if "/" in hostname:
    hostname = hostname.split("/")[0]

# --- Knowledge Base ---
kb = KnowledgeBase()

# --- Models ---
class SearchQuery(BaseModel):
    query: str

class TranscriptLog(BaseModel):
    role: str
    text: str

# --- Endpoints ---
@app.get("/")
async def get():
    """Serve the frontend."""
    with open("index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/config")
async def get_config():
    """Returns Azure configuration for the frontend."""
    return JSONResponse(content={
        "hostname": hostname,
        "deployment": DEPLOYMENT_NAME,
        "apiKey": AZURE_OPENAI_API_KEY
    })

@app.get("/session")
async def get_session_token():
    """Fetches an ephemeral token from Azure OpenAI for WebRTC."""
    logger.info("Fetching ephemeral session token...")
    
    token_url = f"https://{hostname}/openai/v1/realtime/client_secrets"
    headers = {
        "api-key": AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    
    session_config = {
        "session": {
            "type": "realtime",
            "model": DEPLOYMENT_NAME,
            "instructions": (
                "You are a senior concierge voice agent for Aeroméxico airlines. "
                "1. LANGUAGE: Start in ENGLISH. If user speaks other languages, switch to them. "
                "2. STYLE: Be professional, empathetic, concise (1-2 sentences). "
                "3. KNOWLEDGE: You know Aeroméxico policies (baggage, pets, fare families, lounges). "
                "4. LIMITATIONS: You cannot book flights or check real-time schedules. Be upfront about this. "
                "5. PATIENCE: Wait for user to finish speaking before responding."
            ),
            "audio": {
                "output": {
                    "voice": "shimmer"
                }
            }
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, headers=headers, json=session_config, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully obtained ephemeral token.")
            return JSONResponse(content={
                "token": data.get("value"),
                "expires_at": data.get("expires_at"),
                "session_id": data.get("id")
            })
    except Exception as e:
        logger.error(f"Token fetch error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/log_transcript")
async def log_transcript(log: TranscriptLog):
    """Log transcript from the client."""
    logger.info(f"[TRANSCRIPT] {log.role.upper()}: {log.text}")
    return JSONResponse({"status": "logged"})

@app.post("/search_kb")
async def search_knowledge_base(query: SearchQuery):
    """Search the knowledge base."""
    logger.info(f"KB Search: '{query.query}'")
    result = kb.search(query.query)
    return JSONResponse(content={"result": result})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
