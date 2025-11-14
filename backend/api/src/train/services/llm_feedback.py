from typing import Optional
from api.src.common.llm.base import BaseLLMService
from api.core.logging import get_logger

logger = get_logger(__name__)


class PronunciationFeedbackService(BaseLLMService):
    """
    STT 기반 발음 교정 피드백 서비스 (향후 구현용)
    
    음성인식 결과와 예상 텍스트를 비교하여 발음 교정 피드백 제공
    """
    
    MODEL_VERSION = "gpt-5-mini"
    
    def build_prompt(
        self,
        expected_text: str,
        recognized_text: str,
        **kwargs
    ) -> list[dict[str, str]]:
        """
        STT 결과 기반 발음 교정 프롬프트 구성
        
        Args:
            expected_text: 기대 텍스트 (예: "사과")
            recognized_text: STT 인식 텍스트 (예: "배")
            
        Returns:
            list[dict[str, str]]: 프롬프트
        """
        system_prompt = """당신은 음성 장애를 겪는 분들과 함께하는 따뜻한 음성 치료사입니다.
발음 차이를 분석하되, 전문 용어나 진단적 표현 없이 자연스럽고 따뜻하게 설명하세요.

**표현 가이드:**
- "이 소리를 ~하게 발음해보면 어떨까요?"
- "입모양을 조금만 더 ~하면 좋을 것 같아요"
- 절대 금지: 전문 용어, 진단적 표현, 부정적 단어

**톤:** 함께 연습하는 친구처럼 부드럽고 격려하는 느낌"""

        user_prompt = f"""**발음 분석:**

- 말해야 할 내용: "{expected_text}"
- 실제 인식된 내용: "{recognized_text}"

---

어떤 소리가 다르게 발음되었는지 자연스럽게 설명하고,
올바른 발음 방법을 3-4문장으로 따뜻하게 알려주세요.

전문 용어나 수치는 사용하지 말고, "~해보면 어떨까요?" 같은 부드러운 제안으로 작성하세요."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    async def generate_pronunciation_feedback(
        self,
        expected_text: str,
        recognized_text: str
    ) -> tuple[str, str]:
        """
        발음 교정 피드백 생성
        
        Args:
            expected_text: 기대 텍스트
            recognized_text: STT 인식 텍스트
            
        Returns:
            tuple[str, str]: (피드백 텍스트, 모델 버전)
        """
        logger.info(f"Generating pronunciation feedback: '{expected_text}' -> '{recognized_text}'")
        
        feedback = await self.generate(
            model=self.MODEL_VERSION,
            temperature=0.7,
            expected_text=expected_text,
            recognized_text=recognized_text
        )
        
        logger.info(f"Pronunciation feedback generated successfully")
        return feedback, self.MODEL_VERSION


