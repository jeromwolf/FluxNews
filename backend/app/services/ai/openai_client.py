import os
import logging
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI API 클라이언트 래퍼"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API 키
            model: 사용할 모델 (기본: gpt-4o-mini)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
            
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
        self.default_temperature = 0.3  # 일관성 있는 결과를 위해 낮은 온도
        
    async def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        OpenAI API로 텍스트 완성 요청
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            temperature: 창의성 수준 (0-2)
            max_tokens: 최대 토큰 수
            response_format: JSON 응답 형식 지정
            
        Returns:
            응답 데이터와 메타정보
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # API 호출 파라미터
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.default_temperature,
                "max_tokens": max_tokens
            }
            
            # JSON 응답 형식 지정 (GPT-4o 이상에서 지원)
            if response_format and self.model in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]:
                params["response_format"] = {"type": "json_object"}
            
            # API 호출
            response = await self.client.chat.completions.create(**params)
            
            # 응답 데이터 구성
            result = {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
            # JSON 응답인 경우 파싱
            if response_format:
                try:
                    result["parsed_content"] = json.loads(result["content"])
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {str(e)}")
                    result["parsed_content"] = None
                    
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
            
    async def batch_complete(
        self,
        prompts: List[str],
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = 2000,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        여러 프롬프트를 동시에 처리
        
        Args:
            prompts: 프롬프트 리스트
            system_prompt: 공통 시스템 프롬프트
            temperature: 창의성 수준
            max_tokens: 최대 토큰 수
            max_concurrent: 최대 동시 요청 수
            
        Returns:
            응답 리스트
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _process_with_semaphore(prompt: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
        tasks = [_process_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)
        
    async def analyze_with_retry(
        self,
        prompt: str,
        system_prompt: str = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """
        재시도 로직과 함께 분석 수행
        
        Args:
            prompt: 분석 프롬프트
            system_prompt: 시스템 프롬프트
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간격
            
        Returns:
            분석 결과 또는 None
        """
        for attempt in range(max_retries):
            try:
                result = await self.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    response_format={"type": "json_object"}
                )
                
                if result.get("parsed_content"):
                    return result
                    
                logger.warning(f"Attempt {attempt + 1}: Invalid response format")
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    
        return None
        
    def estimate_cost(self, usage: Dict[str, int]) -> Dict[str, float]:
        """
        토큰 사용량으로 비용 추정
        
        Args:
            usage: 토큰 사용량 정보
            
        Returns:
            비용 정보
        """
        # 2024년 기준 가격 (1K 토큰당)
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
        }
        
        model_pricing = pricing.get(self.model, pricing["gpt-4o-mini"])
        
        input_cost = (usage["prompt_tokens"] / 1000) * model_pricing["input"]
        output_cost = (usage["completion_tokens"] / 1000) * model_pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "total_cost_krw": round(total_cost * 1400, 2)  # 대략적인 환율
        }
        
    async def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            response = await self.complete(
                prompt="Hello",
                max_tokens=10
            )
            return response is not None
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False