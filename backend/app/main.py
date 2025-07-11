from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.services.notification import notification_service
import asyncio

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    # 알림 서비스 시작
    await notification_service.start()
    
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    # 알림 서비스 종료
    await notification_service.stop()