import feedparser
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timezone
import hashlib
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class RSSParser:
    """RSS 피드 파서 클래스"""
    
    # 주요 뉴스 소스 RSS 피드
    FEED_SOURCES = {
        "english": {
            "Reuters Tech": "https://www.reutersagency.com/feed/?best-topics=tech&post_type=best",
            "Bloomberg Tech": "https://www.bloomberg.com/technology/feeds/site.xml",
            "TechCrunch": "https://techcrunch.com/feed/",
            "The Verge": "https://www.theverge.com/rss/index.xml",
            "MIT Tech Review": "https://www.technologyreview.com/feed/",
        },
        "korean": {
            "연합뉴스 IT": "https://www.yna.co.kr/RSS/it.xml",
            "조선비즈 테크": "https://biz.chosun.com/rss/technology.xml",
            "한국경제 IT": "https://rss.hankyung.com/feed/it.xml",
            "ZDNet Korea": "https://www.zdnet.co.kr/rss/news_all.xml",
            "전자신문": "https://rss.etnews.com/Section902.xml",
        }
    }
    
    # 모빌리티/로보틱스 관련 키워드
    RELEVANT_KEYWORDS = [
        # 영어
        "autonomous", "self-driving", "robotics", "mobility", "EV", "electric vehicle",
        "battery", "AI", "artificial intelligence", "lidar", "sensor", "automation",
        # 한국어
        "자율주행", "로봇", "로보틱스", "모빌리티", "전기차", "배터리", 
        "인공지능", "센서", "자동화", "무인", "드론", "UAM"
    ]
    
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
        
    def _is_relevant(self, article: Dict) -> bool:
        """기사가 관련성이 있는지 확인"""
        text = f"{article.get('title', '')} {article.get('summary', '')}"
        text_lower = text.lower()
        
        return any(keyword.lower() in text_lower for keyword in self.RELEVANT_KEYWORDS)
        
    def _extract_source_name(self, feed_url: str) -> str:
        """피드 URL에서 소스명 추출"""
        for lang_feeds in self.FEED_SOURCES.values():
            for name, url in lang_feeds.items():
                if url == feed_url:
                    return name
        
        # 기본값: 도메인명 사용
        parsed = urlparse(feed_url)
        return parsed.netloc.replace('www.', '').split('.')[0].title()
        
    async def fetch_feed(self, feed_url: str) -> Optional[feedparser.FeedParserDict]:
        """단일 RSS 피드 가져오기"""
        try:
            async with self.session.get(feed_url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    return feedparser.parse(content)
                else:
                    logger.error(f"Failed to fetch {feed_url}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {feed_url}: {str(e)}")
            return None
            
    def parse_entry(self, entry: feedparser.FeedParserDict, source_name: str, feed_url: str) -> Dict:
        """RSS 엔트리를 표준 포맷으로 파싱"""
        # 발행 시간 파싱
        published_time = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_time = datetime.fromtimestamp(
                feedparser._parse_date(entry.published).timetuple().tm_sec,
                tz=timezone.utc
            )
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published_time = datetime.fromtimestamp(
                feedparser._parse_date(entry.updated).timetuple().tm_sec,
                tz=timezone.utc
            )
        else:
            published_time = datetime.now(timezone.utc)
            
        # 요약 추출
        summary = ""
        if hasattr(entry, 'summary'):
            summary = entry.summary
        elif hasattr(entry, 'description'):
            summary = entry.description
            
        # 콘텐츠 추출
        content = summary
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].get('value', summary)
            
        article = {
            'id': self._generate_article_id(entry.link, entry.title),
            'title': entry.title,
            'url': entry.link,
            'source': source_name,
            'source_url': feed_url,
            'summary': summary[:500],  # 요약은 500자로 제한
            'content': content,
            'published_date': published_time.isoformat(),
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'language': 'ko' if any(source_name in self.FEED_SOURCES['korean'] for source_name in self.FEED_SOURCES['korean']) else 'en',
            'processed': False
        }
        
        return article
        
    async def fetch_all_feeds(self, filter_relevant: bool = True) -> List[Dict]:
        """모든 피드에서 기사 수집"""
        all_articles = []
        
        # 모든 피드 URL 수집
        all_feed_urls = []
        for lang_feeds in self.FEED_SOURCES.values():
            all_feed_urls.extend([(url, name) for name, url in lang_feeds.items()])
            
        # 병렬로 피드 가져오기
        tasks = [self.fetch_feed(url) for url, _ in all_feed_urls]
        feeds = await asyncio.gather(*tasks)
        
        # 각 피드 처리
        for (feed_url, source_name), feed in zip(all_feed_urls, feeds):
            if not feed or not feed.entries:
                continue
                
            for entry in feed.entries[:20]:  # 피드당 최대 20개 기사
                try:
                    article = self.parse_entry(entry, source_name, feed_url)
                    
                    # 관련성 필터링
                    if filter_relevant and not self._is_relevant(article):
                        continue
                        
                    all_articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing entry from {source_name}: {str(e)}")
                    continue
                    
        logger.info(f"Collected {len(all_articles)} relevant articles from RSS feeds")
        return all_articles
        
    async def fetch_specific_feeds(self, feed_urls: List[str], filter_relevant: bool = True) -> List[Dict]:
        """특정 피드에서만 기사 수집"""
        all_articles = []
        
        # 병렬로 피드 가져오기
        tasks = [self.fetch_feed(url) for url in feed_urls]
        feeds = await asyncio.gather(*tasks)
        
        # 각 피드 처리
        for feed_url, feed in zip(feed_urls, feeds):
            if not feed or not feed.entries:
                continue
                
            source_name = self._extract_source_name(feed_url)
            
            for entry in feed.entries[:20]:
                try:
                    article = self.parse_entry(entry, source_name, feed_url)
                    
                    if filter_relevant and not self._is_relevant(article):
                        continue
                        
                    all_articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing entry from {feed_url}: {str(e)}")
                    continue
                    
        return all_articles