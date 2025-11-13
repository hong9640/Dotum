"""
배치 피드백 생성 서비스 (리팩토링 버전)

간결하고 명확한 로직으로 재작성
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import json

from api.src.train.repositories.feedback_repository import FeedbackRepository
from api.src.train.services.llm_feedback import PraatFeedbackService
from api.src.train.models.training_item import TrainingItem
from api.src.train.models.praat import PraatFeatures
from api.src.train.models.media import MediaFile, MediaType
from api.src.train.models.words import TrainWords
from api.src.train.models.sentences import TrainSentences
from api.core.logging import get_logger

logger = get_logger(__name__)


class BatchFeedbackService:
    """배치 피드백 생성 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = FeedbackRepository(db)
        self.llm_service = PraatFeedbackService()
    
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
        
        # 프롬프트 구성
        system_prompt = """당신은 음성 장애를 겪는 분들과 함께하는 따뜻한 음성 치료사입니다.
데이터를 분석하되, 전문 용어나 수치는 절대 사용하지 말고 자연스럽고 감성적으로 표현하세요.

**응답 형식 (반드시 JSON만 반환):**
```json
{
  "session_feedback": "전체 훈련에 대한 따뜻하고 감성적인 피드백 (3-4문단, 희망과 용기를 주는 톤)",
  "items": [
    {
      "item_index": 0,
      "vowel_distortion": "발음에 대한 자연스러운 피드백 (1문장, 전문용어/수치 NO)",
      "sound_stability": "소리 안정감에 대한 감성적 피드백 (1문장, 전문용어/수치 NO)",
      "voice_clarity": "목소리 맑기에 대한 따뜻한 피드백 (1문장, 전문용어/수치 NO)",
      "voice_health": "음성 건강에 대한 격려 피드백 (1문장, 전문용어/수치 NO)",
      "overall": "종합 격려 (2문장, 희망적인 메시지)"
    }
  ]
}
```

**절대 금지:**
- HNR, CPP, CSID, F1, F2, dB, Hz 같은 전문 용어 사용 금지
- 수치 직접 언급 금지 (15.2 dB, 12-20 범위 같은 표현 NO)
- "우수", "보통", "개선 필요", "정상 범위" 같은 평가 표현 금지
- 의학적, 진단적, 분석적 느낌의 문장 금지

**반드시 사용:**
- "목소리가 맑아졌어요", "발음이 정확해졌네요", "호흡이 안정적이에요"
- "이 부분은 정말 좋아요!", "조금만 더 연습해볼까요?"
- 감정이 담긴 자연스러운 표현
- 희망과 용기를 주는 메시지"""

        user_prompt = f"""**{user_name}님, 오늘 훈련 정말 수고 많으셨어요. 💚**

**전체 평균 데이터:**
{json.dumps(session_avg, ensure_ascii=False, indent=2)}

**개별 연습 데이터 ({len(items_summary)}개):**
{json.dumps(items_summary, ensure_ascii=False, indent=2)}

---

위 데이터를 분석하여 JSON 형식으로 피드백을 작성하되,
**전문 용어나 수치는 절대 언급하지 말고** 자연스럽고 따뜻하게 표현하세요.

**작성 원칙:**
- 잘하고 있는 부분: 구체적으로 칭찬 ("목소리가 ~", "발음이 ~")
- 개선할 부분: 부드럽게 제안 ("이 부분은 조금만 더 ~")
- 전체적인 톤: 함께 응원하는 친구 같은 느낌
- 목표: 음성 장애로 힘들어하는 분이 이 피드백을 보고 희망과 용기를 얻도록

**금지 사항:**
- HNR, CPP, dB, Hz 등 전문 용어 사용 금지
- 수치 직접 언급 금지
- "우수", "보통", "개선 필요" 같은 평가 단어 금지
- 분석적, 진단적 느낌의 문장 금지

작은 발전도 크게 기뻐하며, 계속 나아갈 수 있다는 메시지를 전해주세요. 🌱"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # LLM 호출
        response_text = await self.llm_service.provider.generate(
            prompt=messages,
            model=self.llm_service.MODEL_VERSION,
            temperature=0.7,
            max_tokens=4000
        )
        
        # JSON 파싱
        return self._parse_llm_response(response_text)
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """LLM 응답 파싱"""
        try:
            # ```json ... ``` 블록 추출
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            result = json.loads(response_text)
            result["model_version"] = self.llm_service.MODEL_VERSION
            
            logger.info(f"[Batch] JSON parsed - {len(result.get('items', []))} item feedbacks")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"[Batch] JSON parse failed: {e}")
            logger.debug(f"[Batch] Response: {response_text[:500]}...")
            
            # Fallback
            return {
                "session_feedback": response_text[:5000],
                "items": [],
                "model_version": self.llm_service.MODEL_VERSION
            }
    
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
                model_version=self.llm_service.MODEL_VERSION
            )
        
        logger.info(f"[Batch] Saved {len(items_feedbacks)} item feedbacks")
    
    async def _save_session_feedback_only(self, praat_result: Any, user_name: str):
        """세션 피드백만 생성 (아이템 없을 때)"""
        feedback_text, model_version = await self.llm_service.generate_session_feedback(
            praat_result=praat_result,
            user_name=user_name
        )
        
        await self.repository.create_session_feedback(
            session_praat_result_id=praat_result.id,
            feedback_text=feedback_text,
            model_version=model_version
        )

