# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import brief, serp, keywords, suggestions

# Optional: log routes on startup to aid debugging 404s
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Startup
    try:
        print("Registered routes:")
        for r in app.routes:
            path = getattr(r, "path", None)
            methods = sorted(getattr(r, "methods", []) or [])
            if path:
                print(f"  {path}  methods={methods}")
    except Exception as e:
        print(f"Route logging error: {e}")
    yield
    # Shutdown (if needed)

app = FastAPI(title="Keyword & Brief API", version="0.1.0", lifespan=lifespan)

# CORS for local Next.js later (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # in prod: set to your domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brief.router, prefix="/generate-brief")
app.include_router(serp.router, prefix="/serp")
app.include_router(keywords.router, prefix="/suggest-keywords")
app.include_router(suggestions.router, prefix="/suggestions")

@app.get("/")
def root():
    return {"status": "ok", "endpoints": [
        "/",
        "/ping",
        "/health",
        "/docs",
        "/redoc",
    ]}

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/health")
def health(): return {"ok": True}

# You can fill implementations later; keep contracts stable.


if __name__ == "__main__":
    # Allows: `python api/main.py` for quick local run
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
