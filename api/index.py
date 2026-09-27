"""
Vercel Serverless Function Entry Point for ProCom API.
This module exposes the FastAPI app as a Vercel-compatible handler.
"""
from backend.main import app

# Vercel expects a variable named `app` or `handler`
# FastAPI is ASGI-compatible, which Vercel's Python runtime supports natively.
handler = app
