"""
OpenAI Provider - AI 언어모델 인프라 레이어

OpenAI API를 호출하는 싱글톤 프로바이더
모든 LLM 서비스의 기반이 되는 저수준 API 제공
"""
from typing import Optional, Any
from openai import AsyncOpenAI
from api.core.config import settings
from api.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider:
    """
    OpenAI 프로바이더 싱글톤
    
    OpenAI API를 래핑하여 일관된 인터페이스 제공
    애플리케이션 전역에서 단일 인스턴스 사용
    """
    _instance: Optional["OpenAIProvider"] = None
    
    def __new__(cls) -> "OpenAIProvider":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # 싱글톤이므로 한 번만 초기화
        if self._initialized:
            return
            
        self.client = AsyncOpenAI(
            api_key=settings.OPEN_AI_API_KEY,
            timeout=60.0,  # 60초 타임아웃
        )
        self._initialized = True
        logger.info("OpenAI Provider initialized successfully")
    
    async def generate(
        self,
        prompt: list[dict[str, str]],
        model: str = "gpt-5-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        reasoning_effort: str = "low",
        verbosity: str = "low",
        **kwargs: Any
    ) -> str:
        """
        텍스트 생성 API 호출 (GPT-4/GPT-5 모두 지원)
        
        프롬프트를 입력받아 텍스트를 생성 (피드백, 분석 리포트 등)
        
        Args:
            prompt: 프롬프트 리스트 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            model: 사용할 모델 (기본: gpt-5-mini)
            temperature: 창의성 파라미터 (GPT-4만 사용, GPT-5는 무시)
            max_tokens: 최대 토큰 수
            reasoning_effort: GPT-5 추론 깊이 ("minimal", "low", "medium", "high")
            verbosity: GPT-5 출력 상세도 ("low", "medium", "high")
            **kwargs: 추가 파라미터
            
        Returns:
            str: 생성된 텍스트
            
        Raises:
            Exception: API 호출 실패시
        """
        try:
            api_params = {
                "model": model,
                "messages": prompt,
                **kwargs
            }
            
            # GPT-5 모델 계열 처리 (Chat Completions API 사용시)
            if "gpt-5" in model:
                # GPT-5는 temperature 지원 안 함
                # reasoning_effort와 verbosity 사용
                api_params["reasoning_effort"] = reasoning_effort
                api_params["verbosity"] = verbosity
                
                # Chat Completions API에서는 max_completion_tokens 사용
                if max_tokens is not None:
                    api_params["max_completion_tokens"] = max_tokens
                    
                logger.debug(f"GPT-5 API - reasoning: {reasoning_effort}, verbosity: {verbosity}")
            
            # 기존 모델 (GPT-4 등) 처리
            else:
                api_params["temperature"] = temperature
                
                if max_tokens is not None:
                    api_params["max_tokens"] = max_tokens
                    
                logger.debug(f"GPT-4 API - temperature: {temperature}")
            
            response = await self.client.chat.completions.create(**api_params)
            
            content = response.choices[0].message.content
            
            logger.info(
                f"OpenAI text generated - model: {model}, "
                f"tokens: {response.usage.total_tokens if response.usage else 'N/A'}"
            )
            
            return content or ""
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise


# 전역 싱글톤 인스턴스
openai_provider = OpenAIProvider()

