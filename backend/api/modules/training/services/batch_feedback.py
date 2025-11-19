"""
배치 피드백 생성 서비스 (리팩토링 버전)

간결하고 명확한 로직으로 재작성
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import json

from api.modules.training.repositories.feedback import FeedbackRepository
from api.modules.training.repositories.stt import SttResultsRepository
from api.shared.providers.openai_provider import openai_provider
from api.modules.training.models.training_item import TrainingItem
from api.modules.training.models.training_session import TrainingSession, TrainingType
from api.modules.training.models.praat import PraatFeatures
from api.modules.training.models.media import MediaFile, MediaType
from api.modules.training.models.words import TrainWords
from api.modules.training.models.sentences import TrainSentences
from api.core.logging import get_logger

logger = get_logger(__name__)


class BatchFeedbackService:
    """배치 피드백 생성 서비스"""
    
    MODEL_VERSION = "gpt-5-mini"  # LLM 모델 버전
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = FeedbackRepository(db)
        self.stt_repo = SttResultsRepository(db)
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
            logger.info(f"[Batch] Starting feedback generation for session {session_id} (wav2lip 완료 여부와 무관)")
            
            # 0. AIModel 먼저 생성/조회
            ai_model = await self.repository.get_or_create_ai_model(self.MODEL_VERSION)
            logger.info(f"[Batch] Using AIModel: id={ai_model.id}, version={ai_model.version}")
            
            # 1. SessionPraatResult 조회
            # SessionPraatResult는 세션 완료 시 생성되므로 wav2lip 완료 여부와 무관
            praat_result = await self.repository.get_session_praat_result_by_session_id(session_id)
            if not praat_result:
                logger.warning(f"[Batch] No SessionPraatResult for session {session_id} - 피드백 생성 불가")
                logger.warning(f"[Batch] SessionPraatResult는 세션 완료 시 생성되어야 합니다")
                return False
            
            # 2. 중복 체크
            existing_feedback = await self.repository.get_session_feedback_by_praat_result_id(
                praat_result.id
            )
            if existing_feedback:
                logger.info(f"[Batch] Feedback already exists for session {session_id}")
                return True
            
            # 3. 세션 타입 확인 (STT 사용 여부 결정)
            session_stmt = select(TrainingSession).where(TrainingSession.id == session_id)
            session_result = await self.db.execute(session_stmt)
            session = session_result.scalar_one_or_none()
            session_type = session.type if session else None
            
            # 4. 아이템 데이터 조회
            items_data = await self._get_items_with_praat(session_id, session_type)
            
            if not items_data:
                # 아이템 없으면 세션 피드백만 생성
                logger.info(f"[Batch] No items, generating session feedback only")
                await self._save_session_feedback_only(praat_result, user_name, ai_model.id)
                return True
            
            # 5. 배치 LLM 호출
            batch_result = await self._generate_batch_feedback(
                praat_result, items_data, user_name, session_type
            )
            
            # 5. 세션 피드백 저장
            await self.repository.create_session_feedback(
                session_praat_result_id=praat_result.id,
                feedback_text=batch_result["session_feedback"],
                ai_model_id=ai_model.id
            )
            logger.info(f"[Batch] Session feedback saved")
            
            # 6. 아이템 피드백 저장
            await self._save_item_feedbacks(
                batch_result.get("items", []),
                items_data,
                ai_model.id
            )
            
            logger.info(f"[Batch] ✅ All feedbacks saved for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"[Batch] ❌ Failed: {e}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def _get_items_with_praat(
        self,
        session_id: int,
        session_type: Optional[TrainingType] = None
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
        
        # 5-1. STT 결과 일괄 조회 (WORD/SENTENCE 타입만)
        item_ids = [item.id for item, _ in items_with_video]
        stt_map = {}
        # WORD/SENTENCE 타입일 때만 STT 조회 (VOCAL은 STT 불필요)
        if item_ids and session_type in (TrainingType.WORD, TrainingType.SENTENCE):
            from ..models.training_item_stt_results import TrainingItemSttResults
            stt_stmt = select(TrainingItemSttResults).where(
                TrainingItemSttResults.training_item_id.in_(item_ids)
            ).order_by(TrainingItemSttResults.created_at.desc())
            stt_result = await self.db.execute(stt_stmt)
            stt_list = stt_result.scalars().all()
            # 각 item_id별 최신 STT 결과만 저장
            for stt in stt_list:
                if stt.training_item_id not in stt_map:
                    stt_map[stt.training_item_id] = stt.stt_result
            logger.debug(f"[Batch] Loaded {len(stt_map)} STT results (type: {session_type})")
        else:
            logger.debug(f"[Batch] STT skipped (type: {session_type}, VOCAL은 Praat 지표만 사용)")
        
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
            
            # STT 결과 조회
            stt_result = stt_map.get(item.id)
            
            items_data.append({
                "item_index": item.item_index,
                "praat_features_id": praat.id,
                "expected_text": expected_text or f"item_{item.item_index}",
                "stt_result": stt_result,  # STT 결과 추가
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
        user_name: str,
        session_type: Optional[TrainingType] = None
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
        
        # 아이템 요약 (STT 결과 포함)
        items_summary = []
        for item in items_data:
            item_summary = {
                "index": item["item_index"],
                "hnr": round(item["praat"]["hnr"], 1) if item["praat"]["hnr"] else None,
                "cpp": round(item["praat"]["cpp"], 2) if item["praat"]["cpp"] else None,
                "csid": round(item["praat"]["csid"], 1) if item["praat"]["csid"] else None,
                "f0": round(item["praat"].get("f0", 0), 0) if item["praat"].get("f0") else None,
                "f1": round(item["praat"]["f1"], 0) if item["praat"]["f1"] else None,
                "f2": round(item["praat"]["f2"], 0) if item["praat"]["f2"] else None,
                "jitter": round(item["praat"]["jitter_local"], 3) if item["praat"].get("jitter_local") else None,
                "shimmer": round(item["praat"]["shimmer_local"], 3) if item["praat"].get("shimmer_local") else None,
                "intensity": round(item["praat"]["intensity_mean"], 1) if item["praat"].get("intensity_mean") else None
            }
            # WORD/SENTENCE 타입만 expected_text와 stt_result 포함
            if session_type in (TrainingType.WORD, TrainingType.SENTENCE):
                item_summary["expected_text"] = item["expected_text"]  # 말해야 할 텍스트
                item_summary["stt_result"] = item.get("stt_result")  # STT로 인식된 텍스트
            items_summary.append(item_summary)
        
        # 연습한 단어 리스트 추출 (WORD/SENTENCE 타입만)
        if session_type in (TrainingType.WORD, TrainingType.SENTENCE):
            practiced_words = [item.get("expected_text") for item in items_summary if item.get("expected_text")]
            words_str = ", ".join([f"'{w}'" for w in practiced_words[:10]])  # 최대 10개
        else:
            words_str = ""  # VOCAL 타입은 단어 없음
        
        # Few-shot 예시
        few_shot_examples = """
