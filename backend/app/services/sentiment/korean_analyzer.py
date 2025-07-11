"""한국어 감정 분석 지원"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from konlpy.tag import Okt
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class KoreanSentimentResult:
    """한국어 감정 분석 결과"""
    original_text: str
    processed_text: str
    sentiment: str  # positive, negative, neutral
    score: float
    keywords: List[str]
    entities: List[str]

class KoreanSentimentAnalyzer:
    """한국어 텍스트 감정 분석"""
    
    def __init__(self):
        try:
            self.okt = Okt()
            self._initialized = True
        except Exception as e:
            logger.warning(f"KoNLPy initialization failed: {str(e)}")
            self._initialized = False
            
        # 감정 사전 (간단한 규칙 기반)
        self.positive_words = {
            '성장', '상승', '증가', '호조', '개선', '혁신', '성공', '달성',
            '흑자', '수익', '이익', '호재', '긍정', '확대', '강화', '발전',
            '신기록', '최고', '돌파', '상회', '개발', '출시', '계약', '수주'
        }
        
        self.negative_words = {
            '하락', '감소', '위기', '우려', '리스크', '손실', '적자', '부진',
            '악화', '중단', '철수', '실패', '논란', '사고', '리콜', '소송',
            '파산', '구조조정', '감원', '폐쇄', '취소', '연기', '하회', '부족'
        }
        
        # 강조 표현
        self.intensifiers = {
            '매우': 1.5, '아주': 1.5, '정말': 1.5, '너무': 1.5,
            '크게': 1.3, '대폭': 1.3, '급': 1.3, '심각': 1.5
        }
        
        # 부정 표현
        self.negations = {'안', '못', '없', '아니', '미', '불'}
        
        # 금융/기업 관련 개체명
        self.company_patterns = [
            r'(\w+)(?:그룹|주식회사|전자|자동차|중공업|화학|제약|바이오|테크|로보틱스)',
            r'(\w+)(?:은행|증권|보험|캐피탈|자산운용)',
            r'(?:현대|삼성|LG|SK|롯데|한화|포스코|두산|CJ)(\w*)'
        ]
        
    def _extract_korean_entities(self, text: str) -> List[str]:
        """한국어 텍스트에서 기업명 추출"""
        entities = []
        
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
            
        # 중복 제거
        return list(set(filter(None, entities)))
        
    def _tokenize_and_tag(self, text: str) -> List[Tuple[str, str]]:
        """형태소 분석"""
        if not self._initialized:
            # KoNLPy 없이 간단한 토크나이징
            words = text.split()
            return [(word, 'Noun') for word in words]
            
        try:
            return self.okt.pos(text)
        except Exception as e:
            logger.error(f"Tokenization error: {str(e)}")
            words = text.split()
            return [(word, 'Noun') for word in words]
            
    def analyze(self, text: str) -> KoreanSentimentResult:
        """한국어 텍스트 감정 분석"""
        # 기업명 추출
        entities = self._extract_korean_entities(text)
        
        # 형태소 분석
        tokens = self._tokenize_and_tag(text)
        
        # 감정 점수 계산
        positive_score = 0
        negative_score = 0
        keywords = []
        
        # 부정어 체크를 위한 윈도우
        negation_window = False
        intensifier_value = 1.0
        
        for i, (word, pos) in enumerate(tokens):
            # 강조 표현 체크
            if word in self.intensifiers:
                intensifier_value = self.intensifiers[word]
                continue
                
            # 부정어 체크
            if word in self.negations:
                negation_window = True
                continue
                
            # 감정 단어 체크
            if word in self.positive_words:
                if negation_window:
                    negative_score += intensifier_value
                else:
                    positive_score += intensifier_value
                keywords.append(word)
                
            elif word in self.negative_words:
                if negation_window:
                    positive_score += intensifier_value
                else:
                    negative_score += intensifier_value
                keywords.append(word)
                
            # 윈도우 리셋
            if pos in ['Punctuation', 'Josa']:
                negation_window = False
                intensifier_value = 1.0
                
        # 최종 감정 결정
        total_score = positive_score + negative_score
        if total_score == 0:
            sentiment = 'neutral'
            score = 0.5
        else:
            score = positive_score / total_score
            if score > 0.6:
                sentiment = 'positive'
            elif score < 0.4:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
                
        return KoreanSentimentResult(
            original_text=text,
            processed_text=' '.join([word for word, _ in tokens]),
            sentiment=sentiment,
            score=float(score),
            keywords=keywords,
            entities=entities
        )
        
    async def analyze_async(self, text: str) -> KoreanSentimentResult:
        """비동기 분석"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze, text)
        
    def enhance_with_domain_knowledge(
        self,
        result: KoreanSentimentResult,
        domain: str = 'finance'
    ) -> KoreanSentimentResult:
        """도메인 지식을 활용한 감정 분석 개선"""
        if domain == 'finance':
            # 금융 도메인 특화 규칙
            text_lower = result.original_text.lower()
            
            # 수치 패턴 확인
            increase_pattern = r'(\d+\.?\d*)\s*[%％]\s*(?:증가|상승|성장)'
            decrease_pattern = r'(\d+\.?\d*)\s*[%％]\s*(?:감소|하락|감소)'
            
            increase_matches = re.findall(increase_pattern, result.original_text)
            decrease_matches = re.findall(decrease_pattern, result.original_text)
            
            # 수치 기반 조정
            if increase_matches:
                avg_increase = sum(float(m) for m in increase_matches) / len(increase_matches)
                if avg_increase > 10 and result.sentiment == 'neutral':
                    result.sentiment = 'positive'
                    result.score = min(result.score + 0.2, 1.0)
                    
            if decrease_matches:
                avg_decrease = sum(float(m) for m in decrease_matches) / len(decrease_matches)
                if avg_decrease > 10 and result.sentiment == 'neutral':
                    result.sentiment = 'negative'
                    result.score = max(result.score - 0.2, 0.0)
                    
        return result
        
    def get_sentiment_explanation(self, result: KoreanSentimentResult) -> str:
        """감정 분석 결과 설명"""
        explanation = f"감정: {result.sentiment} (점수: {result.score:.2f})\n"
        
        if result.keywords:
            explanation += f"주요 키워드: {', '.join(result.keywords)}\n"
            
        if result.entities:
            explanation += f"언급된 기업: {', '.join(result.entities)}\n"
            
        # 감정에 따른 설명
        if result.sentiment == 'positive':
            explanation += "긍정적인 내용이 우세합니다."
        elif result.sentiment == 'negative':
            explanation += "부정적인 내용이 우세합니다."
        else:
            explanation += "중립적인 내용입니다."
            
        return explanation