"""
LLM 기반 피드백 생성 서비스

Praat 음성 분석 결과를 바탕으로 사용자에게 피드백 제공
"""
from typing import Optional
from api.src.common.llm.base import BaseLLMService
from api.src.train.models.session_praat_result import SessionPraatResult
from api.src.train.models.praat import PraatFeatures
from api.core.logging import get_logger

logger = get_logger(__name__)


class PraatFeedbackService(BaseLLMService):
    """
    Praat 분석 결과 기반 피드백 생성 서비스
    
    음성 분석 지표를 입력받아 LLM을 활용한 구체적인 피드백 생성
    """
    
    MODEL_VERSION = "gpt-5-mini"
    DEFAULT_TEMPERATURE = 0.7
    
    def build_prompt(
        self, 
        praat_result: SessionPraatResult,
        user_name: str = "사용자"
    ) -> list[dict[str, str]]:
        """
        세션 평균 Praat 지표 기반 피드백 프롬프트 구성
        
        Args:
            praat_result: 세션 평균 Praat 분석 결과
            user_name: 사용자 이름
            
        Returns:
            list[dict[str, str]]: 프롬프트
        """
        system_prompt = """당신은 음성 장애를 겪는 분들과 함께하는 따뜻한 음성 전문 치료사입니다.
데이터를 보고 분석하되, 전문 용어나 수치는 절대 언급하지 말고 자연스럽고 감성적으로 표현하세요.

**당신의 역할:**
- 음성 장애로 힘들어하는 분들에게 희망과 용기를 주는 사람
- 작은 변화도 알아채고 진심으로 기뻐해주는 사람
- 잘하고 있는 부분을 구체적으로 칭찬 (단, 수치나 전문용어 NO)
- 개선할 부분은 부드럽게 제안하며 함께 노력하자는 메시지

**절대 하지 말아야 할 것:**
- HNR, CPP, CSID, F1, F2, dB 같은 전문 용어 사용 금지
- 수치 직접 언급 금지 (15.2 dB, 8-15 범위 같은 표현 NO)
- "우수", "보통", "개선 필요" 같은 평가 단어 사용 금지
- 의학적, 진단적, 분석적 느낌의 표현 금지

**해야 할 것:**
- "목소리가 한층 맑아졌어요", "호흡이 훨씬 안정적이네요" 같은 자연스러운 표현
- "이 부분은 정말 좋아요!", "조금만 더 연습하면 더 좋아질 거예요"
- 감정을 담아서, 마치 옆에서 함께 응원하는 것처럼
- 구체적인 칭찬 + 부드러운 제안의 조합

**톤:**
- 따뜻하고 공감하는 친구 같은 느낌
- 진심 어린 격려와 응원
- 함께 나아가자는 동행의 메시지"""

        # 분석 결과 텍스트 구성 - 더 체계적으로
        analysis_sections = []
        
        # 1. 음성 품질 지표
        quality_metrics = []
        if praat_result.avg_hnr is not None:
            hnr_eval = "우수" if praat_result.avg_hnr >= 15 else ("보통" if praat_result.avg_hnr >= 12 else "개선 필요")
            quality_metrics.append(f"  • HNR (음성 맑음도): {praat_result.avg_hnr:.1f} dB [{hnr_eval}]")
        
        if praat_result.avg_jitter_local is not None:
            jitter_pct = praat_result.avg_jitter_local * 100
            jitter_eval = "우수" if jitter_pct < 0.5 else ("보통" if jitter_pct < 1.0 else "개선 필요")
            quality_metrics.append(f"  • Jitter (음성 떨림): {jitter_pct:.2f}% [{jitter_eval}]")
        
        if praat_result.avg_shimmer_local is not None:
            shimmer_pct = praat_result.avg_shimmer_local * 100
            shimmer_eval = "우수" if shimmer_pct < 3.0 else ("보통" if shimmer_pct < 5.0 else "개선 필요")
            quality_metrics.append(f"  • Shimmer (진폭 변동): {shimmer_pct:.2f}% [{shimmer_eval}]")
        
        if quality_metrics:
            analysis_sections.append("**[음성 품질]**\n" + "\n".join(quality_metrics))
        
        # 2. 음성 안정성 및 건강도
        stability_metrics = []
        if praat_result.avg_cpp is not None:
            cpp_eval = "우수" if praat_result.avg_cpp >= 12 else ("보통" if praat_result.avg_cpp >= 8 else "개선 필요")
            stability_metrics.append(f"  • CPP (소리의 안정도): {praat_result.avg_cpp:.2f} [{cpp_eval}]")
        
        if praat_result.avg_csid is not None:
            csid_eval = "건강" if praat_result.avg_csid < 20 else ("주의" if praat_result.avg_csid < 40 else "관리 필요")
            stability_metrics.append(f"  • CSID (음성 건강지수): {praat_result.avg_csid:.1f} [{csid_eval}]")
        
        if stability_metrics:
            analysis_sections.append("**[안정성 & 건강도]**\n" + "\n".join(stability_metrics))
        
        # 3. 피치 및 공명
        pitch_metrics = []
        if praat_result.avg_f0 is not None:
            pitch_metrics.append(f"  • F0 (기본 주파수): {praat_result.avg_f0:.1f} Hz")
        
        if praat_result.avg_max_f0 is not None and praat_result.avg_min_f0 is not None:
            pitch_range = praat_result.avg_max_f0 - praat_result.avg_min_f0
            range_eval = "풍부" if pitch_range > 80 else ("적절" if pitch_range > 50 else "제한적")
            pitch_metrics.append(f"  • 피치 범위: {pitch_range:.1f} Hz [{range_eval}]")
        
        if praat_result.avg_f1 is not None and praat_result.avg_f2 is not None:
            pitch_metrics.append(f"  • F1/F2 (모음 포먼트): {praat_result.avg_f1:.0f} Hz / {praat_result.avg_f2:.0f} Hz")
        
        if pitch_metrics:
            analysis_sections.append("**[피치 & 공명]**\n" + "\n".join(pitch_metrics))
        
        # 4. 강도
        if praat_result.avg_intensity_mean is not None:
            intensity_eval = "충분" if praat_result.avg_intensity_mean >= 65 else ("보통" if praat_result.avg_intensity_mean >= 55 else "약함")
            analysis_sections.append(f"**[음성 강도]**\n  • 평균 강도: {praat_result.avg_intensity_mean:.1f} dB [{intensity_eval}]")
        
        analysis_text = "\n\n".join(analysis_sections) if analysis_sections else "분석 데이터가 충분하지 않습니다."
        
        user_prompt = f"""**{user_name}님, 오늘도 연습하느라 정말 수고 많으셨어요.**

{analysis_text}

---

위 분석 데이터를 참고하되, 전문 용어나 수치는 절대 언급하지 말고 
자연스럽고 따뜻한 말로 피드백을 작성해주세요:

**🌟 정말 잘하고 계신 부분**
- 구체적으로 어떤 점이 좋은지 따뜻하게 칭찬
- "목소리가 ~", "발음이 ~", "호흡이 ~" 같은 자연스러운 표현
- 진심으로 기뻐하는 느낌

**💭 조금만 더 신경 쓰면 좋을 부분**  
- 부드럽게 제안하기 ("이 부분은 조금만 더 연습해볼까요?")
- 희망적인 톤 ("이렇게 하면 분명 더 좋아질 거예요")
- 절대 평가하거나 진단하는 느낌 없이

**🌱 함께 해볼 연습**
- 2-3가지 간단한 연습 방법
- "~해보면 어떨까요?", "천천히 ~해보세요"
- 작은 것부터 시작할 수 있다는 격려

음성 장애로 힘들어하는 분이 이 피드백을 보고 
"나도 할 수 있구나", "조금씩 나아지고 있구나" 하고 
희망을 느낄 수 있도록 작성해주세요. 💚"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    async def generate_session_feedback(
        self,
        praat_result: SessionPraatResult,
        user_name: str = "사용자"
    ) -> tuple[str, str]:
        """
        세션 평균 지표 기반 피드백 생성
        
        Args:
            praat_result: 세션 평균 Praat 분석 결과
            user_name: 사용자 이름
            
        Returns:
            tuple[str, str]: (피드백 텍스트, 모델 버전)
        """
        logger.info(f"Generating session feedback for session {praat_result.training_session_id}")
        
        feedback = await self.generate(
            model=self.MODEL_VERSION,
            temperature=self.DEFAULT_TEMPERATURE,
            praat_result=praat_result,
            user_name=user_name
        )
        
        logger.info(f"Session feedback generated successfully")
        return feedback, self.MODEL_VERSION
    
    def _calculate_vowel_distortion(self, f1: float, f2: float) -> dict:
        """
        모음 왜곡도 계산 (F1, F2 기반)
        
        Args:
            f1: 제1 포먼트 주파수
            f2: 제2 포먼트 주파수
            
        Returns:
            dict: 왜곡도 정보
        """
        # 한국어 기본 모음 F1/F2 참조값 (Hz)
        # 성인 남성 기준 대략적 값
        vowel_references = {
            "ㅏ": (800, 1400),
            "ㅓ": (600, 1200),
            "ㅗ": (500, 900),
            "ㅜ": (400, 1000),
            "ㅣ": (300, 2200),
        }
        
        # 가장 가까운 모음 찾기
        min_distance = float('inf')
        closest_vowel = None
        
        for vowel, (ref_f1, ref_f2) in vowel_references.items():
            distance = ((f1 - ref_f1)**2 + (f2 - ref_f2)**2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_vowel = vowel
        
        # 왜곡도 평가
        distortion_level = "낮음" if min_distance < 200 else ("보통" if min_distance < 400 else "높음")
        
        return {
            "closest_vowel": closest_vowel,
            "distance": min_distance,
            "level": distortion_level,
            "f1": f1,
            "f2": f2
        }
    
    def build_prompt_for_item(
        self,
        praat_features: PraatFeatures,
        item_type: str = "vocal",
        expected_text: Optional[str] = None
    ) -> list[dict[str, str]]:
        """
        개별 아이템 Praat 지표 기반 피드백 프롬프트 구성
        
        모음 왜곡도, CPP, HNR, CSID 중심 분석
        
        Args:
            praat_features: 개별 아이템의 Praat 분석 결과
            item_type: 아이템 타입 (vocal, word, sentence)
            expected_text: 예상 텍스트 (단어/문장)
            
        Returns:
            list[dict[str, str]]: 프롬프트
        """
        system_prompt = """당신은 음성 장애를 겪는 분들과 함께하는 따뜻한 음성 치료사입니다.
