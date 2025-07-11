import hashlib
from typing import List, Dict, Set, Tuple
from difflib import SequenceMatcher
import re
from urllib.parse import urlparse, parse_qs, urljoin
import logging

logger = logging.getLogger(__name__)

class NewsDeduplicator:
    """뉴스 중복 제거 시스템"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: 제목 유사도 임계값 (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.seen_urls: Set[str] = set()
        self.seen_titles: Set[str] = set()
        self.seen_hashes: Set[str] = set()
        
    def _normalize_url(self, url: str) -> str:
        """URL 정규화"""
        try:
            # URL 파싱
            parsed = urlparse(url.lower())
            
            # 쿼리 파라미터 제거 (일부 추적 파라미터)
            query_params = parse_qs(parsed.query)
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
                             'fbclid', 'gclid', 'ref', 'source']
            
            filtered_params = {k: v for k, v in query_params.items() 
                             if k not in tracking_params}
            
            # 정규화된 URL 재구성
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if filtered_params:
                param_str = '&'.join([f"{k}={v[0]}" for k, v in sorted(filtered_params.items())])
                normalized += f"?{param_str}"
                
            return normalized.rstrip('/')
            
        except Exception as e:
            logger.error(f"Error normalizing URL {url}: {str(e)}")
            return url
            
    def _normalize_title(self, title: str) -> str:
        """제목 정규화"""
        # 소문자 변환
        normalized = title.lower()
        
        # 특수문자 제거 (한글, 영문, 숫자, 공백만 남김)
        normalized = re.sub(r'[^a-z0-9가-힣\s]', ' ', normalized)
        
        # 다중 공백 제거
        normalized = ' '.join(normalized.split())
        
        return normalized
        
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """두 제목의 유사도 계산"""
        norm_title1 = self._normalize_title(title1)
        norm_title2 = self._normalize_title(title2)
        
        return SequenceMatcher(None, norm_title1, norm_title2).ratio()
        
    def _generate_content_hash(self, article: Dict) -> str:
        """기사 내용 해시 생성"""
        # 제목과 본문 일부를 조합하여 해시 생성
        content = f"{article.get('title', '')}"
        
        if article.get('content'):
            # 본문 첫 500자 사용
            content += article['content'][:500]
        elif article.get('summary'):
            content += article['summary']
            
        return hashlib.md5(content.encode('utf-8')).hexdigest()
        
    def is_duplicate(self, article: Dict, existing_articles: List[Dict] = None) -> Tuple[bool, str]:
        """
        기사가 중복인지 확인
        
        Returns:
            (is_duplicate, reason)
        """
        # URL 중복 확인
        normalized_url = self._normalize_url(article['url'])
        if normalized_url in self.seen_urls:
            return True, "duplicate_url"
            
        # 컨텐츠 해시 중복 확인
        content_hash = self._generate_content_hash(article)
        if content_hash in self.seen_hashes:
            return True, "duplicate_content"
            
        # 제목 유사도 확인
        article_title = article.get('title', '')
        for seen_title in self.seen_titles:
            similarity = self._calculate_title_similarity(article_title, seen_title)
            if similarity >= self.similarity_threshold:
                return True, f"similar_title_{similarity:.2f}"
                
        # 기존 기사들과 비교 (선택적)
        if existing_articles:
            for existing in existing_articles:
                # URL 비교
                if self._normalize_url(existing['url']) == normalized_url:
                    return True, "duplicate_url_in_batch"
                    
                # 제목 유사도 비교
                similarity = self._calculate_title_similarity(
                    article_title, 
                    existing.get('title', '')
                )
                if similarity >= self.similarity_threshold:
                    return True, f"similar_title_in_batch_{similarity:.2f}"
                    
        return False, "unique"
        
    def add_article(self, article: Dict):
        """처리된 기사를 중복 체크 세트에 추가"""
        self.seen_urls.add(self._normalize_url(article['url']))
        self.seen_titles.add(article.get('title', ''))
        self.seen_hashes.add(self._generate_content_hash(article))
        
    def filter_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """기사 목록에서 중복 제거"""
        unique_articles = []
        duplicate_count = 0
        
        for article in articles:
            is_dup, reason = self.is_duplicate(article, unique_articles)
            
            if not is_dup:
                unique_articles.append(article)
                self.add_article(article)
            else:
                duplicate_count += 1
                logger.debug(f"Filtered duplicate article: {article.get('title', 'No title')} - Reason: {reason}")
                
        logger.info(f"Filtered {duplicate_count} duplicate articles from {len(articles)} total")
        return unique_articles
        
    def merge_similar_articles(self, articles: List[Dict]) -> List[Dict]:
        """유사한 기사들을 병합 (같은 사건에 대한 여러 보도)"""
        merged_groups = []
        processed_indices = set()
        
        for i, article in enumerate(articles):
            if i in processed_indices:
                continue
                
            # 현재 기사와 유사한 기사들 찾기
            similar_group = [article]
            processed_indices.add(i)
            
            for j, other_article in enumerate(articles[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                    
                similarity = self._calculate_title_similarity(
                    article.get('title', ''),
                    other_article.get('title', '')
                )
                
                if similarity >= self.similarity_threshold:
                    similar_group.append(other_article)
                    processed_indices.add(j)
                    
            # 그룹에서 가장 최신/상세한 기사 선택
            if len(similar_group) > 1:
                # 가장 긴 컨텐츠를 가진 기사 선택
                best_article = max(similar_group, 
                                 key=lambda a: len(a.get('content', '') or a.get('summary', '')))
                
                # 다른 소스들 추가
                sources = list(set([a['source'] for a in similar_group]))
                best_article['merged_sources'] = sources
                best_article['duplicate_count'] = len(similar_group)
                
                merged_groups.append(best_article)
            else:
                merged_groups.append(article)
                
        return merged_groups
        
    def clear_cache(self):
        """중복 체크 캐시 초기화"""
        self.seen_urls.clear()
        self.seen_titles.clear()
        self.seen_hashes.clear()
        
    def get_stats(self) -> Dict:
        """중복 제거 통계"""
        return {
            'cached_urls': len(self.seen_urls),
            'cached_titles': len(self.seen_titles),
            'cached_hashes': len(self.seen_hashes)
        }