"""
배치 피드백 생성 서비스 (리팩토링 버전)

간결하고 명확한 로직으로 재작성
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import json

from api.src.train.repositories.feedback import FeedbackRepository
from api.core.openai_provider import openai_provider
from api.src.train.models.training_item import TrainingItem
from api.src.train.models.praat import PraatFeatures
from api.src.train.models.media import MediaFile, MediaType
from api.src.train.models.words import TrainWords
from api.src.train.models.sentences import TrainSentences
from api.core.logging import get_logger

logger = get_logger(__name__)


class BatchFeedbackService:
    """배치 피드백 생성 서비스"""
    
    MODEL_VERSION = "gpt-5-mini"  # LLM 모델 버전
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = FeedbackRepository(db)
        self.provider = openai_provider
    
    async def generate_and_save_session_feedback(
        self,
        session_id: int,
        user_name: str
    ) -> bool:
        """
        세션 평균 피드백 + 모든 아이템 피드백 배치 생성
        
        Returns:
            bool: 성공 여부
        """
        try:
            logger.info(f"[Batch] Starting feedback generation for session {session_id}")
            
            # 1. SessionPraatResult 조회
            praat_result = await self.repository.get_session_praat_result_by_session_id(session_id)
            if not praat_result:
                logger.warning(f"[Batch] No SessionPraatResult for session {session_id}")
                return False
            
            # 2. 중복 체크
            existing_feedback = await self.repository.get_session_feedback_by_praat_result_id(
                praat_result.id
            )
            if existing_feedback:
                logger.info(f"[Batch] Feedback already exists for session {session_id}")
                return True
            
            # 3. 아이템 데이터 조회
            items_data = await self._get_items_with_praat(session_id)
            
            if not items_data:
                # 아이템 없으면 세션 피드백만 생성
                logger.info(f"[Batch] No items, generating session feedback only")
                await self._save_session_feedback_only(praat_result, user_name)
                return True
            
            # 4. 배치 LLM 호출
            batch_result = await self._generate_batch_feedback(
                praat_result, items_data, user_name
            )
            
            # 5. 세션 피드백 저장
            await self.repository.create_session_feedback(
                session_praat_result_id=praat_result.id,
                feedback_text=batch_result["session_feedback"],
                model_version=batch_result["model_version"]
            )
            logger.info(f"[Batch] Session feedback saved")
            
            # 6. 아이템 피드백 저장
            await self._save_item_feedbacks(
                batch_result.get("items", []),
                items_data
            )
            
            logger.info(f"[Batch] ✅ All feedbacks saved for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"[Batch] ❌ Failed: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def _get_items_with_praat(
        self,
        session_id: int
    ) -> List[Dict[str, Any]]:
        """
        아이템 + Praat 데이터 조회 (최적화)
        
        Returns:
            [
                {
                    "item_index": 0,
                    "praat_features_id": 123,
                    "expected_text": "사과",
                    "praat": {...}
                },
                ...
            ]
        """
        logger.debug(f"[Batch] Fetching items with praat for session {session_id}")
        
        # 1. 완료된 아이템 조회 (VIDEO MediaFile 포함)
        items_stmt = (
            select(TrainingItem, MediaFile)
            .join(MediaFile, TrainingItem.media_file_id == MediaFile.id)
            .where(TrainingItem.training_session_id == session_id)
            .where(TrainingItem.is_completed == True)
            .where(MediaFile.media_type == MediaType.VIDEO)
            .order_by(TrainingItem.item_index)
        )
        items_result = await self.db.execute(items_stmt)
        items_with_video = items_result.all()
        
        if not items_with_video:
            logger.debug(f"[Batch] No completed items found")
            return []
        
        logger.debug(f"[Batch] Found {len(items_with_video)} completed items")
        
        # 2. VIDEO -> AUDIO object_key 변환
        audio_keys = [
            video_media.object_key.replace('.mp4', '.wav').replace('.MP4', '.wav')
            for _, video_media in items_with_video
        ]
        logger.debug(f"[Batch] Looking for {len(audio_keys)} audio files")
        
        # 3. AUDIO MediaFile + PraatFeatures 조회 (JOIN으로 한 번에)
        audio_praat_stmt = (
            select(MediaFile, PraatFeatures)
            .join(PraatFeatures, MediaFile.id == PraatFeatures.media_id)
            .where(MediaFile.object_key.in_(audio_keys))
            .where(MediaFile.media_type == MediaType.AUDIO)
        )
        audio_praat_result = await self.db.execute(audio_praat_stmt)
        audio_praat_list = audio_praat_result.all()
        
        if not audio_praat_list:
            logger.warning(f"[Batch] No audio/praat data found")
            return []
        
        logger.debug(f"[Batch] Found {len(audio_praat_list)} audio+praat pairs")
        
        # 4. word/sentence 일괄 조회 (N+1 문제 해결)
        word_ids = [item.word_id for item, _ in items_with_video if item.word_id]
        sentence_ids = [item.sentence_id for item, _ in items_with_video if item.sentence_id]
        
        words_map = {}
        sentences_map = {}
        
        if word_ids:
            words_stmt = select(TrainWords).where(TrainWords.id.in_(word_ids))
            words_result = await self.db.execute(words_stmt)
            words_list = words_result.scalars().all()
            words_map = {w.id: w.word for w in words_list}
            logger.debug(f"[Batch] Loaded {len(words_map)} words")
        
        if sentence_ids:
            sentences_stmt = select(TrainSentences).where(TrainSentences.id.in_(sentence_ids))
            sentences_result = await self.db.execute(sentences_stmt)
            sentences_list = sentences_result.scalars().all()
            sentences_map = {s.id: s.sentence for s in sentences_list}
            logger.debug(f"[Batch] Loaded {len(sentences_map)} sentences")
        
        # 5. AUDIO object_key -> (Item, PraatFeatures) 매핑
        audio_key_to_praat = {audio.object_key: praat for audio, praat in audio_praat_list}
        
        # 6. 데이터 조합
        items_data = []
        for item, video_media in items_with_video:
            # VIDEO -> AUDIO object_key
            audio_key = video_media.object_key.replace('.mp4', '.wav').replace('.MP4', '.wav')
            
            # PraatFeatures 찾기
            praat = audio_key_to_praat.get(audio_key)
            if not praat:
                logger.warning(f"[Batch] No praat for item {item.item_index}")
                continue
            
            # 텍스트 조회 (미리 로드된 맵에서)
            expected_text = None
            if item.word_id:
                expected_text = words_map.get(item.word_id)
            elif item.sentence_id:
                expected_text = sentences_map.get(item.sentence_id)
            
            items_data.append({
                "item_index": item.item_index,
                "praat_features_id": praat.id,
                "expected_text": expected_text or f"item_{item.item_index}",
                "praat": {
                    "f0": praat.f0,
                    "f1": praat.f1,
                    "f2": praat.f2,
                    "hnr": praat.hnr,
                    "cpp": praat.cpp,
                    "csid": praat.csid,
                    "jitter_local": praat.jitter_local,
                    "shimmer_local": praat.shimmer_local,
                    "intensity_mean": praat.intensity_mean
                }
            })
        
        # item_index 순서로 정렬
        items_data.sort(key=lambda x: x["item_index"])
        
        logger.info(f"[Batch] ✅ Prepared {len(items_data)} items for LLM")
        return items_data
    
    async def _generate_batch_feedback(
        self,
        praat_result: Any,
        items_data: List[Dict],
        user_name: str
    ) -> Dict[str, Any]:
        """
        배치 LLM 호출
        
        Returns:
            {
                "session_feedback": "...",
                "items": [...],
                "model_version": "..."
            }
        """
        # 세션 평균 지표
        session_avg = {
            "hnr": praat_result.avg_hnr,
            "cpp": praat_result.avg_cpp,
            "csid": praat_result.avg_csid,
            "f0": praat_result.avg_f0,
            "f1": praat_result.avg_f1,
            "f2": praat_result.avg_f2,
            "jitter": praat_result.avg_jitter_local,
            "shimmer": praat_result.avg_shimmer_local,
            "intensity": praat_result.avg_intensity_mean
        }
        
        # 아이템 요약
        items_summary = [
            {
                "index": item["item_index"],
                "text": item["expected_text"],
                "hnr": round(item["praat"]["hnr"], 1) if item["praat"]["hnr"] else None,
                "cpp": round(item["praat"]["cpp"], 2) if item["praat"]["cpp"] else None,
                "csid": round(item["praat"]["csid"], 1) if item["praat"]["csid"] else None,
                "f1": round(item["praat"]["f1"], 0) if item["praat"]["f1"] else None,
                "f2": round(item["praat"]["f2"], 0) if item["praat"]["f2"] else None
            }
            for item in items_data
        ]
        
        # 연습한 단어 리스트 추출
        practiced_words = [item["text"] for item in items_summary]
        words_str = ", ".join([f"'{w}'" for w in practiced_words[:10]])  # 최대 10개
        
        # Few-shot 예시
        few_shot_examples = """