**예시 1 - 좋은 세션:**
입력: hnr=18.2, cpp=13.5, csid=15.8, items=["사과", "나무", "바람"]
출력:
{
  "session_feedback": "오늘 정말 수고 많으셨어요! '사과', '나무', '바람' 모두에서 발음이 또렷하고 안정적이었어요. 목에 무리 없이 편안하게 발성하신 게 인상적이었어요. 조금만 더 연습하면 더욱 완벽해질 거예요! 🌷",
  "items": [
    {
      "item_index": 0,
      "item_feedback": "'사과' 발음이 정말 또렷했어요. 끝소리까지 분명하게 들려서 좋았고, 목에도 무리가 없어 보였어요. 정말 잘하셨어요!",
      "vowel_distortion_feedback": "'사과'의 모음이 또렷하게 들렸어요. 입술 모양이 자연스럽게 만들어져서 좋았어요.",
      "sound_stability_feedback": "전체적인 흐름이 안정적이었어요. 소리가 중간에 흔들리지 않고 매끄럽게 이어졌어요.",
      "voice_clarity_feedback": "목소리가 맑고 선명하게 들렸어요. 끝소리까지 분명하게 전달되어 좋았어요.",
      "voice_health_feedback": "말할 때 목에 힘이 들어가지 않고 자연스럽게 발성하신 게 잘 느껴졌어요.",
      "overall_feedback": "전반적으로 안정적이고 맑은 발성이었어요. 특히 모음 발음이 또렷해서 좋았어요."
    },
    {
      "item_index": 1,
      "item_feedback": "'나무'에서 소리가 안정적으로 이어졌어요. 중간에 흐트러지지 않고 자연스럽게 완성하셨네요!",
      "vowel_distortion_feedback": "'나무'의 모음이 자연스럽게 들렸어요. 입술과 혀의 위치가 적절했어요.",
      "sound_stability_feedback": "소리가 시작부터 끝까지 안정적으로 유지되었어요. 흔들림 없이 매끄러웠어요.",
      "voice_clarity_feedback": "목소리가 선명하게 전달되었어요. 각 음절이 또렷하게 들렸어요.",
      "voice_health_feedback": "편안하게 발성하려는 노력이 느껴졌어요. 목에 무리가 없어 보였어요.",
      "overall_feedback": "안정적인 발성이었어요. 특히 소리의 연속성이 좋아서 자연스러웠어요."
    },
    {
      "item_index": 2,
      "item_feedback": "'바람' 발음도 훌륭해요. 편안하게 발성하려는 노력이 느껴졌어요.",
      "vowel_distortion_feedback": "'바람'의 모음이 또렷하게 들렸어요. 입술을 둥글게 모으는 것이 자연스러웠어요.",
      "sound_stability_feedback": "전체적인 흐름이 괜찮았어요. 마지막 소리까지 안정적으로 유지되었어요.",
      "voice_clarity_feedback": "목소리가 맑게 들렸어요. 끝소리까지 분명하게 전달되어 좋았어요.",
      "voice_health_feedback": "편안하게 발성하려는 노력이 잘 느껴졌어요. 목에 힘이 들어가지 않았어요.",
      "overall_feedback": "훌륭한 발성이었어요. 편안하면서도 또렷한 발음이 인상적이었어요."
    }
  ]
}

