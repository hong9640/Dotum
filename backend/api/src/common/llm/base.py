"""
LLM 서비스 베이스 클래스

모든 도메인별 LLM 서비스가 상속받아야 하는 추상 베이스 클래스
프롬프트 구성과 LLM 호출을 표준화
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from api.core.openai_provider import openai_provider
from api.core.logging import get_logger

logger = get_logger(__name__)


class BaseLLMService(ABC):
    """
    LLM 서비스 추상 베이스 클래스
    
    모든 도메인별 LLM 서비스는 이 클래스를 상속받아
    build_prompt() 메서드를 구현해야 함
    
    Usage:
        class MyLLMService(BaseLLMService):
            def build_prompt(self, user_input: str) -> list[dict]:
                return [
                    {"role": "system", "content": "You are..."},
                    {"role": "user", "content": user_input}
                ]
        
        service = MyLLMService()
        result = await service.generate(user_input="Hello")
    """
    
    def __init__(self):
        """OpenAI Provider 초기화"""
        self.provider = openai_provider
        logger.debug(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    def build_prompt(self, **kwargs: Any) -> list[dict[str, str]]:
        """
        도메인별 프롬프트 생성 (추상 메서드)
        
        하위 클래스에서 반드시 구현해야 함
        도메인 특화된 프롬프트 로직을 여기에 작성
        
        Args:
            **kwargs: 프롬프트 생성에 필요한 파라미터
            
        Returns:
            list[dict[str, str]]: OpenAI 메시지 형식의 프롬프트
                [
                    {"role": "system", "content": "..."},
                    {"role": "user", "content": "..."}
                ]
        """
        pass
    
    async def generate(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        텍스트 생성
        
        build_prompt()로 프롬프트를 구성하고 OpenAI API 호출하여 텍스트 생성
        
        Args:
            model: 사용할 LLM 모델
            temperature: 창의성 파라미터 (0.0~2.0)
            max_tokens: 최대 토큰 수
            **kwargs: build_prompt()에 전달될 파라미터
            
        Returns:
            str: 생성된 텍스트
            
        Raises:
            Exception: OpenAI API 호출 실패시
        """
        try:
            # 도메인별 프롬프트 구성
            prompt = self.build_prompt(**kwargs)
            
            logger.debug(f"{self.__class__.__name__} generating text")
            
            # OpenAI API 호출
            result = await self.provider.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            logger.info(f"{self.__class__.__name__} text generated successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} text generation failed: {str(e)}")
            raise