**예시 1 - 좋은 세션:**
입력: hnr=18.2, cpp=13.5, csid=15.8, items=["사과", "나무", "바람"]
출력:
{
  "session_feedback": "오늘 정말 수고 많으셨어요. 목소리를 하나하나 살펴보면서 따뜻한 순간들이 느껴졌어요.\\n\\n🌟 정말 잘하고 계신 부분\\n\\n1) 발음이 정말 또렷해요. '사과', '나무', '바람' 모두에서 끝소리까지 분명하게 들려서 좋았어요.\\n\\n2) 소리가 안정적으로 이어졌어요. 말하는 중간에 흐트러지지 않고 자연스러웠어요.\\n\\n3) 목에 힘이 거의 느껴지지 않았어요. 편안하게 발성하려는 노력이 보였어요.\\n\\n4) 호흡이 안정적이었어요. 중간에 끊기지 않고 매끄럽게 완성되었어요.\\n\\n💭 조금만 더 신경 쓰면 좋을 부분\\n\\n몇몇 순간 소리가 시작될 때 살짝 힘이 들어가는 느낌이 있었어요. 하지만 걱정하지 않으셔도 괜찮아요. 말 시작할 때만 부드럽게 숨을 내보내면 더 편안해질 거예요.\\n\\n🌱 함께 해볼 연습\\n\\n1) 말 시작 전 편안한 숨 내쉬기\\n2) 천천히 연습하기\\n3) 입술과 혀 준비 운동\\n\\n오늘 연습 정말 잘 해주셨어요. 당신의 목소리는 이미 멋진 가능성을 가지고 있어요. 우리, 천천히 같이 걸어봐요. 🌷",
  "items": [
    {"item_index": 0, "vowel_distortion": "발음이 정확해요.", "sound_stability": "소리가 안정적이었어요.", "voice_clarity": "목소리가 맑게 들렸어요.", "voice_health": "목에 무리 없이 말하셨네요.", "overall": "정말 잘하셨어요!"}
  ]
}