**예시 2 - 개선 필요:**
입력: hnr=9.5, cpp=6.2, csid=35.1, items=["구름", "꽃"]
출력:
{
  "session_feedback": "오늘도 연습해주셔서 고마워요! '구름', '꽃'처럼 어려운 단어를 끝까지 완성하신 게 대단해요. 조금만 더 천천히 말하고 입 모양을 준비하면 더 또렷해질 거예요. 함께 해요! 💚",
  "items": [
    {
      "item_index": 0,
      "item_feedback": "'구름'처럼 복잡한 발음을 끝까지 완성하신 게 대단해요. 조금만 더 천천히 말하면 더 또렷해질 거예요!",
      "vowel_distortion_feedback": "'구름'의 모음이 조금 아쉬웠어요. 입술을 조금 더 둥글게 모아주면 모음이 더 분명하게 들릴 거예요.",
      "sound_stability_feedback": "전체적인 흐름은 괜찮았지만, 마지막 소리에서 살짝 흔들리는 순간이 있었어요. 천천히 말하면 더 안정적일 거예요.",
      "voice_clarity_feedback": "끝소리가 단어의 목표 음과 조금 다르게 들렸어요. 마무리 부분을 천천히 닫아주면 전달이 더 선명해질 거예요.",
      "voice_health_feedback": "말할 때 목에 힘이 들어가지 않고 자연스럽게 발성하신 게 잘 느껴졌어요. 이 부분은 계속 유지해주세요.",
      "overall_feedback": "복잡한 발음을 끝까지 완성하신 게 대단해요. 조금만 더 천천히 연습하면 더욱 완벽해질 거예요."
    },
    {
      "item_index": 1,
      "item_feedback": "'꽃' 발음도 끝까지 노력하셨어요. 입 모양 준비를 충분히 하면 더 자연스러워질 거예요.",
      "vowel_distortion_feedback": "'꽃'의 모음이 충분히 둥글게 만들어지지 않아 '깍'처럼 들렸어요. 입술을 조금 더 둥글게 모아주면 모양이 더 또렷하게 잡힐 거예요.",
      "sound_stability_feedback": "전체적인 흐름은 괜찮았어요. 다만 입 모양이 빠르게 바뀌는 부분에서 살짝 불안정했어요.",
      "voice_clarity_feedback": "끝소리가 조금 약하게 들렸어요. 마무리 부분을 천천히 닫아주면 더 선명해질 거예요.",
      "voice_health_feedback": "목에 무리가 없이 발성하려는 노력이 느껴졌어요. 이 부분은 잘하고 계세요.",
      "overall_feedback": "끝까지 노력하신 게 대단해요. 입 모양 준비를 충분히 하면 더 자연스럽고 또렷한 발음이 될 거예요."
    }
  ]
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
  "session_feedback": "string (50-100자, 한 줄 요약 - 전체 세션을 간결하게 요약한 따뜻한 격려 메시지)",
  "items": [
    {{
      "item_index": number,
      "item_feedback": "string (100-200자, 해당 아이템에 대한 따뜻한 피드백)",
      "vowel_distortion_feedback": "string (50-100자, 모음 왜곡도 피드백 - F1, F2 포먼트 기반)",
      "sound_stability_feedback": "string (50-100자, 소리의 안정도 피드백 - CPP 기반)",
      "voice_clarity_feedback": "string (50-100자, 음성 맑음도 피드백 - HNR 기반)",
      "voice_health_feedback": "string (50-100자, 음성 건강지수 피드백 - CSID 기반)",
      "overall_feedback": "string (100-150자, 전체 종합 피드백)"
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
✅ 실제 연습 단어 최소 3개 언급 (WORD/SENTENCE 타입)
✅ "우리 함께", "조금씩", "천천히" 같은 동행 표현"""

        # WORD/SENTENCE 타입일 때만 STT 관련 프롬프트 추가
        stt_pronunciation_guide = ""
        if session_type in (TrainingType.WORD, TrainingType.SENTENCE):
            stt_pronunciation_guide = """

**한국어 발음 특성 고려 (WORD/SENTENCE 타입):**
- **구개음화**: "굳이" → "구지" (정상, /ㄷ/이 /ㅈ/로 발음되는 현상)
- **비음화**: "밥물" → "밤물" (정상)
- **유음화**: "할 일" → "할릴" (정상)
- **경음화**: "좋다" → "좋따" (정상)

**STT 발음 판별 규칙:**
1. **정상 발음**: 예상 텍스트와 STT 결과가 한국어 음운 규칙에 따라 변형된 경우
   - 예: "굳이" → "구지" ✅ 정상 (구개음화)
   - 예: "꽃이" → "꼬치" ✅ 정상 (구개음화)
   
2. **발음 오류**: 예상 텍스트와 STT 결과가 음운 규칙과 무관하게 다를 경우
   - 예: "굳이" → "뭣이" ❌ 발음 오류
   - 예: "꽃" → "꽅" ❌ 발음 오류

3. **비한글 문자 처리 (중요)**:
   - stt_result가 한글이 아닌 다른 문자(중국어 한자, 일본어, 알파벳 등)로 표시된 경우:
     a) 한국어 화자가 읽었을 때 어떤 발음에 가장 가까울지 상상
     b) 그 소리를 한국어 음절로 옮겨 적기 (예: "当空" → "당공")
     c) 피드백 작성 시 원래 문자열("当空")은 사용하지 않고 한국어 표기("당공")만 사용
     d) 예: expected_text="땅콩", stt_result="当空" → "원래 단어는 '땅콩'인데 실제로는 '당공'에 가깝게 들렸어요"

