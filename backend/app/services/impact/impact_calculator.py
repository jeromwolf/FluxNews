"""영향도 점수 계산기"""
import logging
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .impact_models import (
    ImpactScore, ImpactFactors, ImpactType,
    RelationshipType, CompanyRelationWeight
)

logger = logging.getLogger(__name__)

class ImpactCalculator:
    """뉴스가 기업에 미치는 영향도 계산"""
    
    def __init__(self):
        # 가중치 설정
        self.weights = {
            'sentiment': 0.3,  # 감정 분석 결과
            'relevance': 0.25,  # 관련성
            'magnitude': 0.2,  # 뉴스 규모
            'source': 0.15,  # 출처 신뢰도
            'recency': 0.1  # 최신성
        }
        
    def calculate_impact(
        self,
        factors: ImpactFactors,
        article_id: int,
        company_id: int
    ) -> ImpactScore:
        """
        영향도 점수 계산
        
        Args:
            factors: 영향도 계산 요소
            article_id: 기사 ID
            company_id: 기업 ID
            
        Returns:
            계산된 영향도 점수
        """
        # 1. 기본 점수 계산
        base_score = self._calculate_base_score(factors)
        
        # 2. 감정 요인 계산
        sentiment_factor = self._calculate_sentiment_factor(
            factors.sentiment_score,
            factors.sentiment_confidence
        )
        
        # 3. 관련성 요인 계산
        relevance_factor = self._calculate_relevance_factor(factors)
        
        # 4. 시간 감쇠 적용
        time_decay_factor = factors.get_time_decay_factor()
        
        # 5. 관계 가중치 적용
        relationship_factor = self._calculate_relationship_factor(factors)
        
        # 6. 최종 점수 계산
        final_score = self._compute_final_score(
            base_score,
            sentiment_factor,
            relevance_factor,
            time_decay_factor,
            relationship_factor,
            factors
        )
        
        # 7. 신뢰도 계산
        confidence = self._calculate_confidence(factors)
        
        # 8. 영향 유형 결정
        impact_type = self._determine_impact_type(factors)
        
        # 9. 설명 생성
        explanation = self._generate_explanation(
            final_score,
            factors,
            impact_type
        )
        
        return ImpactScore(
            article_id=article_id,
            company_id=company_id,
            base_score=base_score,
            sentiment_factor=sentiment_factor,
            relevance_factor=relevance_factor,
            time_decay_factor=time_decay_factor,
            relationship_factor=relationship_factor,
            final_score=final_score,
            confidence=confidence,
            impact_type=impact_type,
            factors=factors,
            explanation=explanation,
            calculated_at=datetime.utcnow()
        )
        
    def _calculate_base_score(self, factors: ImpactFactors) -> float:
        """기본 점수 계산"""
        # 뉴스 규모에 따른 기본 점수
        magnitude_score = factors.get_magnitude_weight()
        
        # 출처 신뢰도
        source_score = factors.source_credibility
        
        # 언급 빈도 점수 (로그 스케일)
        mention_score = min(1.0, math.log(factors.company_mentioned_count + 1) / math.log(10))
        
        # 가중 평균
        base_score = (
            magnitude_score * 0.4 +
            source_score * 0.3 +
            mention_score * 0.3
        )
        
        return base_score
        
    def _calculate_sentiment_factor(
        self,
        sentiment_score: float,
        confidence: float
    ) -> float:
        """감정 요인 계산"""
        # 감정 점수를 영향도로 변환
        # 극단적인 감정(매우 긍정/부정)일수록 영향도 높음
        if sentiment_score > 0.5:
            # 긍정적: 0.5~1.0 -> 0.0~1.0
            factor = (sentiment_score - 0.5) * 2
        else:
            # 부정적: 0.0~0.5 -> 1.0~0.0
            factor = (0.5 - sentiment_score) * 2
            
        # 신뢰도 적용
        return factor * confidence
        
    def _calculate_relevance_factor(self, factors: ImpactFactors) -> float:
        """관련성 요인 계산"""
        relevance = factors.relevance_score
        
        # 주요 주제인 경우 보너스
        if factors.is_primary_subject:
            relevance = min(1.0, relevance * 1.5)
            
        # 섹터/시장 영향 고려
        if factors.sector_impact:
            relevance = min(1.0, relevance * 1.2)
        if factors.market_impact:
            relevance = min(1.0, relevance * 1.3)
            
        return relevance
        
    def _calculate_relationship_factor(self, factors: ImpactFactors) -> float:
        """관계 가중치 계산"""
        if factors.is_primary_subject:
            return 1.0  # 직접 영향
            
        if factors.relationship_type:
            return CompanyRelationWeight.get_default_weight(factors.relationship_type)
            
        return 0.5  # 기본값
        
    def _compute_final_score(
        self,
        base_score: float,
        sentiment_factor: float,
        relevance_factor: float,
        time_decay_factor: float,
        relationship_factor: float,
        factors: ImpactFactors
    ) -> float:
        """최종 점수 계산"""
        # 가중 평균 계산
        weighted_score = (
            base_score * self.weights['magnitude'] +
            sentiment_factor * self.weights['sentiment'] +
            relevance_factor * self.weights['relevance'] +
            factors.source_credibility * self.weights['source'] +
            time_decay_factor * self.weights['recency']
        )
        
        # 관계 가중치 적용
        final_score = weighted_score * relationship_factor
        
        # 0-1 범위로 정규화
        return max(0.0, min(1.0, final_score))
        
    def _calculate_confidence(self, factors: ImpactFactors) -> float:
        """신뢰도 계산"""
        # 각 요소의 신뢰도 종합
        confidence_factors = [
            factors.sentiment_confidence,
            factors.source_credibility,
            min(1.0, factors.company_mentioned_count / 5),  # 언급 횟수
            1.0 if factors.is_primary_subject else 0.7
        ]
        
        # 평균 신뢰도
        return sum(confidence_factors) / len(confidence_factors)
        
    def _determine_impact_type(self, factors: ImpactFactors) -> ImpactType:
        """영향 유형 결정"""
        if factors.is_primary_subject:
            return ImpactType.DIRECT
        elif factors.relationship_type:
            return ImpactType.INDIRECT
        elif factors.sector_impact:
            return ImpactType.SECTOR
        elif factors.market_impact:
            return ImpactType.MARKET
        else:
            return ImpactType.INDIRECT
            
    def _generate_explanation(
        self,
        score: float,
        factors: ImpactFactors,
        impact_type: ImpactType
    ) -> str:
        """영향도 설명 생성"""
        level = self._get_impact_level(score)
        
        # 기본 설명
        explanation = f"영향도: {level} ({score:.2f})\n"
        
        # 영향 유형
        impact_type_kr = {
            ImpactType.DIRECT: "직접적 영향",
            ImpactType.INDIRECT: "간접적 영향",
            ImpactType.SECTOR: "섹터 영향",
            ImpactType.MARKET: "시장 전반 영향"
        }
        explanation += f"유형: {impact_type_kr.get(impact_type, '기타')}\n"
        
        # 주요 요인
        if factors.is_primary_subject:
            explanation += "- 기업이 뉴스의 주요 주제\n"
        
        if factors.company_mentioned_count > 3:
            explanation += f"- {factors.company_mentioned_count}회 언급\n"
            
        # 감정 영향
        if factors.sentiment_score > 0.7:
            explanation += "- 매우 긍정적인 내용\n"
        elif factors.sentiment_score < 0.3:
            explanation += "- 매우 부정적인 내용\n"
            
        # 규모
        magnitude_kr = {
            "minor": "경미한",
            "moderate": "보통",
            "major": "중대한",
            "critical": "매우 중대한"
        }
        explanation += f"- {magnitude_kr.get(factors.news_magnitude, '보통')} 규모의 뉴스\n"
        
        return explanation.strip()
        
    def _get_impact_level(self, score: float) -> str:
        """점수에 따른 영향도 수준"""
        if score >= 0.8:
            return "매우 높음"
        elif score >= 0.6:
            return "높음"
        elif score >= 0.4:
            return "중간"
        elif score >= 0.2:
            return "낮음"
        else:
            return "매우 낮음"
            
    def calculate_batch_impacts(
        self,
        factors_list: List[Tuple[ImpactFactors, int, int]]
    ) -> List[ImpactScore]:
        """배치 영향도 계산"""
        results = []
        
        for factors, article_id, company_id in factors_list:
            try:
                score = self.calculate_impact(factors, article_id, company_id)
                results.append(score)
            except Exception as e:
                logger.error(f"Error calculating impact for article {article_id}, company {company_id}: {str(e)}")
                
        return results