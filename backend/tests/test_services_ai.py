"""AI 서비스 테스트"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from app.services.ai.openai_client import OpenAIClient
from app.services.sentiment.finbert_analyzer import FinBERTAnalyzer
from app.services.impact.impact_calculator import ImpactCalculator, ImpactFactors

class TestOpenAIClient:
    """OpenAI 클라이언트 테스트"""
    
    @pytest.mark.asyncio
    async def test_complete_success(self):
        """API 호출 성공 테스트"""
        client = OpenAIClient()
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(total_tokens=100)
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await client.complete("Test prompt")
            
            assert result["result"] == "Test response"
            assert result["usage"]["total_tokens"] == 100
            assert result["cost"]["total"] > 0
    
    @pytest.mark.asyncio
    async def test_extract_companies(self):
        """기업 추출 테스트"""
        client = OpenAIClient()
        
        mock_response = {
            "result": {
                "companies": [
                    {"name": "현대자동차", "relevance": 0.9},
                    {"name": "LG전자", "relevance": 0.7}
                ],
                "relationships": [
                    {
                        "source": "현대자동차",
                        "target": "LG전자",
                        "type": "partnership"
                    }
                ]
            },
            "usage": {"total_tokens": 200}
        }
        
        with patch.object(client, 'complete', new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = mock_response
            
            companies, relationships = await client.extract_companies(
                "현대자동차와 LG전자가 전기차 배터리 협력을 발표했다."
            )
            
            assert len(companies) == 2
            assert companies[0]["name"] == "현대자동차"
            assert len(relationships) == 1
            assert relationships[0]["type"] == "partnership"
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self):
        """Rate limit 재시도 테스트"""
        client = OpenAIClient()
        
        # 첫 번째 호출은 rate limit, 두 번째는 성공
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                Exception("Rate limit exceeded"),
                Mock(
                    choices=[Mock(message=Mock(content="Success"))],
                    usage=Mock(total_tokens=50)
                )
            ]
            
            result = await client.complete("Test", max_retries=2)
            
            assert result["result"] == "Success"
            assert mock_create.call_count == 2

class TestFinBERTAnalyzer:
    """FinBERT 감정 분석 테스트"""
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment(self):
        """감정 분석 테스트"""
        # Mock transformers
        with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
            with patch('transformers.AutoModelForSequenceClassification.from_pretrained') as mock_model:
                # Mock tokenizer
                mock_tokenizer.return_value = Mock(
                    return_tensors='pt',
                    __call__=Mock(return_value={'input_ids': Mock()})
                )
                
                # Mock model output
                mock_output = Mock()
                mock_output.logits = Mock()
                mock_model.return_value = Mock(
                    __call__=Mock(return_value=mock_output)
                )
                
                # Mock softmax result
                with patch('torch.nn.functional.softmax') as mock_softmax:
                    mock_softmax.return_value = Mock(
                        tolist=Mock(return_value=[[0.1, 0.2, 0.7]])  # Positive
                    )
                    
                    analyzer = FinBERTAnalyzer()
                    result = await analyzer.analyze("주가가 크게 상승했습니다.")
                    
                    assert result["sentiment"] == "positive"
                    assert result["confidence"] == 0.7
                    assert result["scores"]["positive"] == 0.7
    
    @pytest.mark.asyncio
    async def test_batch_analyze(self):
        """배치 분석 테스트"""
        with patch('transformers.AutoTokenizer.from_pretrained'):
            with patch('transformers.AutoModelForSequenceClassification.from_pretrained'):
                with patch.object(FinBERTAnalyzer, 'analyze', new_callable=AsyncMock) as mock_analyze:
                    mock_analyze.side_effect = [
                        {"sentiment": "positive", "confidence": 0.8},
                        {"sentiment": "negative", "confidence": 0.6},
                        {"sentiment": "neutral", "confidence": 0.9}
                    ]
                    
                    analyzer = FinBERTAnalyzer()
                    texts = ["긍정적 뉴스", "부정적 뉴스", "중립적 뉴스"]
                    
                    results = await analyzer.batch_analyze(texts)
                    
                    assert len(results) == 3
                    assert results[0]["sentiment"] == "positive"
                    assert results[1]["sentiment"] == "negative"
                    assert results[2]["sentiment"] == "neutral"

class TestImpactCalculator:
    """영향도 계산기 테스트"""
    
    def test_calculate_impact_high_score(self):
        """높은 영향도 점수 계산 테스트"""
        calculator = ImpactCalculator()
        
        factors = ImpactFactors(
            sentiment_score=0.9,      # 매우 긍정적
            relevance_score=0.95,     # 매우 관련성 높음
            magnitude_score=0.8,      # 큰 규모
            source_credibility=0.9,   # 신뢰도 높은 소스
            time_decay=1.0           # 최신 뉴스
        )
        
        impact = calculator.calculate_impact(factors, article_id=1, company_id=1)
        
        assert impact.final_score > 0.8
        assert impact.confidence > 0.8
        assert impact.category == "high"
    
    def test_calculate_impact_with_relationships(self):
        """관계 기반 영향도 계산 테스트"""
        calculator = ImpactCalculator()
        
        factors = ImpactFactors(
            sentiment_score=0.7,
            relevance_score=0.5,  # 간접 관련
            magnitude_score=0.6,
            source_credibility=0.8,
            time_decay=0.9
        )
        
        relationships = [
            {"weight": 0.8, "type": "supplier"},
            {"weight": 0.6, "type": "partner"}
        ]
        
        impact = calculator.calculate_impact(
            factors, 
            article_id=1, 
            company_id=1,
            relationships=relationships
        )
        
        # 관계로 인한 간접 영향도 증가
        assert impact.indirect_impact > 0
        assert impact.final_score > factors.relevance_score
    
    def test_time_decay_calculation(self):
        """시간 감쇠 계산 테스트"""
        calculator = ImpactCalculator()
        
        # 1일 전
        decay_1day = calculator._calculate_time_decay(hours_ago=24)
        assert 0.8 < decay_1day < 1.0
        
        # 7일 전
        decay_7days = calculator._calculate_time_decay(hours_ago=168)
        assert 0.3 < decay_7days < 0.5
        
        # 30일 전
        decay_30days = calculator._calculate_time_decay(hours_ago=720)
        assert decay_30days < 0.1