**예시 2 - 개선 필요:**
입력: hnr=9.5, cpp=6.2, csid=35.1, items=["구름", "꽃"]
출력:
{
  "session_feedback": "오늘도 연습해주셔서 고마워요. '구름', '꽃'처럼 어려운 단어를 연습하신 것만으로도 큰 의미가 있어요.\\n\\n🌟 잘하고 계신 부분\\n\\n1) 끝까지 연습을 완성하셨어요. 이것만으로도 충분히 칭찬받아야 해요.\\n\\n2) 단어를 정확히 따라하려는 노력이 보였어요.\\n\\n💭 조금만 더 신경 쓰면 좋을 부분\\n\\n소리가 시작될 때 힘이 들어가는 느낌이 있었어요. 하지만 괜찮아요! 조금만 더 편안하게 시작하면 훨씬 부드러워질 거예요. 입 모양이 빠르게 바뀌는 '꽃', '구름' 같은 단어는 천천히 말해보면 더 또렷해질 거예요.\\n\\n🌱 함께 해볼 연습\\n\\n1) 말 전 편안하게 숨 내쉬기\\n2) 천천히 연습하기\\n3) 입술 준비 운동\\n\\n조금씩 나아가고 있어요. 함께 해요! 💚",
  "items": [...]
}
"""
        
        # 프롬프트 구성
        system_prompt = f"""당신은 10년 경력의 음성 언어 치료사입니다.

**당신의 배경:**
- 수백 명의 음성 장애 환자와 함께 성장한 경험
- "함께 걷는다"는 철학으로 환자와 동행
- 작은 발전도 크게 기뻐하고, 실패는 성장의 과정으로 봄

**당신의 말하는 방식:**
- "우리 함께", "조금씩", "천천히" 같은 동행 표현 자주 사용
- 구체적인 예시와 칭찬을 먼저, 개선점은 나중에
- 부정보다는 긍정 프레이밍 ("아직 안 돼요" → "조금만 더 연습하면 돼요")

**중요:** 반드시 아래 JSON 스키마 형식으로만 응답하세요. 
추가 설명이나 마크다운 블록 없이 순수 JSON만 반환하세요.

**JSON 스키마:**
{{
  "session_feedback": "string (500-1000자)",
  "items": [
    {{
      "item_index": number,
      "vowel_distortion": "string (50-100자)",
      "sound_stability": "string (50-100자)",
      "voice_clarity": "string (50-100자)",
      "voice_health": "string (50-100자)",
      "overall": "string (100-150자)"
    }}
  ]
}}

{few_shot_examples}

**절대 금지:**
❌ HNR, CPP, CSID, F1, F2, dB, Hz 같은 전문 용어
❌ 수치 ("15.2", "90%")
❌ 평가 용어 ("우수", "보통", "개선 필요")
❌ 부정어 ("아직", "여전히", "부족")

