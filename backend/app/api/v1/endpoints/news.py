from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from app.core.supabase import get_supabase_client
from app.services.news import NewsPipeline
from app.services.ai import NewsAnalyzer, CostTracker, BatchAnalyzer
from app.services.sentiment import SentimentPipeline
import os
import logging

logger = logging.getLogger(__name__)

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
    
    # 비용 추적기 초기화
    cost_tracker = CostTracker()
    
    try:
        # Get article content
        article_response = supabase.table("news_articles").select("*").eq("id", request.article_id).single().execute()
        article = article_response.data
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Check user's daily limit
        user_response = supabase.table("users").select("subscription_tier").eq("id", request.user_id).single().execute()
        user = user_response.data
        user_tier = user.get("subscription_tier", "free")
        
        # 제한 확인
        allowed, limit_reason = await cost_tracker.check_limits(request.user_id, user_tier)
        if not allowed:
            raise HTTPException(status_code=429, detail=limit_reason)
        
        # AI 분석 수행
        analyzer = NewsAnalyzer(cost_tracker=cost_tracker)
        analysis_result = await analyzer.analyze_article(
            article_id=request.article_id,
            article_title=article['title'],
            article_content=article['content'],
            user_id=request.user_id
        )
        
        if "error" in analysis_result:
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # 사용자 분석 기록 저장
        supabase.table("user_analyses").insert({
            "user_id": request.user_id,
            "article_id": request.article_id,
            "analysis_result": analysis_result
        }).execute()
        
        # 응답 구성
        return AIAnalysisResponse(
            article_id=request.article_id,
            summary=analysis_result.get("summary", ""),
            key_companies=analysis_result.get("companies_mentioned", []),
            impact_analysis=analysis_result.get("market_impact", {}),
            sentiment=analysis_result.get("sentiment", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
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

class CollectNewsRequest(BaseModel):
    sources: Optional[List[str]] = None  # ['rss', 'google']
    
class CollectNewsResponse(BaseModel):
    message: str
    task_id: Optional[str] = None

@router.post("/collect", response_model=CollectNewsResponse)
async def collect_news(
    request: CollectNewsRequest,
    background_tasks: BackgroundTasks
):
    """뉴스 수집 작업 시작 (백그라운드)"""
    
    async def _collect_news_task():
        pipeline = NewsPipeline()
        try:
            stats = await pipeline.process_pipeline(sources=request.sources)
            print(f"News collection completed: {stats}")
        except Exception as e:
            print(f"Error in news collection: {str(e)}")
    
    # 백그라운드 작업으로 실행
    background_tasks.add_task(_collect_news_task)
    
    return CollectNewsResponse(
        message="News collection started in background",
        task_id="manual_collection"
    )

@router.get("/stats/collection")
async def get_collection_stats():
    """뉴스 수집 통계"""
    supabase = get_supabase_client()
    
    try:
        # 오늘 수집된 기사 수
        today_response = supabase.table("news_articles")\
            .select("id", count="exact")\
            .gte("created_at", datetime.now().date().isoformat())\
            .execute()
            
        # 처리된 기사 수
        processed_response = supabase.table("news_articles")\
            .select("id", count="exact")\
            .eq("processed", True)\
            .execute()
            
        # 소스별 통계
        source_stats = supabase.table("news_articles")\
            .select("source")\
            .execute()
            
        source_counts = {}
        for article in source_stats.data:
            source = article['source']
            source_counts[source] = source_counts.get(source, 0) + 1
            
        return {
            "today_collected": today_response.count,
            "total_processed": processed_response.count,
            "sources": source_counts,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BatchAnalysisRequest(BaseModel):
    article_ids: List[int]
    user_id: str

class BatchAnalysisResponse(BaseModel):
    total: int
    successful: int
    failed: int
    summary: Dict[str, Any]

@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(request: BatchAnalysisRequest):
    """여러 기사를 배치로 분석"""
    supabase = get_supabase_client()
    
    # 사용자 티어 확인
    user_response = supabase.table("users").select("subscription_tier").eq("id", request.user_id).single().execute()
    user = user_response.data
    user_tier = user.get("subscription_tier", "free")
    
    # Free 티어는 배치 분석 불가
    if user_tier == "free":
        raise HTTPException(status_code=403, detail="Batch analysis is only available for premium users")
    
    # 배치 크기 제한
    max_batch_size = 10 if user_tier == "premium" else 50
    if len(request.article_ids) > max_batch_size:
        raise HTTPException(status_code=400, detail=f"Maximum batch size is {max_batch_size} articles")
    
    # 배치 분석 수행
    batch_analyzer = BatchAnalyzer()
    result = await batch_analyzer.analyze_batch(
        article_ids=request.article_ids,
        user_id=request.user_id
    )
    
    return BatchAnalysisResponse(
        total=result["total"],
        successful=result["successful"],
        failed=result["failed"],
        summary=result["summary"]
    )

@router.get("/ai/usage")
async def get_ai_usage(user_id: str = Query(..., description="User ID")):
    """AI 사용량 통계 조회"""
    cost_tracker = CostTracker()
    stats = await cost_tracker.get_usage_stats(user_id)
    return stats

@router.get("/ai/usage/global")
async def get_global_ai_usage():
    """전체 시스템 AI 사용량 통계"""
    cost_tracker = CostTracker()
    stats = await cost_tracker.get_global_stats()
    return stats

@router.get("/sentiment/market")
async def get_market_sentiment(
    hours: int = Query(24, description="Time window in hours"),
    company_id: Optional[int] = Query(None, description="Specific company ID")
):
    """시장 감정 지표 조회"""
    sentiment_pipeline = SentimentPipeline(enable_gpu=False)
    sentiment = await sentiment_pipeline.get_market_sentiment(
        time_window_hours=hours,
        company_id=company_id
    )
    return sentiment

@router.post("/sentiment/analyze/{article_id}")
async def analyze_article_sentiment(
    article_id: int,
    background_tasks: BackgroundTasks
):
    """특정 기사 감정 분석 (백그라운드)"""
    
    async def _analyze_sentiment():
        sentiment_pipeline = SentimentPipeline(enable_gpu=False)
        supabase = get_supabase_client()
        
        # 기사 조회
        response = supabase.table("news_articles")\
            .select("title, content")\
            .eq("id", article_id)\
            .single()\
            .execute()
            
        if response.data:
            article = response.data
            await sentiment_pipeline.analyze_article(
                article_id=article_id,
                title=article["title"],
                content=article["content"],
                force_reanalysis=True
            )
    
    background_tasks.add_task(_analyze_sentiment)
    
    return {
        "message": f"Sentiment analysis started for article {article_id}",
        "article_id": article_id
    }