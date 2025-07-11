from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.core.supabase import get_supabase_client

router = APIRouter()

class NewsArticle(BaseModel):
    id: int
    title: str
    content: str
    url: str
    source: str
    published_date: datetime
    sentiment_score: Optional[float] = None
    processed: bool = False

class NewsImpact(BaseModel):
    article_id: int
    company_id: int
    impact_score: float
    confidence_score: float
    explanation: str

@router.get("/", response_model=List[NewsArticle])
async def get_news_feed(
    limit: int = Query(20, description="Number of articles to return"),
    offset: int = Query(0, description="Offset for pagination"),
    processed_only: bool = Query(True, description="Only return processed articles")
):
    supabase = get_supabase_client()
    try:
        query = supabase.table("news_articles").select("*")
        
        if processed_only:
            query = query.eq("processed", True)
        
        query = query.order("published_date", desc=True).limit(limit).offset(offset)
        response = query.execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{article_id}/impacts", response_model=List[NewsImpact])
async def get_article_impacts(article_id: int):
    supabase = get_supabase_client()
    try:
        response = supabase.table("news_company_impacts").select("*").eq("article_id", article_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company/{company_id}", response_model=List[NewsArticle])
async def get_company_news(
    company_id: int,
    limit: int = Query(20, description="Number of articles to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    supabase = get_supabase_client()
    try:
        impact_response = supabase.table("news_company_impacts").select("article_id").eq("company_id", company_id).execute()
        article_ids = [impact["article_id"] for impact in impact_response.data]
        
        if not article_ids:
            return []
        
        articles_response = supabase.table("news_articles").select("*").in_("id", article_ids).order("published_date", desc=True).limit(limit).offset(offset).execute()
        
        return articles_response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))