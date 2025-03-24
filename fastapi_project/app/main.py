from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
import os

from .database import get_db
from .models import Link
from .redis_client import get_cache
from datetime import datetime

app = FastAPI(
    title="URL Shortener API",
    description="Сервис сокращения ссылок",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from .routers import auth, links

# Register routers
app.include_router(auth.router)
app.include_router(links.router)

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в URL Shortener API"}

# Корневой маршрут для работы с короткими ссылками (redirect)
@app.get("/{short_code}")
async def redirect(short_code: str, request: Request, db = Depends(get_db)):
    """
    Обрабатывает короткий URL и перенаправляет на соответствующий оригинальный URL
    """
    # Вместо использования url_path_for напрямую вызываем функцию redirect_to_original
    return await links.redirect_to_original(short_code=short_code, request=request, db=db)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)