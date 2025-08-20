# api/main.py
from fastapi import FastAPI
from api.models import KeywordResponse, Brief, WriterNotes
from typing import Dict, Any
from services import fetch_serp_snapshot  # already have
from brief_renderer import brief_to_markdown
from parsing import parse_brief_output
from services import generate_writer_notes

app = FastAPI(title="Keyword & Brief API")

@app.get("/health")
def health(): return {"ok": True}

# You can fill implementations later; keep contracts stable.