**필수 포함:**
✅ 실제 연습 단어 최소 3개 언급
✅ "우리 함께", "조금씩", "천천히" 같은 동행 표현"""

        user_prompt = f"""**{user_name}님의 훈련 분석 데이터:**

**세션 전체 평균:**
{json.dumps(session_avg, ensure_ascii=False, indent=2)}

**개별 연습 내용 ({len(items_summary)}개):**
{json.dumps(items_summary, ensure_ascii=False, indent=2)}

**반드시 포함해야 할 연습 단어들:** {words_str}

---

**단계별 분석 과정:**

1. **데이터 해석:** 위 수치들을 보고 어떤 음성 특성이 좋았는지, 개선이 필요한지 먼저 생각하세요.
   - hnr 15+ = 목소리 맑음 / cpp 8+ = 소리 안정 / csid 20- = 목 건강 좋음

2. **긍정 요소 찾기:** 잘하고 있는 부분을 4가지 찾고, 위 연습 단어 중 최소 3개를 구체적 예시로 언급하세요.

3. **개선 제안:** 부드럽고 희망적인 톤으로 1-2가지 제시하세요.

4. **JSON 생성:** 위 분석을 바탕으로 순수 JSON만 반환하세요.

---

**session_feedback 구조 (500-1000자):**

1. 따뜻한 인사 (1-2문장)
2. 잘한 점 4가지 (각 2-3문장, **실제 단어 반드시 포함**)
   - 예: "특히 '사과', '나무'에서 발음이 또렷했어요."
3. 개선점 1-2가지 (부드럽게, "하지만 괜찮아요" 포함)
4. 연습 방법 3가지 (구체적, 실천 가능)
5. 격려 마무리 (2문장)

**items 피드백:**
각 항목당 1-2문장, 자연스럽고 따뜻하게

