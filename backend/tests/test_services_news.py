"""뉴스 서비스 유닛 테스트"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.news.rss_parser import RSSParser
from app.services.news.google_news_collector import GoogleNewsCollector
from app.services.news.deduplication import NewsDeduplicator
from app.services.news.news_pipeline import NewsPipeline

class TestRSSParser:
    """RSS 파서 테스트"""
    
    @pytest.mark.asyncio
    async def test_parse_feed_success(self):
        """RSS 피드 파싱 성공 테스트"""
        parser = RSSParser()
        
        # Mock feedparser
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(
                entries=[
                    Mock(
                        title="Test Article 1",
                        link="https://example.com/1",
                        summary="Summary 1",
                        published_parsed=(2025, 1, 12, 10, 0, 0, 0, 0, 0)
                    ),
                    Mock(
                        title="Test Article 2",
                        link="https://example.com/2",
                        summary="Summary 2",
                        published_parsed=(2025, 1, 12, 11, 0, 0, 0, 0, 0)
                    )
                ]
            )
            
            articles = await parser.parse_feed("https://example.com/rss")
            
            assert len(articles) == 2
            assert articles[0]["title"] == "Test Article 1"
            assert articles[0]["url"] == "https://example.com/1"
            assert "published_date" in articles[0]
    
    @pytest.mark.asyncio
    async def test_fetch_all_feeds(self):
        """모든 피드 수집 테스트"""
        parser = RSSParser()
        
        with patch.object(parser, 'parse_feed', new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = [
                {"title": "Article 1", "url": "https://example.com/1"}
            ]
            
            articles = await parser.fetch_all_feeds()
            
            assert len(articles) > 0
            # 여러 피드 소스가 호출되었는지 확인
            assert mock_parse.call_count >= 2

class TestGoogleNewsCollector:
    """Google News 수집기 테스트"""
    
    @pytest.mark.asyncio
    async def test_search_news(self):
        """뉴스 검색 테스트"""
        collector = GoogleNewsCollector()
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value='<html><body>Test</body></html>')
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            with patch.object(collector, '_parse_search_results') as mock_parse:
                mock_parse.return_value = [
                    {
                        "title": "현대차 자율주행 기술 발표",
                        "url": "https://news.example.com/1",
                        "source": "Example News",
                        "published_date": datetime.utcnow()
                    }
                ]
                
                articles = await collector.search_news("현대자동차 자율주행")
                
                assert len(articles) == 1
                assert "현대차" in articles[0]["title"]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """속도 제한 테스트"""
        collector = GoogleNewsCollector()
        
        # 연속 요청 시 지연 확인
        start_time = datetime.utcnow()
        
        with patch('aiohttp.ClientSession.get', new_callable=AsyncMock):
            await collector._fetch_with_retry("https://example.com")
            await collector._fetch_with_retry("https://example.com")
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        # 최소 지연 시간 확인
        assert elapsed >= 1.0  # 최소 1초 지연

class TestNewsDeduplicator:
    """중복 제거 테스트"""
    
    def test_is_duplicate_by_url(self):
        """URL 기반 중복 확인 테스트"""
        dedup = NewsDeduplicator()
        
        articles = [
            {"url": "https://example.com/news/1", "title": "Article 1"},
            {"url": "https://example.com/news/1?utm=123", "title": "Article 1"},
            {"url": "https://example.com/news/2", "title": "Article 2"}
        ]
        
        unique = dedup.deduplicate(articles)
        
        assert len(unique) == 2
        assert unique[0]["url"] == "https://example.com/news/1"
        assert unique[1]["url"] == "https://example.com/news/2"
    
    def test_is_duplicate_by_title_similarity(self):
        """제목 유사도 기반 중복 확인 테스트"""
        dedup = NewsDeduplicator()
        
        articles = [
            {"url": "https://site1.com/1", "title": "현대차, 전기차 신모델 출시"},
            {"url": "https://site2.com/2", "title": "현대차 전기차 신모델 출시"},
            {"url": "https://site3.com/3", "title": "삼성전자 반도체 실적 발표"}
        ]
        
        unique = dedup.deduplicate(articles)
        
        assert len(unique) == 2  # 유사한 제목 하나만 포함
    
    def test_normalize_url(self):
        """URL 정규화 테스트"""
        dedup = NewsDeduplicator()
        
        url1 = "https://example.com/news?utm_source=twitter&id=123"
        url2 = "https://example.com/news?id=123&utm_campaign=social"
        
        normalized1 = dedup._normalize_url(url1)
        normalized2 = dedup._normalize_url(url2)
        
        assert normalized1 == normalized2

class TestNewsPipeline:
    """뉴스 파이프라인 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_collect_news(self, mock_supabase):
        """뉴스 수집 파이프라인 테스트"""
        pipeline = NewsPipeline()
        
        # Mock 각 수집기
        with patch.object(pipeline.rss_parser, 'fetch_all_feeds', new_callable=AsyncMock) as mock_rss:
            with patch.object(pipeline.google_collector, 'collect_trending', new_callable=AsyncMock) as mock_google:
                mock_rss.return_value = [
                    {"title": "RSS Article", "url": "https://rss.com/1"}
                ]
                mock_google.return_value = [
                    {"title": "Google Article", "url": "https://google.com/1"}
                ]
                
                # Mock 저장
                mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()
                
                result = await pipeline.collect_news()
                
                assert result["total_collected"] == 2
                assert result["rss_count"] == 1
                assert result["google_count"] == 1
                assert result["saved_count"] > 0