4. **피드백 작성 시**:
   - 정상 발음: 칭찬하고 넘어가기
   - 발음 오류: 부드럽게 교정 제안 (부담 주지 않기)"""
        
        system_prompt = system_prompt + stt_pronunciation_guide

        user_prompt = f"""**{user_name}님의 훈련 분석 데이터:**

**세션 전체 평균:**
{json.dumps(session_avg, ensure_ascii=False, indent=2)}

**개별 연습 내용 ({len(items_summary)}개):**
각 아이템에는 다음 정보가 포함되어 있습니다:"""

        # WORD/SENTENCE 타입: STT 정보 포함, VOCAL 타입: Praat 지표만
        if session_type in (TrainingType.WORD, TrainingType.SENTENCE):
            words_prompt = f"\n**반드시 포함해야 할 연습 단어들:** {words_str}" if words_str else ""
            user_prompt_additional = f"""
- expected_text: 말해야 할 텍스트
- stt_result: STT로 실제 인식된 텍스트 (null일 수 있음, 한글이 아닌 문자일 수 있음)
- hnr, cpp, csid, f1, f2: 음성 분석 지표

{json.dumps(items_summary, ensure_ascii=False, indent=2)}{words_prompt}

---

**[WORD/SENTENCE 타입에서의 규칙]**

