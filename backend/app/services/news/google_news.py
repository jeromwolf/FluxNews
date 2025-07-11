import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
import hashlib
import logging
from bs4 import BeautifulSoup
import json
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class GoogleNewsCollector:
    """Google News 수집기"""
    
    # 검색 쿼리
    SEARCH_QUERIES = {
        'korean_companies': [
            'Hyundai Motor autonomous driving',
            'Kia electric vehicle',
            'Samsung SDI battery',
            'LG Energy Solution',
            'Naver robotics',
            'Kakao Mobility',
            'Doosan Robotics',
            'Rainbow Robotics',
            '현대자동차 자율주행',
            '기아 전기차',
            '삼성SDI 배터리',
            'LG에너지솔루션',
            '네이버 로봇',
            '카카오모빌리티',
            '두산로보틱스',
            '레인보우로보틱스'
        ],
        'technology_trends': [
            'autonomous vehicle Korea',
            'robotics startup Korea',
            'EV battery technology',
            'mobility as a service Korea',
            'industrial robots Korea',
            '한국 자율주행차',
            '한국 로봇 스타트업',
            '전기차 배터리 기술',
            '한국 모빌리티',
            '산업용 로봇'
        ]
    }
    
    BASE_URL = "https://news.google.com/rss/search"
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def _generate_article_id(self, url: str, title: str) -> str:
        """기사 고유 ID 생성"""
        content = f"{url}{title}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()[:16]
        
    def _build_search_url(self, query: str, language: str = "en") -> str:
        """Google News RSS 검색 URL 생성"""
        params = {
            'q': query,
            'hl': language,
            'gl': 'KR',  # 한국 지역 뉴스 우선
            'ceid': 'KR:ko' if language == 'ko' else 'US:en'
        }
        
        query_string = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        return f"{self.BASE_URL}?{query_string}"
        
    async def fetch_articles_for_query(self, query: str, max_articles: int = 10) -> List[Dict]:
        """특정 쿼리에 대한 기사 수집"""
        articles = []
        
        # 쿼리 언어 감지 (간단한 한글 체크)
        language = 'ko' if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in query) else 'en'
        
        url = self._build_search_url(query, language)
        
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch Google News for query '{query}': HTTP {response.status}")
                    return articles
                    
                content = await response.text()
                
                # RSS 파싱
                from xml.etree import ElementTree as ET
                root = ET.fromstring(content)
                
                items = root.findall('.//item')[:max_articles]
                
                for item in items:
                    try:
                        title = item.find('title').text if item.find('title') is not None else ''
                        link = item.find('link').text if item.find('link') is not None else ''
                        pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                        source = item.find('source').text if item.find('source') is not None else 'Google News'
                        
                        # 발행 시간 파싱
                        try:
                            from email.utils import parsedate_to_datetime
                            published_time = parsedate_to_datetime(pub_date)
                        except:
                            published_time = datetime.now(timezone.utc)
                            
                        article = {
                            'id': self._generate_article_id(link, title),
                            'title': title,
                            'url': link,
                            'source': source,
                            'source_url': url,
                            'published_date': published_time.isoformat(),
                            'collected_at': datetime.now(timezone.utc).isoformat(),
                            'language': language,
                            'search_query': query,
                            'processed': False
                        }
                        
                        articles.append(article)
                        
                    except Exception as e:
                        logger.error(f"Error parsing Google News item: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error fetching Google News for query '{query}': {str(e)}")
            
        return articles
        
    async def fetch_article_content(self, url: str) -> Optional[Dict[str, str]]:
        """기사 본문 내용 가져오기"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 기사 본문 추출 (일반적인 패턴)
                content = ""
                
                # 여러 선택자 시도
                selectors = [
                    'article',
                    '[role="main"]',
                    '.article-body',
                    '.content',
                    'main',
                    '#content'
                ]
                
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        # 텍스트 추출
                        paragraphs = element.find_all('p')
                        if paragraphs:
                            content = ' '.join([p.get_text().strip() for p in paragraphs])
                            break
                            
                # 요약 생성 (첫 500자)
                summary = content[:500] if content else ""
                
                return {
                    'content': content,
                    'summary': summary
                }
                
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {str(e)}")
            return None
            
    async def collect_all_articles(self, hours_back: int = 24) -> List[Dict]:
        """모든 검색 쿼리에서 기사 수집"""
        all_articles = []
        
        # 모든 쿼리 수집
        all_queries = []
        for query_list in self.SEARCH_QUERIES.values():
            all_queries.extend(query_list)
            
        # 병렬로 기사 수집
        tasks = [self.fetch_articles_for_query(query, max_articles=5) for query in all_queries]
        results = await asyncio.gather(*tasks)
        
        # 결과 합치기
        for articles in results:
            all_articles.extend(articles)
            
        # 시간 필터링 (최근 N시간 이내)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        filtered_articles = []
        
        for article in all_articles:
            try:
                pub_time = datetime.fromisoformat(article['published_date'].replace('Z', '+00:00'))
                if pub_time >= cutoff_time:
                    filtered_articles.append(article)
            except:
                filtered_articles.append(article)
                
        # 중복 제거 (URL 기준)
        unique_articles = {}
        for article in filtered_articles:
            if article['url'] not in unique_articles:
                unique_articles[article['url']] = article
                
        logger.info(f"Collected {len(unique_articles)} unique articles from Google News")
        return list(unique_articles.values())
        
    async def enrich_articles_with_content(self, articles: List[Dict]) -> List[Dict]:
        """기사 목록에 본문 내용 추가"""
        enriched_articles = []
        
        # 병렬로 본문 가져오기
        tasks = [self.fetch_article_content(article['url']) for article in articles]
        contents = await asyncio.gather(*tasks)
        
        for article, content_data in zip(articles, contents):
            if content_data:
                article['content'] = content_data['content']
                article['summary'] = content_data['summary']
            else:
                article['content'] = ""
                article['summary'] = article.get('title', '')[:200]
                
            enriched_articles.append(article)
            
        return enriched_articles