**검증 체크리스트:**
✓ 연습 단어 중 최소 3개를 session_feedback에 언급했나요?
✓ 전문 용어, 수치, 부정어를 사용하지 않았나요?
✓ 순수 JSON만 반환했나요? (```json 블록 NO)

이 체크리스트를 통과한 후 JSON을 반환하세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # LLM 호출 (GPT-5: reasoning_effort=low, verbosity=medium)
        # 감정적 피드백이므로 verbosity를 medium으로 설정
        response_text = await self.provider.generate(
            prompt=messages,
            model=self.MODEL_VERSION,
            temperature=0.7,  # GPT-5는 무시됨
            max_tokens=4000,
            reasoning_effort="low",  # 빠른 추론
            verbosity="medium"  # 따뜻하고 충분한 설명
        )
        
        # JSON 파싱 및 검증
        result = self._parse_llm_response(response_text)
        
        # 단어 포함 검증
        if not self._validate_word_inclusion(result, items_data):
            logger.warning("[Batch] ⚠️ Feedback doesn't include enough practiced words")
        
        return result
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """LLM 응답 파싱 with robust fallback"""
        original_text = response_text
        
        try:
            # ```json ... ``` 블록 추출
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
                logger.debug("[Batch] Extracted from ```json block")
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
                logger.debug("[Batch] Extracted from ``` block")
            
            result = json.loads(response_text)
            
            # 스키마 검증
            if "session_feedback" not in result:
                raise ValueError("Missing session_feedback field")
            if "items" not in result or not isinstance(result["items"], list):
                raise ValueError("Invalid or missing items field")
            
            # 필수 필드 검증
            for item in result["items"]:
                if "item_index" not in item:
                    logger.warning(f"[Batch] Item missing item_index: {item}")
            
            result["model_version"] = self.MODEL_VERSION
            
            logger.info(f"[Batch] ✅ JSON parsed successfully - {len(result.get('items', []))} item feedbacks")
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"[Batch] Parse failed: {e}")
            logger.error(f"[Batch] Original response (first 1000 chars):\n{original_text[:1000]}")
            
            # Fallback: 최소한의 구조라도 유지
            logger.warning("[Batch] Using fallback - session feedback only")
            return {
                "session_feedback": self._extract_fallback_feedback(original_text),
                "items": [],  # 아이템 피드백은 비움
                "model_version": self.MODEL_VERSION
            }
    
    def _extract_fallback_feedback(self, text: str) -> str:
        """Fallback 시 텍스트에서 피드백 추출"""
        # JSON이 아닌 순수 텍스트라도 의미 있는 부분 추출
        # session_feedback 필드 찾기 시도
        if '"session_feedback"' in text:
            try:
                start = text.find('"session_feedback"') + len('"session_feedback"')
                start = text.find('"', start) + 1
                end = text.find('"', start)
                if end > start:
                    return text[start:end]
            except:
                pass
        
        # 그냥 텍스트 전체 사용 (최대 3000자)
        clean_text = text.replace("```json", "").replace("```", "").strip()
        return clean_text[:3000] if len(clean_text) > 3000 else clean_text
    
    def _validate_word_inclusion(self, feedback: Dict, items_data: List[Dict]) -> bool:
        """피드백에 실제 연습 단어가 포함되었는지 검증"""
        practiced_words = [item["expected_text"] for item in items_data if item.get("expected_text")]
        
        if not practiced_words:
            return True  # 단어 데이터 없으면 검증 스킵
        
        session_text = feedback.get("session_feedback", "")
        
        # 최소 3개 단어 포함 확인 (또는 전체의 30%)
        min_required = min(3, max(1, int(len(practiced_words) * 0.3)))
        mentioned_count = sum(1 for word in practiced_words if word and word in session_text)
        
        if mentioned_count >= min_required:
            logger.info(f"[Batch] ✅ Word inclusion validated: {mentioned_count}/{len(practiced_words)} words mentioned")
            return True
        else:
            logger.warning(f"[Batch] ⚠️ Only {mentioned_count}/{len(practiced_words)} words mentioned (required: {min_required})")
            return False
    
    async def _save_item_feedbacks(
        self,
        items_feedbacks: List[Dict],
        items_data: List[Dict]
    ):
        """개별 아이템 피드백 저장"""
        items_map = {item["item_index"]: item for item in items_data}
        
        for feedback in items_feedbacks:
            item_index = feedback.get("item_index")
            if item_index is None:
                continue
            
            item_data = items_map.get(item_index)
            if not item_data:
                logger.warning(f"[Batch] No data for item_index {item_index}")
                continue
            
            # 중복 체크
            praat_features_id = item_data["praat_features_id"]
            existing = await self.repository.get_item_feedback_by_praat_features_id(
                praat_features_id
            )
            if existing:
                continue
            
            # 저장
            await self.repository.create_item_feedback(
                praat_features_id=praat_features_id,
                vowel_distortion_feedback=feedback.get("vowel_distortion"),
                sound_stability_feedback=feedback.get("sound_stability"),
                voice_clarity_feedback=feedback.get("voice_clarity"),
                voice_health_feedback=feedback.get("voice_health"),
                overall_feedback=feedback.get("overall"),
                model_version=self.MODEL_VERSION
            )
        
        logger.info(f"[Batch] Saved {len(items_feedbacks)} item feedbacks")
    
    async def _save_session_feedback_only(self, praat_result: Any, user_name: str):
        """세션 피드백만 생성 (아이템 없을 때)"""
        logger.info("[Batch] Generating session-only feedback (no items)")
        
        # 아이템이 없어도 세션 평균 데이터로 간단한 피드백 생성
        session_avg = {
            "hnr": praat_result.avg_hnr,
            "cpp": praat_result.avg_cpp,
            "csid": praat_result.avg_csid,
            "f0": praat_result.avg_f0,
        }
        
        simple_prompt = [
            {
                "role": "system", 
                "content": """당신은 따뜻한 음성 치료사입니다.

**역할:** 음성 장애를 겪는 분들에게 희망과 용기를 주는 동반자

**절대 금지:** 전문 용어, 수치, 평가 단어, 부정적 표현
**필수:** "우리 함께", "조금씩", "천천히" 같은 동행 표현"""
            },
            {
                "role": "user", 
                "content": f"""{user_name}님의 음성 평균 데이터: {json.dumps(session_avg, ensure_ascii=False)}

위 데이터를 보고 따뜻한 격려 메시지를 3-5문장으로 작성해주세요.

**구조:**
1. 따뜻한 인사
2. 잘하고 있는 점 1-2가지 칭찬
3. 부드러운 격려 메시지
4. 함께 가자는 마무리

전문 용어나 수치는 절대 사용하지 말고, 자연스럽게 응원해주세요. 💚"""
            }
        ]
        
        feedback_text = await self.provider.generate(
            prompt=simple_prompt,
            model=self.MODEL_VERSION,
            temperature=0.7,
            max_tokens=500,
            reasoning_effort="minimal",  # 간단한 피드백
            verbosity="low"  # 간결하게
        )
        
        await self.repository.create_session_feedback(
            session_praat_result_id=praat_result.id,
            feedback_text=feedback_text,
            model_version=self.MODEL_VERSION
        )
        
        logger.info("[Batch] ✅ Session-only feedback saved")