**STT 발음 평가:**
- expected_text(말해야 할 텍스트)와 stt_result(STT 인식 결과)를 비교하여 발음을 평가해 주세요.

**비한글 문자 처리 (중요):**
- stt_result가 한글이 아닌 다른 문자(중국어 한자, 일본어, 알파벳 등)로 표시된 경우:
  1) stt_result를 한국어 화자가 읽었을 때 어떤 발음에 가장 가까울지 상상해 보고,
     그 소리를 한국어 음절로 옮겨 적는다고 생각해 주세요.
     - 예: "当空" → "당공"처럼, 한국어 화자가 읽을 법한 소리를 떠올립니다.
  
  2) 이렇게 얻은 한국어 표기를, 사용자가 실제로 발음한 형태라고 간주합니다.
     - 위 예시에서는 사용자가 "당공"에 가깝게 발음한 것으로 봅니다.
  
  3) 피드백을 작성할 때는 stt_result의 원래 문자열("当空")은 그대로 쓰지 말고,
     위에서 얻은 한국어 표기("당공")만 사용해 주세요.
     - 예: expected_text가 "땅콩"이고 stt_result가 "当空"이라면,
       내부적으로 stt_result를 "당공"으로 치환해서,
       "원래 단어는 '땅콩'인데 실제로는 '당공'에 가깝게 들렸어요"처럼 설명합니다.

**발음 평가 기준:**
- 한국어 안에서 자연스럽게 일어나는 발음 차이(비슷한 소리로 바뀌는 정도)는
  정상적인 변이로 보고,
  의미나 소리가 꽤 다르게 느껴지는 경우에만 발음 오류로 간주해 주세요.

- 발음 오류가 있다고 판단되더라도,
  부담을 주지 않는 선에서 부드럽게 올바른 발음을 제안해 주세요.
  - 예: "처음 소리가 조금 약해져서 '땅콩'이 '당공'처럼 들렸어요.
         처음 소리를 조금 더 또렷하게 내 보면 좋을 것 같아요." 처럼 설명합니다.

**단계별 분석 과정:**

1. **STT 발음 분석 (우선순위 1):**
   - 각 아이템의 expected_text와 stt_result를 비교하세요
   - stt_result가 비한글 문자면 한국어 발음으로 변환하여 비교하세요
   - 한국어 음운 규칙(구개음화, 비음화, 유음화, 경음화)을 고려하여 발음이 정상인지 판별하세요
   - 발음 오류가 있으면 구체적으로 어떤 부분이 다른지 파악하세요

2. **데이터 해석:**
   - 위 수치들을 보고 어떤 음성 특성이 좋았는지, 개선이 필요한지 먼저 생각하세요.
   - hnr 15+ = 목소리 맑음 / cpp 8+ = 소리 안정 / csid 20- = 목 건강 좋음

