from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.core.supabase import get_supabase_client

router = APIRouter()

class Company(BaseModel):
    id: int
    name: str
    ticker: str
    sector: str
    country: str
    description: Optional[str] = None

@router.get("/", response_model=List[Company])
async def get_companies(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    limit: int = Query(20, description="Number of companies to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    supabase = get_supabase_client()
    try:
        query = supabase.table("companies").select("*")
        
        if sector:
            query = query.eq("sector", sector)
        
        query = query.limit(limit).offset(offset)
        response = query.execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}", response_model=Company)
async def get_company(company_id: int):
    supabase = get_supabase_client()
    try:
        response = supabase.table("companies").select("*").eq("id", company_id).single().execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=404, detail="Company not found")

@router.get("/{company_id}/relationships")
async def get_company_relationships(company_id: int):
    supabase = get_supabase_client()
    try:
        response = supabase.table("company_relationships").select("*").or_(f"company_id_1.eq.{company_id},company_id_2.eq.{company_id}").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))