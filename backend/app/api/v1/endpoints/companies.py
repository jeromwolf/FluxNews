from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
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

class CompanyRelationship(BaseModel):
    id: int
    company_id_1: int
    company_id_2: int
    relationship_type: str
    description: Optional[str] = None

class NetworkNode(BaseModel):
    id: int
    name: str
    ticker: str
    sector: str
    x: Optional[float] = None
    y: Optional[float] = None

class NetworkEdge(BaseModel):
    source: int
    target: int
    type: str
    weight: float = 1.0

class CompanyNetwork(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]

@router.get("/network", response_model=CompanyNetwork)
async def get_company_network(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    max_companies: int = Query(50, description="Maximum number of companies to include")
):
    supabase = get_supabase_client()
    
    try:
        # Get companies
        company_query = supabase.table("companies").select("*")
        if sector:
            company_query = company_query.eq("sector", sector)
        company_query = company_query.limit(max_companies)
        companies_response = company_query.execute()
        
        companies = companies_response.data
        company_ids = [c["id"] for c in companies]
        
        # Get relationships for these companies
        relationships_response = supabase.table("company_relationships")\
            .select("*")\
            .in_("company_id_1", company_ids)\
            .in_("company_id_2", company_ids)\
            .execute()
        
        # Create network nodes
        nodes = []
        for i, company in enumerate(companies):
            # Simple circular layout
            import math
            angle = (2 * math.pi * i) / len(companies)
            nodes.append(NetworkNode(
                id=company["id"],
                name=company["name"],
                ticker=company["ticker"],
                sector=company["sector"],
                x=math.cos(angle) * 100,
                y=math.sin(angle) * 100
            ))
        
        # Create network edges
        edges = []
        for rel in relationships_response.data:
            edges.append(NetworkEdge(
                source=rel["company_id_1"],
                target=rel["company_id_2"],
                type=rel["relationship_type"],
                weight=1.0
            ))
        
        return CompanyNetwork(nodes=nodes, edges=edges)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_companies(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Number of results")
):
    supabase = get_supabase_client()
    
    try:
        # Search in name and ticker
        response = supabase.table("companies")\
            .select("*")\
            .or_(f"name.ilike.%{q}%,ticker.ilike.%{q}%")\
            .limit(limit)\
            .execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))