3. **긍정 요소 찾기:**
   - 잘하고 있는 부분을 3~4가지 찾고, 위 연습 단어 중 일부를 자연스럽게 언급하세요.
   - STT 발음이 정확한 경우도 칭찬 포인트입니다

4. **개선 제안:**
   - 부드럽고 희망적인 톤으로 1~2가지 제시하세요.
   - 발음 오류가 있으면 한국어 음운 규칙을 고려하여 부드럽게 교정 제안하세요

5. **JSON 생성:**
   - 위 분석을 바탕으로 순수 JSON만 반환하세요."""
        else:
            # VOCAL 타입: Praat 지표만 사용 (STT 없음)
            user_prompt_additional = f"""
- hnr, cpp, csid, f0, f1, f2, jitter, shimmer, intensity: 음성 분석 지표 (Praat)
- VOCAL 타입은 발성 훈련이므로 텍스트 발음 판별 없이 Praat 지표만으로 피드백 생성

{json.dumps(items_summary, ensure_ascii=False, indent=2)}

---

**단계별 분석 과정 (VOCAL 타입 - Praat 지표 중심):**

1. **데이터 해석:** 위 Praat 지표들을 보고 어떤 음성 특성이 좋았는지, 개선이 필요한지 먼저 생각하세요.
   - hnr 15+ = 목소리 맑음 / cpp 8+ = 소리 안정 / csid 20- = 목 건강 좋음
   - jitter 낮음 = 음정 안정 / shimmer 낮음 = 음량 안정

2. **긍정 요소 찾기:** 잘하고 있는 부분을 4가지 찾으세요.
   - Praat 지표가 양호한 경우 구체적으로 칭찬하세요

3. **개선 제안:** 부드럽고 희망적인 톤으로 1-2가지 제시하세요.
   - 발성 방법, 호흡, 목소리 사용 방법 등에 대한 제안

4. **JSON 생성:** 위 분석을 바탕으로 순수 JSON만 반환하세요."""
        
        user_prompt = user_prompt + user_prompt_additional
        
        # 공통 피드백 구조
        feedback_structure = """

---

**session_feedback 구조 (50-100자, 한 줄 요약):**

1. 따뜻한 인사 (1문장)
2. 잘한 점 간단히 언급 (실제 단어 포함 - WORD/SENTENCE 타입만)
3. 부드러운 격려 메시지 (1문장)

**중요:** 반드시 50-100자 이내로 간결하게 작성하세요. 여러 문단으로 나누지 말고 한 줄로 요약하세요."""

        if session_type in (TrainingType.WORD, TrainingType.SENTENCE):
            feedback_structure += f"""
   - 예: "오늘 정말 수고 많으셨어요! '사과', '나무' 모두에서 발음이 또렷했어요. 조금만 더 연습하면 더욱 완벽해질 거예요! 🌷"
   - 연습 단어 후보: {words_str if words_str else "연습 단어 정보 없음"}

**items 배열 작성 가이드:**
- 각 아이템에 대해:
  - item_index를 그대로 사용합니다.
  - item_feedback에는 해당 단어나 문장 발화를 상상하며,
    좋았던 점과 한두 가지 부드러운 제안을 100~200자 정도로 작성합니다.
  - 가능한 경우, 해당 아이템의 expected_text를 자연스럽게 언급해 주세요.
  
**세부 피드백 작성 가이드 (각 아이템별 필수):**
각 아이템의 Praat 지표(F1, F2, CPP, HNR, CSID)를 분석하여 다음 5가지 피드백을 작성하세요:

1. **vowel_distortion_feedback (모음 왜곡도)**: 
   - F1, F2 포먼트 값을 기반으로 모음의 왜곡 정도를 평가
   - 예: "'과'의 모음이 충분히 둥글게 만들어지지 않아 '가'처럼 들렸어요. 입술을 조금 더 둥글게 모아주면 모양이 더 또렷하게 잡힐 거예요."
   - 부드럽고 구체적인 개선 제안 포함

