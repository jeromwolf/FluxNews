"""프롬프트 템플릿 관리"""
from typing import Dict, List
import json

class PromptTemplates:
    """AI 분석용 프롬프트 템플릿"""
    
    # 시스템 프롬프트
    SYSTEM_PROMPTS = {
        "news_analyzer": """You are an expert financial news analyst specializing in mobility and robotics sectors.
Your task is to analyze news articles for their investment impact on companies in these sectors.
Focus on Korean companies and their global competitors.
Always respond in valid JSON format.""",
        
        "company_extractor": """You are an expert at identifying and extracting company mentions from news articles.
Focus on companies in the autonomous driving, electric vehicles, robotics, and AI sectors.
Pay special attention to Korean companies like Hyundai, Samsung, LG, etc.
Always respond in valid JSON format.""",
        
        "impact_analyzer": """You are a financial analyst who evaluates how news events impact company stock prices.
Consider both direct impacts (company is main subject) and indirect impacts (competitor/partner news).
Provide impact scores between 0.0 (no impact) and 1.0 (maximum impact).
Always respond in valid JSON format."""
    }
    
    @staticmethod
    def news_analysis_prompt(article_title: str, article_content: str, target_companies: List[str] = None) -> str:
        """뉴스 분석 프롬프트 생성"""
        companies_context = ""
        if target_companies:
            companies_context = f"\nFocus particularly on these companies: {', '.join(target_companies)}"
            
        return f"""Analyze this news article for investment insights:

Title: {article_title}
Content: {article_content}
{companies_context}

Provide your analysis in the following JSON format:
{{
    "summary": "2-3 sentence investment-focused summary",
    "sentiment": {{
        "overall": "positive/negative/neutral",
        "score": 0.0-1.0,
        "confidence": 0.0-1.0
    }},
    "key_topics": ["list", "of", "key", "topics"],
    "companies_mentioned": [
        {{
            "name": "Company Name",
            "ticker": "TICKER",
            "country": "Country",
            "sector": "Sector",
            "relevance": "primary/secondary/mentioned"
        }}
    ],
    "market_impact": {{
        "timeframe": "immediate/short-term/long-term",
        "magnitude": "low/medium/high",
        "sectors_affected": ["list", "of", "sectors"]
    }},
    "investment_signals": [
        {{
            "company": "Company Name",
            "signal": "bullish/bearish/neutral",
            "reasoning": "Brief explanation"
        }}
    ]
}}"""

    @staticmethod
    def company_extraction_prompt(article_content: str, known_companies: List[Dict] = None) -> str:
        """기업 추출 프롬프트 생성"""
        known_context = ""
        if known_companies:
            company_list = [f"{c['name']} ({c.get('ticker', 'N/A')})" for c in known_companies]
            known_context = f"\n\nKnown companies in our database:\n{', '.join(company_list[:20])}"
            
        return f"""Extract all company mentions from this article:

{article_content}
{known_context}

Identify and extract:
1. Companies directly mentioned
2. Companies implied through product/service mentions
3. Parent companies of mentioned subsidiaries
4. Key competitors that would be affected

Return in JSON format:
{{
    "companies": [
        {{
            "name": "Official company name",
            "ticker": "Stock ticker if known",
            "mentions": ["list of exact mentions in article"],
            "context": "How the company is mentioned",
            "confidence": 0.0-1.0
        }}
    ],
    "relationships": [
        {{
            "company1": "Company Name",
            "company2": "Company Name", 
            "relationship": "competitor/partner/supplier/customer",
            "mentioned_in_article": true/false
        }}
    ]
}}"""

    @staticmethod
    def impact_analysis_prompt(
        article_summary: str,
        company_name: str,
        company_info: Dict,
        related_companies: List[str] = None
    ) -> str:
        """영향도 분석 프롬프트 생성"""
        company_context = f"""
Company: {company_name}
Sector: {company_info.get('sector', 'Unknown')}
Market Cap: {company_info.get('market_cap', 'Unknown')}
Main Business: {company_info.get('description', 'Unknown')}"""

        related_context = ""
        if related_companies:
            related_context = f"\nRelated companies in network: {', '.join(related_companies[:10])}"
            
        return f"""Analyze the impact of this news on {company_name}:

News Summary: {article_summary}

{company_context}
{related_context}

Evaluate the impact and provide analysis in JSON format:
{{
    "impact_score": 0.0-1.0,
    "confidence_score": 0.0-1.0,
    "impact_type": "direct/indirect/market_wide",
    "timeframe": "immediate/days/weeks/months",
    "direction": "positive/negative/mixed/neutral",
    "reasoning": "Detailed explanation of the impact",
    "key_factors": ["list", "of", "key", "factors"],
    "risks": ["potential", "risks"],
    "opportunities": ["potential", "opportunities"],
    "related_impacts": [
        {{
            "company": "Related Company",
            "impact": "brief description",
            "score": 0.0-1.0
        }}
    ]
}}"""

    @staticmethod
    def korean_context_prompt(content: str) -> str:
        """한국 시장 맥락 분석 프롬프트"""
        return f"""Analyze this content specifically for Korean market context:

{content}

Focus on:
1. Impact on Korean companies (특히 현대, 삼성, LG, SK 등)
2. Korean government policies mentioned
3. Korea-specific market conditions
4. Comparison with global competitors

Provide analysis in JSON format:
{{
    "korean_companies_affected": [
        {{
            "company": "Company name",
            "korean_name": "한글 회사명",
            "impact": "Description",
            "score": 0.0-1.0
        }}
    ],
    "policy_implications": ["list of policy impacts"],
    "market_opportunities": ["opportunities for Korean companies"],
    "competitive_position": "How this affects Korea's position in global market"
}}"""

    @staticmethod
    def sector_comparison_prompt(
        news_summary: str,
        sector: str,
        companies_in_sector: List[str]
    ) -> str:
        """섹터별 비교 분석 프롬프트"""
        return f"""Compare how this news affects different companies in the {sector} sector:

News: {news_summary}
Companies: {', '.join(companies_in_sector)}

Analyze and rank companies by impact in JSON format:
{{
    "sector_analysis": {{
        "overall_impact": "positive/negative/mixed",
        "key_trends": ["identified", "trends"],
        "market_shift": "description of any market shifts"
    }},
    "company_rankings": [
        {{
            "rank": 1,
            "company": "Company name",
            "impact_score": 0.0-1.0,
            "reasoning": "Why this ranking",
            "competitive_advantage": "gained/lost/maintained"
        }}
    ],
    "investment_recommendation": {{
        "top_picks": ["company1", "company2"],
        "avoid": ["company3", "company4"],
        "watch": ["company5", "company6"]
    }}
}}"""