from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
from app.core.supabase import get_supabase_client
import os
import openai

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

class AIAnalysisRequest(BaseModel):
    article_id: int
    user_id: str

class AIAnalysisResponse(BaseModel):
    article_id: int
    summary: str
    key_companies: List[Dict[str, any]]
    impact_analysis: Dict[str, any]
    sentiment: Dict[str, float]

@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_article(request: AIAnalysisRequest):
    supabase = get_supabase_client()
    
    try:
        # Get article content
        article_response = supabase.table("news_articles").select("*").eq("id", request.article_id).single().execute()
        article = article_response.data
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Check user's daily limit (for free tier)
        user_response = supabase.table("users").select("subscription_tier").eq("id", request.user_id).single().execute()
        user = user_response.data
        
        if user.get("subscription_tier") == "free":
            # Check daily analysis count
            today = datetime.now().date()
            analysis_count = supabase.table("user_analyses").select("id").eq("user_id", request.user_id).gte("created_at", today).count().execute()
            
            if analysis_count.count >= 3:
                raise HTTPException(status_code=429, detail="Daily analysis limit reached for free tier")
        
        # Perform AI analysis
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        
        prompt = f"""
        Analyze this news article for investment insights:
        Title: {article['title']}
        Content: {article['content']}
        
        Provide:
        1. A brief summary (2-3 sentences)
        2. Key companies mentioned and their roles
        3. Potential impact on each company's stock
        4. Overall sentiment (positive/negative/neutral with confidence score)
        
        Focus on Korean mobility and robotics companies if mentioned.
        Return as structured JSON.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        analysis = response.choices[0].message.content
        
        # Store analysis record
        supabase.table("user_analyses").insert({
            "user_id": request.user_id,
            "article_id": request.article_id,
            "analysis_result": analysis
        }).execute()
        
        # Parse and return structured response
        import json
        analysis_data = json.loads(analysis)
        
        return AIAnalysisResponse(
            article_id=request.article_id,
            summary=analysis_data.get("summary", ""),
            key_companies=analysis_data.get("companies", []),
            impact_analysis=analysis_data.get("impact", {}),
            sentiment=analysis_data.get("sentiment", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{article_id}", response_model=NewsArticle)
async def get_article(article_id: int):
    supabase = get_supabase_client()
    try:
        response = supabase.table("news_articles").select("*").eq("id", article_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Article not found")
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))