2. **sound_stability_feedback (소리의 안정도)**:
   - CPP 값을 기반으로 음성의 안정성과 맑음을 평가
   - 예: "전체적인 흐름은 괜찮았지만, 마지막 소리에서 살짝 흔들리는 순간이 있었어요."
   - 안정적인 부분 칭찬 + 개선 제안

3. **voice_clarity_feedback (음성 맑음도)**:
   - HNR 값을 기반으로 하모닉 대 노이즈 비율 평가
   - 예: "끝소리가 단어의 목표 음과 조금 다르게 들렸어요. 마무리 부분을 천천히 닫아주면 전달이 더 선명해질 거예요."
   - 맑은 부분 칭찬 + 개선 제안

4. **voice_health_feedback (음성 건강지수)**:
   - CSID 값을 기반으로 음성 건강 상태 종합 평가
   - 예: "말할 때 목에 힘이 들어가지 않고 자연스럽게 발성하신 게 잘 느껴졌어요."
   - 건강한 부분 강조 + 유지 방법 제안

5. **overall_feedback (종합 피드백)**:
   - 위 4가지 항목을 종합하여 전체적인 평가와 격려
   - 예: "전반적으로 안정적인 발성이었어요. 모음 부분만 조금 더 신경 쓰면 더욱 완벽해질 거예요."
   - 긍정적이고 희망적인 톤으로 마무리

**STT 발음 피드백 작성 가이드:**
1. STT 결과가 정상인 경우 (예: "굳이" → "구지"):
   - "발음이 정확했어요!" 또는 "구개음화가 자연스럽게 적용되어 좋았어요" 등으로 칭찬

2. STT 결과가 비한글 문자인 경우:
   - 한국어 발음으로 변환하여 평가 (예: "当空" → "당공")
   - 피드백에는 원래 문자열("当空") 대신 한국어 표기("당공")만 사용
   - 예: "원래 단어는 '땅콩'인데 실제로는 '당공'에 가깝게 들렸어요"

3. STT 결과가 오류인 경우 (예: "굳이" → "뭣이"):
   - 부드럽게 지적: "처음 소리가 조금 약해져서 '굳이'가 '뭣이'처럼 들렸어요."
   - 구체적인 교정 제안: "'굳이'처럼 발음해보시면 어떨까요? 입 모양을 조금만 더 조심해보세요."
   - 절대 부정적이지 않게: "조금만 더 연습하면 완벽해질 거예요" 같은 격려 포함"""
        else:
            feedback_structure += """
3. 개선점 1-2가지 (부드럽게, "하지만 괜찮아요" 포함)
4. 연습 방법 3가지 (구체적, 실천 가능)
5. 격려 마무리 (2문장)

**items 피드백 (item_feedback):**
각 아이템당 100-200자, 해당 아이템에 대한 구체적이고 따뜻한 피드백

**세부 피드백 작성 가이드 (각 아이템별 필수):**
각 아이템의 Praat 지표(F1, F2, CPP, HNR, CSID)를 분석하여 다음 5가지 피드백을 작성하세요:

1. **vowel_distortion_feedback (모음 왜곡도)**: 
   - F1, F2 포먼트 값을 기반으로 모음의 왜곡 정도를 평가
   - 예: "'과'의 모음이 충분히 둥글게 만들어지지 않아 '가'처럼 들렸어요. 입술을 조금 더 둥글게 모아주면 모양이 더 또렷하게 잡힐 거예요."
   - 부드럽고 구체적인 개선 제안 포함

2. **sound_stability_feedback (소리의 안정도)**:
   - CPP 값을 기반으로 음성의 안정성과 맑음을 평가
   - 예: "전체적인 흐름은 괜찮았지만, 마지막 소리에서 살짝 흔들리는 순간이 있었어요."
   - 안정적인 부분 칭찬 + 개선 제안

3. **voice_clarity_feedback (음성 맑음도)**:
   - HNR 값을 기반으로 하모닉 대 노이즈 비율 평가
   - 예: "끝소리가 단어의 목표 음과 조금 다르게 들렸어요. 마무리 부분을 천천히 닫아주면 전달이 더 선명해질 거예요."
   - 맑은 부분 칭찬 + 개선 제안

