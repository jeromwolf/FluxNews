"""FinBERT 기반 금융 감정 분석"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """감정 분석 결과"""
    label: str  # positive, negative, neutral
    score: float  # 0.0 ~ 1.0
    confidence: float  # 신뢰도
    raw_scores: Dict[str, float]  # 각 라벨별 점수

class FinBERTAnalyzer:
    """FinBERT를 사용한 금융 뉴스 감정 분석"""
    
    def __init__(self, model_name: str = "ProsusAI/finbert", device: str = None):
        """
        Args:
            model_name: HuggingFace 모델 이름
            device: 'cuda', 'cpu', or None (자동 선택)
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 모델 로딩 상태
        self._model = None
        self._tokenizer = None
        self._model_loaded = False
        
        # 배치 처리용 executor
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        logger.info(f"FinBERT Analyzer initialized with device: {self.device}")
        
    def load_model(self):
        """모델 로드 (필요시에만 호출)"""
        if self._model_loaded:
            return
            
        try:
            logger.info(f"Loading FinBERT model: {self.model_name}")
            
            # 토크나이저 로드
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # 모델 로드
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()  # 평가 모드
            
            self._model_loaded = True
            logger.info("FinBERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {str(e)}")
            raise
            
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 기본 정리
        text = text.strip()
        
        # 너무 긴 텍스트는 자르기 (FinBERT는 512 토큰 제한)
        # 대략 단어당 1.5 토큰으로 계산
        max_words = 300
        words = text.split()
        if len(words) > max_words:
            # 앞부분과 뒷부분을 포함
            text = ' '.join(words[:150] + ['...'] + words[-150:])
            
        return text
        
    def _analyze_single(self, text: str) -> SentimentResult:
        """단일 텍스트 감정 분석"""
        if not self._model_loaded:
            self.load_model()
            
        # 전처리
        text = self._preprocess_text(text)
        
        # 토크나이징
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        ).to(self.device)
        
        # 추론
        with torch.no_grad():
            outputs = self._model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # 결과 파싱
        predictions = predictions.cpu().numpy()[0]
        
        # FinBERT 라벨 순서: [positive, negative, neutral]
        labels = ['positive', 'negative', 'neutral']
        scores = {label: float(score) for label, score in zip(labels, predictions)}
        
        # 최고 점수 라벨
        max_idx = np.argmax(predictions)
        label = labels[max_idx]
        score = float(predictions[max_idx])
        
        # 신뢰도 계산 (최고 점수와 두 번째 점수의 차이)
        sorted_scores = sorted(predictions, reverse=True)
        confidence = float(sorted_scores[0] - sorted_scores[1])
        
        return SentimentResult(
            label=label,
            score=score,
            confidence=confidence,
            raw_scores=scores
        )
        
    async def analyze(self, text: str) -> SentimentResult:
        """비동기 감정 분석"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._analyze_single, text)
        
    async def analyze_batch(self, texts: List[str], batch_size: int = 8) -> List[SentimentResult]:
        """배치 감정 분석"""
        results = []
        
        # 배치 단위로 처리
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # 병렬 처리
            batch_results = await asyncio.gather(
                *[self.analyze(text) for text in batch]
            )
            results.extend(batch_results)
            
        return results
        
    def analyze_with_context(self, text: str, context: Dict[str, any] = None) -> SentimentResult:
        """컨텍스트를 고려한 분석"""
        result = self._analyze_single(text)
        
        # 컨텍스트 기반 조정 (예: 특정 키워드나 도메인 정보)
        if context:
            # 예: 특정 회사가 언급된 경우
            if context.get('company_mentioned'):
                company = context['company_mentioned']
                # 부정적 키워드 체크
                negative_keywords = ['bankruptcy', 'lawsuit', 'recall', 'scandal', 'loss']
                positive_keywords = ['profit', 'growth', 'innovation', 'partnership', 'success']
                
                text_lower = text.lower()
                neg_count = sum(1 for kw in negative_keywords if kw in text_lower)
                pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
                
                # 키워드 기반 조정
                if neg_count > pos_count and result.label == 'neutral':
                    result.label = 'negative'
                    result.confidence *= 0.8  # 신뢰도 하향
                elif pos_count > neg_count and result.label == 'neutral':
                    result.label = 'positive'
                    result.confidence *= 0.8
                    
        return result
        
    def get_market_sentiment(self, results: List[SentimentResult]) -> Dict[str, float]:
        """여러 결과를 종합한 시장 감정 지표"""
        if not results:
            return {
                'bullish_score': 0.5,
                'bearish_score': 0.5,
                'neutral_score': 0.0,
                'overall_sentiment': 'neutral',
                'confidence': 0.0
            }
            
        # 가중 평균 계산
        total_weight = 0
        weighted_positive = 0
        weighted_negative = 0
        weighted_neutral = 0
        
        for result in results:
            weight = result.confidence
            total_weight += weight
            
            weighted_positive += result.raw_scores['positive'] * weight
            weighted_negative += result.raw_scores['negative'] * weight
            weighted_neutral += result.raw_scores['neutral'] * weight
            
        if total_weight > 0:
            bullish = weighted_positive / total_weight
            bearish = weighted_negative / total_weight
            neutral = weighted_neutral / total_weight
        else:
            bullish = bearish = neutral = 1/3
            
        # 전체 감정 판단
        if bullish > bearish + 0.1:
            overall = 'bullish'
        elif bearish > bullish + 0.1:
            overall = 'bearish'
        else:
            overall = 'neutral'
            
        return {
            'bullish_score': float(bullish),
            'bearish_score': float(bearish),
            'neutral_score': float(neutral),
            'overall_sentiment': overall,
            'confidence': float(total_weight / len(results))
        }
        
    def cleanup(self):
        """리소스 정리"""
        if self._model:
            del self._model
            self._model = None
        if self._tokenizer:
            del self._tokenizer
            self._tokenizer = None
        self._model_loaded = False
        self.executor.shutdown(wait=True)
        
        # GPU 메모리 정리
        if self.device == 'cuda':
            torch.cuda.empty_cache()