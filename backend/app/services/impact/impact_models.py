"""영향도 점수 계산 모델"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class ImpactType(Enum):
    """영향 유형"""
    DIRECT = "direct"  # 직접적 영향 (회사가 주요 주제)
    INDIRECT = "indirect"  # 간접적 영향 (경쟁사/파트너 관련)
    SECTOR = "sector"  # 섹터 전반 영향
    MARKET = "market"  # 시장 전체 영향

class RelationshipType(Enum):
    """기업 관계 유형"""
    COMPETITOR = "competitor"  # 경쟁사
    PARTNER = "partner"  # 파트너사
    SUPPLIER = "supplier"  # 공급업체
    CUSTOMER = "customer"  # 고객사
    INVESTOR = "investor"  # 투자자
    SUBSIDIARY = "subsidiary"  # 자회사

@dataclass
class CompanyRelationWeight:
    """기업 관계별 가중치"""
    relationship_type: RelationshipType
    weight: float  # 0.0 ~ 1.0
    
    # 기본 가중치 설정
    DEFAULT_WEIGHTS = {
        RelationshipType.COMPETITOR: 0.8,  # 경쟁사 영향 높음
        RelationshipType.PARTNER: 0.7,
        RelationshipType.SUPPLIER: 0.6,
        RelationshipType.CUSTOMER: 0.6,
        RelationshipType.INVESTOR: 0.5,
        RelationshipType.SUBSIDIARY: 0.9  # 자회사는 거의 직접 영향
    }
    
    @classmethod
    def get_default_weight(cls, relationship: RelationshipType) -> float:
        """기본 가중치 반환"""
        return cls.DEFAULT_WEIGHTS.get(relationship, 0.5)

@dataclass
class ImpactFactors:
    """영향도 계산 요소"""
    # 뉴스 관련 요소
    sentiment_score: float  # 감정 점수 (0.0 ~ 1.0)
    sentiment_confidence: float  # 감정 분석 신뢰도
    relevance_score: float  # 관련성 점수 (기업이 얼마나 중요하게 다뤄졌는지)
    
    # 기업 관련 요소
    company_mentioned_count: int  # 기업 언급 횟수
    is_primary_subject: bool  # 주요 주제인지 여부
    relationship_type: Optional[RelationshipType]  # 관계 유형 (간접 영향일 때)
    
    # 시간 요소
    published_date: datetime  # 뉴스 발행 시간
    analysis_date: datetime  # 분석 시간
    
    # 뉴스 특성
    source_credibility: float  # 뉴스 출처 신뢰도 (0.0 ~ 1.0)
    news_magnitude: str  # 뉴스 규모: "minor", "moderate", "major", "critical"
    
    # 추가 컨텍스트
    sector_impact: bool  # 섹터 전반에 영향을 미치는지
    market_impact: bool  # 시장 전체에 영향을 미치는지
    
    def get_time_decay_factor(self) -> float:
        """시간 감쇠 계수 계산"""
        # 뉴스 발행 후 경과 시간 (시간 단위)
        hours_elapsed = (self.analysis_date - self.published_date).total_seconds() / 3600
        
        # 감쇠 곡선: 24시간 후 0.7, 72시간 후 0.5, 1주일 후 0.3
        if hours_elapsed <= 24:
            return 1.0 - (0.3 * hours_elapsed / 24)
        elif hours_elapsed <= 72:
            return 0.7 - (0.2 * (hours_elapsed - 24) / 48)
        elif hours_elapsed <= 168:  # 1주일
            return 0.5 - (0.2 * (hours_elapsed - 72) / 96)
        else:
            return 0.3  # 최소값
            
    def get_magnitude_weight(self) -> float:
        """뉴스 규모별 가중치"""
        magnitude_weights = {
            "minor": 0.3,
            "moderate": 0.6,
            "major": 0.9,
            "critical": 1.0
        }
        return magnitude_weights.get(self.news_magnitude, 0.5)

@dataclass
class ImpactScore:
    """최종 영향도 점수"""
    article_id: int
    company_id: int
    
    # 점수 구성 요소
    base_score: float  # 기본 점수 (0.0 ~ 1.0)
    sentiment_factor: float  # 감정 요인
    relevance_factor: float  # 관련성 요인
    time_decay_factor: float  # 시간 감쇠
    relationship_factor: float  # 관계 가중치
    
    # 최종 점수
    final_score: float  # 0.0 ~ 1.0
    confidence: float  # 신뢰도
    
    # 메타 정보
    impact_type: ImpactType
    factors: ImpactFactors
    explanation: str
    calculated_at: datetime
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'article_id': self.article_id,
            'company_id': self.company_id,
            'final_score': self.final_score,
            'confidence': self.confidence,
            'impact_type': self.impact_type.value,
            'components': {
                'base_score': self.base_score,
                'sentiment_factor': self.sentiment_factor,
                'relevance_factor': self.relevance_factor,
                'time_decay_factor': self.time_decay_factor,
                'relationship_factor': self.relationship_factor
            },
            'explanation': self.explanation,
            'calculated_at': self.calculated_at.isoformat()
        }
        
    def get_impact_level(self) -> str:
        """영향도 수준 반환"""
        if self.final_score >= 0.8:
            return "매우 높음"
        elif self.final_score >= 0.6:
            return "높음"
        elif self.final_score >= 0.4:
            return "중간"
        elif self.final_score >= 0.2:
            return "낮음"
        else:
            return "매우 낮음"