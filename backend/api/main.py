# backend/api/main.py

from fastapi import FastAPI
from backend.api import processing

app = FastAPI()

# Mount your processing routes
app.include_router(processing.router, prefix="/api")

# To run the app, use:
# uvicorn backend.api.main:app --reload