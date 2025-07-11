from fastapi import APIRouter
from app.api.v1.endpoints import auth, companies, news, watchlist, notifications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])