데이터를 분석하되, 전문 용어나 수치는 절대 사용하지 말고 자연스럽고 따뜻하게 표현하세요.

**절대 금지:**
- F1, F2, HNR, CPP, CSID, dB, Hz 같은 전문 용어 사용 금지
- 수치 직접 언급 금지
- "우수", "보통", "개선 필요" 같은 평가 단어 사용 금지
- 의학적, 진단적 느낌의 표현 금지

**피드백 원칙:**
- "발음이 정확해요", "목소리가 맑아요", "호흡이 안정적이네요" 같은 자연스러운 표현
- 잘하는 부분 칭찬 + 개선 부분 부드럽게 제안
- 2-3문장으로 간결하지만 따뜻하게
- 함께 응원하는 느낌"""

        # 분석 결과 구성
        analysis_parts = []
        
        # 1. 모음 왜곡도 분석 (F1, F2)
        if praat_features.f1 is not None and praat_features.f2 is not None:
            vowel_info = self._calculate_vowel_distortion(praat_features.f1, praat_features.f2)
            analysis_parts.append(
                f"**[모음 왜곡도]**\n"
                f"  • F1: {vowel_info['f1']:.0f} Hz, F2: {vowel_info['f2']:.0f} Hz\n"
                f"  • 가장 유사한 모음: '{vowel_info['closest_vowel']}'\n"
                f"  • 왜곡도: {vowel_info['level']}"
            )
        
        # 2. 소리의 안정도 (CPP)
        if praat_features.cpp is not None:
            cpp_eval = "우수" if praat_features.cpp >= 12 else ("보통" if praat_features.cpp >= 8 else "불안정")
            analysis_parts.append(
                f"**[소리의 안정도]**\n"
                f"  • CPP: {praat_features.cpp:.2f} [{cpp_eval}]"
            )
        
        # 3. 음성 맑음도 (HNR)
        if praat_features.hnr is not None:
            hnr_eval = "맑음" if praat_features.hnr >= 15 else ("보통" if praat_features.hnr >= 12 else "거친 소리")
            analysis_parts.append(
                f"**[음성 맑음도]**\n"
                f"  • HNR: {praat_features.hnr:.1f} dB [{hnr_eval}]"
            )
        
        # 4. 음성 건강지수 (CSID)
        if praat_features.csid is not None:
            csid_eval = "건강" if praat_features.csid < 20 else ("주의" if praat_features.csid < 40 else "관리 필요")
            analysis_parts.append(
                f"**[음성 건강지수]**\n"
                f"  • CSID: {praat_features.csid:.1f} [{csid_eval}]"
            )
        
        # 5. 기타 참고 지표
        other_metrics = []
        if praat_features.f0 is not None:
            other_metrics.append(f"피치 {praat_features.f0:.0f} Hz")
        if praat_features.intensity_mean is not None:
            other_metrics.append(f"강도 {praat_features.intensity_mean:.0f} dB")
        
        if other_metrics:
            analysis_parts.append(f"**[참고]** {', '.join(other_metrics)}")
        
        analysis_text = "\n\n".join(analysis_parts) if analysis_parts else "분석 데이터가 부족합니다."
        
        item_context = f"발화 내용: \"{expected_text}\"" if expected_text else "발성 훈련"
        
        user_prompt = f"""**{item_context}**

