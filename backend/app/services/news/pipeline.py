import asyncio
from typing import List, Dict, Optional, Set
from datetime import datetime, timezone
import logging
from app.core.supabase import get_supabase_client
from .rss_parser import RSSParser
from .google_news import GoogleNewsCollector
from .deduplication import NewsDeduplicator

logger = logging.getLogger(__name__)

class NewsPipeline:
    """뉴스 수집, 처리, 저장 파이프라인"""
    
    def __init__(self, batch_size: int = 100):
        """
        Args:
            batch_size: 한 번에 처리할 기사 수
        """
        self.batch_size = batch_size
        self.deduplicator = NewsDeduplicator()
        self.supabase = get_supabase_client()
        
    async def collect_news(self, sources: List[str] = None) -> List[Dict]:
        """여러 소스에서 뉴스 수집"""
        all_articles = []
        
        if not sources or 'rss' in sources:
            # RSS 피드에서 수집
            logger.info("Collecting news from RSS feeds...")
            async with RSSParser() as parser:
                rss_articles = await parser.fetch_all_feeds()
                all_articles.extend(rss_articles)
                
        if not sources or 'google' in sources:
            # Google News에서 수집
            logger.info("Collecting news from Google News...")
            async with GoogleNewsCollector() as collector:
                google_articles = await collector.collect_all_articles(hours_back=24)
                # 본문 내용 추가
                google_articles = await collector.enrich_articles_with_content(google_articles)
                all_articles.extend(google_articles)
                
        logger.info(f"Collected {len(all_articles)} total articles")
        return all_articles
        
    def _check_existing_articles(self, article_ids: List[str]) -> Set[str]:
        """데이터베이스에 이미 존재하는 기사 ID 확인"""
        try:
            # Supabase에서 기존 기사 확인
            response = self.supabase.table('news_articles')\
                .select('external_id')\
                .in_('external_id', article_ids)\
                .execute()
                
            existing_ids = {article['external_id'] for article in response.data}
            return existing_ids
            
        except Exception as e:
            logger.error(f"Error checking existing articles: {str(e)}")
            return set()
            
    def _prepare_article_for_storage(self, article: Dict) -> Dict:
        """저장을 위한 기사 데이터 준비"""
        # 필수 필드 확인 및 기본값 설정
        prepared = {
            'title': article.get('title', 'No Title'),
            'content': article.get('content', article.get('summary', '')),
            'url': article['url'],
            'source': article.get('source', 'Unknown'),
            'published_date': article.get('published_date', datetime.now(timezone.utc).isoformat()),
            'external_id': article.get('id', ''),
            'language': article.get('language', 'en'),
            'processed': False,
            'sentiment_score': None,
            'metadata': {
                'source_url': article.get('source_url', ''),
                'search_query': article.get('search_query', ''),
                'collected_at': article.get('collected_at', datetime.now(timezone.utc).isoformat()),
                'duplicate_count': article.get('duplicate_count', 1),
                'merged_sources': article.get('merged_sources', [])
            }
        }
        
        # 날짜 형식 검증
        try:
            datetime.fromisoformat(prepared['published_date'].replace('Z', '+00:00'))
        except:
            prepared['published_date'] = datetime.now(timezone.utc).isoformat()
            
        return prepared
        
    async def save_articles(self, articles: List[Dict]) -> Dict[str, int]:
        """기사를 데이터베이스에 저장"""
        stats = {
            'total': len(articles),
            'saved': 0,
            'skipped': 0,
            'errors': 0
        }
        
        if not articles:
            return stats
            
        # 기존 기사 확인
        article_ids = [a.get('id', '') for a in articles if a.get('id')]
        existing_ids = self._check_existing_articles(article_ids)
        
        # 새로운 기사만 필터링
        new_articles = []
        for article in articles:
            if article.get('id') in existing_ids:
                stats['skipped'] += 1
                logger.debug(f"Skipping existing article: {article.get('title', 'No title')}")
            else:
                new_articles.append(article)
                
        # 배치로 저장
        for i in range(0, len(new_articles), self.batch_size):
            batch = new_articles[i:i + self.batch_size]
            
            try:
                # 저장용 데이터 준비
                prepared_batch = [self._prepare_article_for_storage(a) for a in batch]
                
                # Supabase에 삽입
                response = self.supabase.table('news_articles')\
                    .insert(prepared_batch)\
                    .execute()
                    
                stats['saved'] += len(response.data)
                logger.info(f"Saved batch of {len(response.data)} articles")
                
            except Exception as e:
                stats['errors'] += len(batch)
                logger.error(f"Error saving batch: {str(e)}")
                
        return stats
        
    async def process_pipeline(self, sources: List[str] = None) -> Dict:
        """전체 뉴스 처리 파이프라인 실행"""
        logger.info("Starting news processing pipeline...")
        
        # 1. 뉴스 수집
        articles = await self.collect_news(sources)
        
        # 2. 중복 제거
        logger.info("Removing duplicates...")
        unique_articles = self.deduplicator.filter_duplicates(articles)
        
        # 3. 유사 기사 병합
        logger.info("Merging similar articles...")
        merged_articles = self.deduplicator.merge_similar_articles(unique_articles)
        
        # 4. 데이터베이스 저장
        logger.info("Saving articles to database...")
        save_stats = await self.save_articles(merged_articles)
        
        # 5. 통계 정리
        pipeline_stats = {
            'collected': len(articles),
            'after_dedup': len(unique_articles),
            'after_merge': len(merged_articles),
            'saved': save_stats['saved'],
            'skipped': save_stats['skipped'],
            'errors': save_stats['errors'],
            'dedup_stats': self.deduplicator.get_stats()
        }
        
        logger.info(f"Pipeline completed: {pipeline_stats}")
        return pipeline_stats
        
    async def process_single_article(self, article_url: str) -> Optional[Dict]:
        """단일 기사 처리"""
        try:
            # Google News collector로 기사 내용 가져오기
            async with GoogleNewsCollector() as collector:
                content_data = await collector.fetch_article_content(article_url)
                
                if not content_data:
                    return None
                    
                article = {
                    'id': self.deduplicator._generate_content_hash({'title': article_url, 'content': content_data['content']}),
                    'url': article_url,
                    'title': 'Manual Entry',
                    'content': content_data['content'],
                    'summary': content_data['summary'],
                    'source': 'Manual',
                    'published_date': datetime.now(timezone.utc).isoformat(),
                    'language': 'en',
                    'processed': False
                }
                
                # 중복 확인
                is_dup, reason = self.deduplicator.is_duplicate(article)
                if is_dup:
                    logger.info(f"Article is duplicate: {reason}")
                    return None
                    
                # 저장
                save_stats = await self.save_articles([article])
                
                if save_stats['saved'] > 0:
                    return article
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error processing single article: {str(e)}")
            return None