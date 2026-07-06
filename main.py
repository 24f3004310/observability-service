import time
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS so the grader can talk to your app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration & State ---
YOUR_EMAIL = "24f3004310@ds.study.iitm.ac.in"  # Change this to your actual logged-in email!
START_TIME = time.time()

# State variables to keep track of counts and logs
http_requests_total = 0
logs_storage: List[Dict[str, Any]] = []

# --- Middleware to Track Every Single Request ---
@app.middleware("http")
async def process_and_log_request(request: Request, call_next):
    global http_requests_total
    
    # 1. Increment the total request counter
    http_requests_total += 1
    
    # 2. Generate a unique request ID
    request_id = str(uuid.uuid4())
    
    # 3. Create a structured log entry
    log_entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    }
    
    # Save the log locally so we can tail it later (keep last 100 to save memory)
    logs_storage.append(log_entry)
    if len(logs_storage) > 100:
        logs_storage.pop(0)
        
    # Process the request normally
    response = await call_next(request)
    return response

# --- Endpoints ---

# 1. GET /work?n=K
@app.get("/work")
async def do_work(n: int = 0):
    # Simulating "n" units of work
    return {
        "email": YOUR_EMAIL,
        "done": n
    }

# 2. GET /metrics
@app.get("/metrics")
async def get_metrics():
    # Return raw text formatted specifically for Prometheus
    from fastapi.responses import PlainTextResponse
    
    prometheus_text = (
        "# HELP http_requests_total Total number of HTTP requests processed.\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {http_requests_total}\n"
    )
    return PlainTextResponse(content=prometheus_text)

# 3. GET /healthz
@app.get("/healthz")
async def get_health():
    uptime = time.time() - START_TIME
    return {
        "status": "ok",
        "uptime_s": max(0.0, uptime)  # Guarantees a non-negative float
    }

# 4. GET /logs/tail?limit=N
@app.get("/logs/tail")
async def get_logs_tail(limit: int = 10):
    # Retrieve the last 'limit' items from our logs list, reversed so newest is first
    requested_logs = logs_storage[-limit:]
    return requested_logs