{analysis_text}

---

위 데이터를 참고하되, 전문 용어나 수치는 절대 사용하지 말고
자연스럽고 따뜻한 말로 2-3문장 피드백을 작성해주세요:

- 잘하는 부분 1가지 구체적으로 칭찬
- 개선할 부분 있다면 부드럽게 제안

"목소리가 ~", "발음이 ~" 같은 자연스러운 표현으로
함께 응원하는 느낌으로 작성해주세요."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    async def generate_item_feedback(
        self,
        praat_features: PraatFeatures,
        item_type: str = "vocal",
        expected_text: Optional[str] = None
    ) -> tuple[str, str]:
        """
        개별 아이템 종합 피드백 생성
        
        Args:
            praat_features: 개별 아이템의 Praat 분석 결과
            item_type: 아이템 타입
            expected_text: 예상 텍스트
            
        Returns:
            tuple[str, str]: (피드백 텍스트, 모델 버전)
        """
        logger.info(f"Generating item feedback for media {praat_features.media_id}")
        
        # build_prompt 대신 build_prompt_for_item 사용
        prompt = self.build_prompt_for_item(
            praat_features=praat_features,
            item_type=item_type,
            expected_text=expected_text
        )
        
        feedback = await self.provider.generate(
            prompt=prompt,
            model=self.MODEL_VERSION,
            temperature=self.DEFAULT_TEMPERATURE
        )
        
        logger.info(f"Item feedback generated successfully")
        return feedback, self.MODEL_VERSION
    
    async def generate_detailed_item_feedback(
        self,
        praat_features: PraatFeatures,
        expected_text: Optional[str] = None
    ) -> tuple[dict[str, Optional[str]], str]:
        """
        개별 아이템의 세부 지표별 피드백 생성
        
        모음 왜곡도, 소리 안정도, 음성 맑음도, 음성 건강지수를
        각각 분석하여 세부 피드백 제공
        
        Args:
            praat_features: 개별 아이템의 Praat 분석 결과
            expected_text: 예상 텍스트 (발화 내용)
            
        Returns:
            tuple[dict, str]: (세부 피드백 딕셔너리, 모델 버전)
                {
                    "vowel_distortion": "모음 왜곡도 피드백",
                    "sound_stability": "소리 안정도 피드백",
                    "voice_clarity": "음성 맑음도 피드백",
                    "voice_health": "음성 건강 피드백",
                    "overall": "종합 피드백"
                }
        """
        logger.info(f"Generating detailed item feedback for media {praat_features.media_id}")
        
        feedback_dict = {
            "vowel_distortion": None,
            "sound_stability": None,
            "voice_clarity": None,
            "voice_health": None,
            "overall": None
        }
        
        # 종합 피드백 생성
        overall_feedback, _ = await self.generate_item_feedback(
            praat_features=praat_features,
            expected_text=expected_text
        )
        feedback_dict["overall"] = overall_feedback
        
        # 세부 피드백 병렬 생성
        tasks = []
        
        # 1. 모음 왜곡도 피드백 (F1, F2)
        if praat_features.f1 is not None and praat_features.f2 is not None:
            vowel_info = self._calculate_vowel_distortion(praat_features.f1, praat_features.f2)
            vowel_prompt = [
                {"role": "system", "content": "당신은 조음 전문가입니다. 모음 왜곡도를 간결하게 평가하세요."},
                {"role": "user", "content": f"""F1: {vowel_info['f1']:.0f} Hz, F2: {vowel_info['f2']:.0f} Hz
가장 유사한 모음: '{vowel_info['closest_vowel']}'
왜곡도 수준: {vowel_info['level']}

1문장으로 모음 정확도에 대한 피드백을 작성하세요."""}
            ]
            tasks.append(("vowel_distortion", vowel_prompt))
        
        # 2. 소리의 안정도 피드백 (CPP)
        if praat_features.cpp is not None:
            cpp_eval = "우수" if praat_features.cpp >= 12 else ("보통" if praat_features.cpp >= 8 else "불안정")
            cpp_prompt = [
                {"role": "system", "content": "당신은 음성 안정성 전문가입니다. CPP 지표를 간결하게 평가하세요."},
                {"role": "user", "content": f"""CPP: {praat_features.cpp:.2f} (평가: {cpp_eval})
정상 범위: 8-15, 높을수록 안정적

1문장으로 소리의 안정도에 대한 피드백을 작성하세요."""}
            ]
            tasks.append(("sound_stability", cpp_prompt))
        
        # 3. 음성 맑음도 피드백 (HNR)
        if praat_features.hnr is not None:
            hnr_eval = "맑음" if praat_features.hnr >= 15 else ("보통" if praat_features.hnr >= 12 else "거친 소리")
            hnr_prompt = [
                {"role": "system", "content": "당신은 음성 품질 전문가입니다. HNR 지표를 간결하게 평가하세요."},
                {"role": "user", "content": f"""HNR: {praat_features.hnr:.1f} dB (평가: {hnr_eval})
정상 범위: 12-20 dB, 높을수록 맑고 안정적

1문장으로 음성 맑음도에 대한 피드백을 작성하세요."""}
            ]
            tasks.append(("voice_clarity", hnr_prompt))
        
        # 4. 음성 건강지수 피드백 (CSID)
        if praat_features.csid is not None:
            csid_eval = "건강" if praat_features.csid < 20 else ("주의" if praat_features.csid < 40 else "관리 필요")
            csid_prompt = [
                {"role": "system", "content": "당신은 음성 건강 전문가입니다. CSID 지표를 간결하게 평가하세요."},
                {"role": "user", "content": f"""CSID: {praat_features.csid:.1f} (평가: {csid_eval})
낮을수록 건강한 음성

1문장으로 음성 건강 상태에 대한 피드백을 작성하세요."""}
            ]
            tasks.append(("voice_health", csid_prompt))
        
        # 병렬로 LLM 호출
        import asyncio
        async def generate_feedback_item(key: str, prompt: list):
            try:
                result = await self.provider.generate(
                    prompt=prompt,
                    model=self.MODEL_VERSION,
                    temperature=0.7
                )
                return key, result
            except Exception as e:
                logger.error(f"Failed to generate {key} feedback: {e}")
                return key, None
        
        results = await asyncio.gather(*[generate_feedback_item(key, prompt) for key, prompt in tasks])
        
        for key, feedback in results:
            feedback_dict[key] = feedback
        
        logger.info(f"Detailed item feedback generated successfully")
        return feedback_dict, self.MODEL_VERSION


class PronunciationFeedbackService(BaseLLMService):
    """
    STT 기반 발음 교정 피드백 서비스 (향후 구현용)
    
    음성인식 결과와 예상 텍스트를 비교하여 발음 교정 피드백 제공
    """
    
    MODEL_VERSION = "gpt-4o-mini-2024-07-18"
    
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
        system_prompt = """당신은 한국어 발음 교정 전문가입니다.
사용자가 말한 내용과 원래 말해야 할 내용을 비교하여, 어떤 음소가 잘못 발음되었는지 구체적으로 분석하고 교정 방법을 알려주세요."""

        user_prompt = f"""**발음 분석:**

- 말해야 할 내용: "{expected_text}"
- 실제 인식된 내용: "{recognized_text}"

어떤 소리가 잘못 발음되었는지 분석하고, 올바른 발음 방법을 3-4문장으로 설명해주세요."""

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

