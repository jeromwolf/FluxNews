"""백그라운드 작업 관리"""
import logging
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.supabase import get_supabase_client
from app.services.sentiment import SentimentPipeline
from app.services.ai import BatchAnalyzer
from app.services.news import NewsPipeline
from app.services.notification import notification_service

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """백그라운드 작업 관리자"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.sentiment_pipeline = SentimentPipeline(enable_gpu=False)  # CPU 사용
        self.news_pipeline = NewsPipeline()
        self.batch_analyzer = BatchAnalyzer()
        
    async def process_unanalyzed_articles(self, limit: int = 50):
        """
        분석되지 않은 기사 처리
        
        Args:
            limit: 한 번에 처리할 최대 기사 수
        """
        try:
            # 미처리 기사 조회
            response = self.supabase.table('news_articles')\
                .select('id, title, content')\
                .eq('processed', False)\
                .order('published_date', desc=True)\
                .limit(limit)\
                .execute()
                
            articles = response.data
            
            if not articles:
                logger.info("No unanalyzed articles found")
                return
                
            logger.info(f"Processing {len(articles)} unanalyzed articles")
            
            # 감정 분석 수행
            sentiment_results = await self.sentiment_pipeline.analyze_batch(articles)
            
            # 처리 완료 표시
            processed_ids = [r.article_id for r in sentiment_results if r.confidence > 0]
            if processed_ids:
                self.supabase.table('news_articles')\
                    .update({'processed': True})\
                    .in_('id', processed_ids)\
                    .execute()
                    
            logger.info(f"Processed {len(processed_ids)} articles")
            
        except Exception as e:
            logger.error(f"Error processing unanalyzed articles: {str(e)}")
            
    async def collect_news_periodically(self):
        """주기적 뉴스 수집"""
        try:
            logger.info("Starting periodic news collection")
            
            # 뉴스 수집 및 처리
            stats = await self.news_pipeline.process_pipeline()
            
            logger.info(f"News collection completed: {stats}")
            
            # 수집된 기사 즉시 분석
            if stats.get('saved', 0) > 0:
                await self.process_unanalyzed_articles()
                
        except Exception as e:
            logger.error(f"Error in periodic news collection: {str(e)}")
            
    async def analyze_company_impacts(self, hours_back: int = 24):
        """
        최근 뉴스의 기업별 영향도 분석
        
        Args:
            hours_back: 분석할 시간 범위
        """
        try:
            cutoff_time = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()
            
            # 최근 처리된 기사 중 영향도 분석이 안 된 것들
            response = self.supabase.table('news_articles')\
                .select('id')\
                .eq('processed', True)\
                .gte('published_date', cutoff_time)\
                .execute()
                
            article_ids = [a['id'] for a in response.data]
            
            if not article_ids:
                logger.info("No articles for impact analysis")
                return
                
            # 이미 분석된 기사 제외
            impacts_response = self.supabase.table('news_company_impacts')\
                .select('article_id')\
                .in_('article_id', article_ids)\
                .execute()
                
            analyzed_ids = {i['article_id'] for i in impacts_response.data}
            unanalyzed_ids = [aid for aid in article_ids if aid not in analyzed_ids]
            
            if unanalyzed_ids:
                logger.info(f"Analyzing impacts for {len(unanalyzed_ids)} articles")
                
                # 배치 분석 (시스템 사용자로)
                results = await self.batch_analyzer.analyze_batch(
                    article_ids=unanalyzed_ids[:20],  # 한 번에 20개씩
                    user_id='system'
                )
                
                # 높은 영향도 알림 트리거
                await self._trigger_impact_notifications(results)
                
        except Exception as e:
            logger.error(f"Error analyzing company impacts: {str(e)}")
            
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """
        오래된 데이터 정리
        
        Args:
            days_to_keep: 유지할 일수
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
            
            # 오래된 분석 기록 삭제
            self.supabase.table('user_analyses')\
                .delete()\
                .lt('created_at', cutoff_date)\
                .execute()
                
            # 오래된 AI 사용 기록 삭제
            self.supabase.table('ai_usage')\
                .delete()\
                .lt('created_at', cutoff_date)\
                .execute()
                
            logger.info(f"Cleaned up data older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            
    async def generate_daily_report(self):
        """일일 리포트 생성"""
        try:
            # 오늘의 통계
            today = datetime.utcnow().date().isoformat()
            
            # 수집된 기사 수
            news_count = self.supabase.table('news_articles')\
                .select('id', count='exact')\
                .gte('created_at', today)\
                .execute()
                
            # 처리된 기사 수
            processed_count = self.supabase.table('news_articles')\
                .select('id', count='exact')\
                .eq('processed', True)\
                .gte('created_at', today)\
                .execute()
                
            # AI 사용량
            ai_usage = self.supabase.table('ai_usage')\
                .select('cost_usd')\
                .gte('created_at', today)\
                .execute()
                
            total_cost = sum(u['cost_usd'] for u in ai_usage.data)
            
            # 시장 감정
            market_sentiment = await self.sentiment_pipeline.get_market_sentiment(24)
            
            report = {
                'date': today,
                'news_collected': news_count.count,
                'news_processed': processed_count.count,
                'ai_requests': len(ai_usage.data),
                'ai_cost_usd': total_cost,
                'market_sentiment': market_sentiment,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # 리포트 저장 (추후 별도 테이블 생성 가능)
            logger.info(f"Daily report: {report}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
            return None
            
    async def _trigger_impact_notifications(self, analysis_results: Dict):
        """영향도 분석 결과에 따른 알림 트리거"""
        try:
            if not analysis_results or 'results' not in analysis_results:
                return
                
            for result in analysis_results['results']:
                if 'error' in result:
                    continue
                    
                # 높은 영향도 기사 확인
                if 'companies_mentioned' in result:
                    for company in result['companies_mentioned']:
                        # 영향도 점수 추출 (AI 분석 결과에서)
                        impact_score = 0.7  # 기본값, 실제로는 분석 결과에서 추출
                        
                        if impact_score >= 0.7:  # 높은 영향도
                            # 해당 기업을 관심 목록에 추가한 사용자 조회
                            user_ids = await notification_service.get_watchlist_users(
                                company['id']
                            )
                            
                            if user_ids:
                                await notification_service.create_high_impact_notification(
                                    article_id=result['article_id'],
                                    company_id=company['id'],
                                    impact_score=impact_score,
                                    user_ids=user_ids
                                )
                                
        except Exception as e:
            logger.error(f"Error triggering impact notifications: {str(e)}")
            
    async def check_sentiment_changes(self):
        """감정 변화 모니터링 및 알림"""
        try:
            # 각 기업의 최근 감정 변화 확인
            companies = self.supabase.table('companies')\
                .select('id')\
                .execute()
                
            for company in companies.data:
                company_id = company['id']
                
                # 24시간 전과 현재 감정 비교
                market_sentiment_now = await self.sentiment_pipeline.get_market_sentiment(
                    time_window_hours=1,
                    company_id=company_id
                )
                
                market_sentiment_before = await self.sentiment_pipeline.get_market_sentiment(
                    time_window_hours=24,
                    company_id=company_id
                )
                
                if market_sentiment_now['total_articles'] > 0 and market_sentiment_before['total_articles'] > 0:
                    current_score = market_sentiment_now['average_score']
                    previous_score = market_sentiment_before['average_score']
                    
                    change = abs(current_score - previous_score)
                    
                    if change >= 0.3:  # 30% 이상 변화
                        # 관심 사용자에게 알림
                        user_ids = await notification_service.get_watchlist_users(company_id)
                        
                        if user_ids:
                            await notification_service.create_sentiment_alert(
                                company_id=company_id,
                                old_sentiment=previous_score,
                                new_sentiment=current_score,
                                user_ids=user_ids
                            )
                            
        except Exception as e:
            logger.error(f"Error checking sentiment changes: {str(e)}")

# 스케줄러 설정을 위한 작업 정의
SCHEDULED_TASKS = {
    'collect_news': {
        'func': 'collect_news_periodically',
        'interval_minutes': 30,
        'description': '뉴스 수집 및 기본 처리'
    },
    'process_articles': {
        'func': 'process_unanalyzed_articles',
        'interval_minutes': 15,
        'description': '미분석 기사 감정 분석'
    },
    'analyze_impacts': {
        'func': 'analyze_company_impacts',
        'interval_minutes': 60,
        'description': '기업별 영향도 분석'
    },
    'cleanup': {
        'func': 'cleanup_old_data',
        'interval_minutes': 1440,  # 24시간
        'description': '오래된 데이터 정리'
    },
    'daily_report': {
        'func': 'generate_daily_report',
        'interval_minutes': 1440,  # 24시간
        'description': '일일 리포트 생성'
    },
    'sentiment_check': {
        'func': 'check_sentiment_changes',
        'interval_minutes': 60,  # 1시간마다
        'description': '감정 변화 모니터링'
    }
}