"""뉴스 API 엔드포인트 테스트"""
import pytest
from fastapi import status

class TestNewsAPI:
    """뉴스 API 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_news_list(self, async_client, mock_supabase):
        """뉴스 목록 조회 테스트"""
        # Mock 데이터 설정
        mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
            {
                "id": 1,
                "title": "Test News 1",
                "content": "Content 1",
                "published_date": "2025-01-12T10:00:00Z"
            },
            {
                "id": 2,
                "title": "Test News 2",
                "content": "Content 2",
                "published_date": "2025-01-12T11:00:00Z"
            }
        ]
        
        # API 호출
        response = await async_client.get("/api/v1/news")
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "Test News 1"
    
    @pytest.mark.asyncio
    async def test_get_news_by_id(self, async_client, mock_supabase, test_news_article):
        """개별 뉴스 조회 테스트"""
        # Mock 데이터 설정
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = test_news_article
        
        # API 호출
        response = await async_client.get(f"/api/v1/news/{test_news_article['id']}")
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_news_article["id"]
        assert data["title"] == test_news_article["title"]
    
    @pytest.mark.asyncio
    async def test_get_news_not_found(self, async_client, mock_supabase):
        """존재하지 않는 뉴스 조회 테스트"""
        # Mock 데이터 설정
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        # API 호출
        response = await async_client.get("/api/v1/news/999")
        
        # 검증
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_analyze_news(self, async_client, mock_supabase, mock_openai, auth_headers):
        """뉴스 AI 분석 테스트"""
        # Mock 데이터 설정
        mock_openai.complete.return_value = {
            "result": {
                "companies": ["현대자동차", "LG전자"],
                "sentiment": "positive",
                "impact_score": 0.8
            },
            "usage": {"total_tokens": 150}
        }
        
        # 요청 데이터
        request_data = {
            "article_id": 1,
            "content": "현대자동차와 LG전자가 전기차 배터리 협력을 발표했다."
        }
        
        # API 호출
        response = await async_client.post(
            "/api/v1/news/analyze",
            json=request_data,
            headers=auth_headers
        )
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "companies" in data["analysis"]
        assert len(data["analysis"]["companies"]) == 2
        assert data["analysis"]["sentiment"] == "positive"
    
    @pytest.mark.asyncio
    async def test_get_company_news(self, async_client, mock_supabase):
        """기업별 뉴스 조회 테스트"""
        # Mock 데이터 설정
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {
                "article_id": 1,
                "impact_score": 0.9,
                "news_articles": {
                    "title": "현대차 전기차 판매 급증",
                    "published_date": "2025-01-12T10:00:00Z"
                }
            }
        ]
        
        # API 호출
        response = await async_client.get("/api/v1/news/company/1")
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["impacts"]) == 1
        assert data["impacts"][0]["impact_score"] == 0.9