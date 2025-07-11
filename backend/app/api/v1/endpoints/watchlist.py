from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.core.supabase import get_supabase_client

router = APIRouter()

class WatchlistItem(BaseModel):
    id: int
    user_id: str
    company_id: int
    alert_enabled: bool = False
    alert_threshold: Optional[float] = None
    created_at: datetime

class AddToWatchlist(BaseModel):
    company_id: int
    alert_enabled: bool = False
    alert_threshold: Optional[float] = None

class UpdateWatchlistItem(BaseModel):
    alert_enabled: Optional[bool] = None
    alert_threshold: Optional[float] = None

class WatchlistCompany(BaseModel):
    id: int
    user_id: str
    company_id: int
    company_name: str
    company_ticker: str
    company_sector: str
    alert_enabled: bool
    alert_threshold: Optional[float]
    created_at: datetime
    recent_impact_score: Optional[float] = None

@router.get("/", response_model=List[WatchlistCompany])
async def get_user_watchlist(user_id: str):
    supabase = get_supabase_client()
    
    try:
        # Get watchlist items with company details
        response = supabase.table("user_watchlists")\
            .select("*, companies(*)")\
            .eq("user_id", user_id)\
            .execute()
        
        # Format response with company details
        watchlist_companies = []
        for item in response.data:
            company = item.get("companies", {})
            
            # Get recent impact score
            impact_response = supabase.table("news_company_impacts")\
                .select("impact_score")\
                .eq("company_id", item["company_id"])\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            recent_impact = impact_response.data[0]["impact_score"] if impact_response.data else None
            
            watchlist_companies.append(WatchlistCompany(
                id=item["id"],
                user_id=item["user_id"],
                company_id=item["company_id"],
                company_name=company.get("name", ""),
                company_ticker=company.get("ticker", ""),
                company_sector=company.get("sector", ""),
                alert_enabled=item["alert_enabled"],
                alert_threshold=item["alert_threshold"],
                created_at=item["created_at"],
                recent_impact_score=recent_impact
            ))
        
        return watchlist_companies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def add_to_watchlist(user_id: str, item: AddToWatchlist):
    supabase = get_supabase_client()
    
    try:
        # Check user's tier and current watchlist count
        user_response = supabase.table("users").select("subscription_tier").eq("id", user_id).single().execute()
        user = user_response.data
        
        # Count current watchlist items
        count_response = supabase.table("user_watchlists").select("id", count="exact").eq("user_id", user_id).execute()
        current_count = count_response.count
        
        # Check limits based on tier
        if user.get("subscription_tier") == "free" and current_count >= 3:
            raise HTTPException(status_code=400, detail="Watchlist limit reached for free tier (3 companies)")
        elif user.get("subscription_tier") == "premium" and current_count >= 50:
            raise HTTPException(status_code=400, detail="Watchlist limit reached for premium tier (50 companies)")
        
        # Check if company already in watchlist
        existing = supabase.table("user_watchlists")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("company_id", item.company_id)\
            .execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail="Company already in watchlist")
        
        # Add to watchlist
        response = supabase.table("user_watchlists").insert({
            "user_id": user_id,
            "company_id": item.company_id,
            "alert_enabled": item.alert_enabled,
            "alert_threshold": item.alert_threshold
        }).execute()
        
        return {"message": "Company added to watchlist", "id": response.data[0]["id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{watchlist_id}")
async def update_watchlist_item(watchlist_id: int, user_id: str, updates: UpdateWatchlistItem):
    supabase = get_supabase_client()
    
    try:
        # Verify ownership
        existing = supabase.table("user_watchlists")\
            .select("id")\
            .eq("id", watchlist_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Watchlist item not found")
        
        # Update fields
        update_data = {}
        if updates.alert_enabled is not None:
            update_data["alert_enabled"] = updates.alert_enabled
        if updates.alert_threshold is not None:
            update_data["alert_threshold"] = updates.alert_threshold
        
        response = supabase.table("user_watchlists")\
            .update(update_data)\
            .eq("id", watchlist_id)\
            .execute()
        
        return {"message": "Watchlist item updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{watchlist_id}")
async def remove_from_watchlist(watchlist_id: int, user_id: str):
    supabase = get_supabase_client()
    
    try:
        # Verify ownership and delete
        response = supabase.table("user_watchlists")\
            .delete()\
            .eq("id", watchlist_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Watchlist item not found")
        
        return {"message": "Company removed from watchlist"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_triggered_alerts(user_id: str):
    supabase = get_supabase_client()
    
    try:
        # Get user's watchlist with alerts enabled
        watchlist_response = supabase.table("user_watchlists")\
            .select("*, companies(*)")\
            .eq("user_id", user_id)\
            .eq("alert_enabled", True)\
            .execute()
        
        triggered_alerts = []
        
        for item in watchlist_response.data:
            if item["alert_threshold"]:
                # Check recent impacts above threshold
                impacts_response = supabase.table("news_company_impacts")\
                    .select("*, news_articles(*)")\
                    .eq("company_id", item["company_id"])\
                    .gte("impact_score", item["alert_threshold"])\
                    .order("created_at", desc=True)\
                    .limit(5)\
                    .execute()
                
                if impacts_response.data:
                    for impact in impacts_response.data:
                        triggered_alerts.append({
                            "company_name": item["companies"]["name"],
                            "company_ticker": item["companies"]["ticker"],
                            "impact_score": impact["impact_score"],
                            "threshold": item["alert_threshold"],
                            "article_title": impact["news_articles"]["title"],
                            "article_date": impact["news_articles"]["published_date"],
                            "explanation": impact.get("explanation", "")
                        })
        
        return triggered_alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))