4. **voice_health_feedback (음성 건강지수)**:
   - CSID 값을 기반으로 음성 건강 상태 종합 평가
   - 예: "말할 때 목에 힘이 들어가지 않고 자연스럽게 발성하신 게 잘 느껴졌어요."
   - 건강한 부분 강조 + 유지 방법 제안

5. **overall_feedback (종합 피드백)**:
   - 위 4가지 항목을 종합하여 전체적인 평가와 격려
   - 예: "전반적으로 안정적인 발성이었어요. 모음 부분만 조금 더 신경 쓰면 더욱 완벽해질 거예요."
   - 긍정적이고 희망적인 톤으로 마무리

**Praat 지표 피드백 작성 가이드 (VOCAL 타입):**
1. Praat 지표가 양호한 경우:
   - "목소리가 맑고 안정적이에요!" 또는 "호흡이 자연스러웠어요" 등으로 칭찬

2. 개선이 필요한 경우:
   - 부드럽게 지적: "목소리를 조금만 더 편안하게 내면 좋을 것 같아요"
   - 구체적인 발성 제안: "복식 호흡을 해보시면 어떨까요?" 또는 "턱을 조금만 더 내려주세요"
   - 절대 부정적이지 않게: "조금만 더 연습하면 완벽해질 거예요" 같은 격려 포함"""
        
        user_prompt = user_prompt + feedback_structure

        # 검증 체크리스트
        # session_feedback 길이 검증 추가
        checklist = """

**검증 체크리스트:**"""
        if session_type in (TrainingType.WORD, TrainingType.SENTENCE):
            checklist += """
✓ 연습 단어 중 최소 2-3개를 session_feedback에 언급했나요?"""
        checklist += """
✓ session_feedback이 50-100자 이내로 간결하게 작성되었나요? (한 줄 요약)
✓ 전문 용어, 수치, 부정어를 사용하지 않았나요?
✓ 순수 JSON만 반환했나요? (```json 블록 NO)

이 체크리스트를 통과한 후 JSON을 반환하세요."""
        
        user_prompt = user_prompt + checklist

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
                if "item_feedback" not in item:
                    logger.warning(f"[Batch] Item missing item_feedback: {item}")
                # 세부 피드백 필드들은 선택사항이지만 있으면 좋음
                if "vowel_distortion_feedback" not in item:
                    logger.debug(f"[Batch] Item {item.get('item_index')} missing vowel_distortion_feedback (optional)")
                if "sound_stability_feedback" not in item:
                    logger.debug(f"[Batch] Item {item.get('item_index')} missing sound_stability_feedback (optional)")
                if "voice_clarity_feedback" not in item:
                    logger.debug(f"[Batch] Item {item.get('item_index')} missing voice_clarity_feedback (optional)")
                if "voice_health_feedback" not in item:
                    logger.debug(f"[Batch] Item {item.get('item_index')} missing voice_health_feedback (optional)")
                if "overall_feedback" not in item:
                    logger.debug(f"[Batch] Item {item.get('item_index')} missing overall_feedback (optional)")
            
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
        items_data: List[Dict],
        ai_model_id: int
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
            
            # 저장 (세부 피드백 포함)
            await self.repository.create_item_feedback(
                praat_features_id=praat_features_id,
                item_feedback=feedback.get("item_feedback"),
                ai_model_id=ai_model_id,
                vowel_distortion_feedback=feedback.get("vowel_distortion_feedback"),
                sound_stability_feedback=feedback.get("sound_stability_feedback"),
                voice_clarity_feedback=feedback.get("voice_clarity_feedback"),
                voice_health_feedback=feedback.get("voice_health_feedback"),
                overall_feedback=feedback.get("overall_feedback")
            )
        
        logger.info(f"[Batch] Saved {len(items_feedbacks)} item feedbacks")
    
    async def _save_session_feedback_only(self, praat_result: Any, user_name: str, ai_model_id: int):
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
            ai_model_id=ai_model_id
        )
        
        logger.info("[Batch] ✅ Session-only feedback saved")

