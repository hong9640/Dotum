import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from google.cloud import storage
from google.cloud.exceptions import NotFound
from api.core.config import Settings
from api.utils.utils import sanitize_username_for_path, generate_file_path


class GCSService:
    """GCS 파일 관리 서비스"""
    
    def __init__(self, settings: Settings):
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.project_id = settings.GCS_PROJECT_ID
        self.credentials_path = settings.GCS_CREDENTIALS_PATH
        
        # GCS 클라이언트 초기화
        if self.credentials_path and os.path.exists(self.credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
        
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
    
    def generate_video_path(
        self, 
        username: str, 
        session_id: str,
        train_id: Optional[int] = None,
        result_id: Optional[int] = None,
        word_id: Optional[int] = None,
        sentence_id: Optional[int] = None,
        item_index: Optional[int] = None
    ) -> str:
        """
        동영상 파일 경로 생성
        형식: videos/{username}/{session_id}/(type:train/result)_(train_id/result_id)_(type:word/sentence)_(word_id/sentence_id).mp4
        VOCAL 타입: videos/{username}/{session_id}/train_item_{item_index}_vocal.mp4
        """
        return generate_file_path(
            base_path="videos",
            username=username,
            session_id=session_id,
            train_id=train_id,
            result_id=result_id,
            word_id=word_id,
            sentence_id=sentence_id,
            item_index=item_index
        )
    
    
    async def upload_video(
        self, 
        file_path: str, # 파일 경로를 받도록 변경
        username: str, 
        session_id: str,
        train_id: Optional[int] = None,
        result_id: Optional[int] = None,
        word_id: Optional[int] = None,
        sentence_id: Optional[int] = None,
        item_index: Optional[int] = None,
        original_filename: str = "",
        content_type: str = "video/mp4"
    ) -> dict:
        """
        동영상 파일을 GCS에 업로드
        
        Args:
            file_path: 업로드할 파일의 로컬 경로
            username: 사용자명
            session_id: 세션 ID
            train_id: 훈련 ID (단어 훈련용)
            result_id: 결과 ID (문장 훈련용)
            word_id: 단어 ID
            sentence_id: 문장 ID
            item_index: 아이템 인덱스 (VOCAL 타입용)
            original_filename: 원본 파일명 (선택사항)
            content_type: MIME 타입
            
        Returns:
            dict: 업로드 결과 정보
        """
        try:
            # GCS 경로 생성
            object_path = self.generate_video_path(
                username=username,
                session_id=session_id,
                train_id=train_id,
                result_id=result_id,
                word_id=word_id,
                sentence_id=sentence_id,
                item_index=item_index
            )
            
            # GCS 객체 생성
            blob = self.bucket.blob(object_path)
            
            # 메타데이터 설정
            blob.metadata = {
                "username": username,
                "session_id": session_id,
                "train_id": str(train_id) if train_id else None,
                "result_id": str(result_id) if result_id else None,
                "word_id": str(word_id) if word_id else None,
                "sentence_id": str(sentence_id) if sentence_id else None,
                "original_filename": original_filename,
                "upload_date": datetime.now().isoformat(),
                "file_type": "video"
            }
            
            # 파일 업로드
            blob.upload_from_filename(file_path, content_type=content_type)
            
            # 공개 URL 생성 (필요시)
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{object_path}"
            
            # 파일 크기 가져오기
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "object_path": object_path,
                "public_url": public_url,
                "filename": object_path.split('/')[-1],
                "file_size": file_size,
                "content_type": content_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "object_path": None
            }
    
    
    async def download_video(self, object_path: str) -> Optional[bytes]:
        """
        GCS에서 동영상 파일 다운로드
        
        Args:
            object_path: GCS 객체 경로
            
        Returns:
            bytes: 파일 바이너리 데이터 또는 None
        """
        try:
            blob = self.bucket.blob(object_path)
            if not blob.exists():
                return None
            
            return blob.download_as_bytes()
            
        except NotFound:
            return None
        except Exception as e:
            print(f"다운로드 오류: {e}")
            return None
    
    async def delete_video(self, object_path: str) -> bool:
        """
        GCS에서 동영상 파일 삭제
        
        Args:
            object_path: GCS 객체 경로
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            blob = self.bucket.blob(object_path)
            blob.delete()
            return True
            
        except NotFound:
            return False
        except Exception as e:
            print(f"삭제 오류: {e}")
            return False
    
    async def get_signed_url(
        self, 
        object_path: str, 
        expiration_hours: int = 1
    ) -> Optional[str]:
        """
        서명된 URL 생성 (임시 접근용)
        
        Args:
            object_path: GCS 객체 경로
            expiration_hours: 만료 시간 (시간)
            
        Returns:
            str: 서명된 URL 또는 None
        """
        try:
            blob = self.bucket.blob(object_path)
            if not blob.exists():
                return None
            
            expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
            return blob.generate_signed_url(expiration=expiration)
            
        except Exception as e:
            print(f"서명된 URL 생성 오류: {e}")
            return None
    
    async def get_signed_urls_batch(
        self, 
        object_paths: list[str], 
        expiration_hours: int = 1
    ) -> dict[str, Optional[str]]:
        """
        여러 객체에 대한 서명된 URL을 일괄 생성 (병렬 처리)
        
        Args:
            object_paths: GCS 객체 경로 리스트
            expiration_hours: 만료 시간 (시간)
            
        Returns:
            dict: {object_path: signed_url} 매핑 (실패 시 None)
        """
        import asyncio
        
        async def get_url_safe(path: str) -> tuple[str, Optional[str]]:
            """개별 URL 생성을 안전하게 수행"""
            url = await self.get_signed_url(path, expiration_hours)
            return (path, url)
        
        # 모든 URL 생성을 병렬로 실행
        tasks = [get_url_safe(path) for path in object_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과를 딕셔너리로 변환
        url_map = {}
        for result in results:
            if isinstance(result, Exception):
                print(f"배치 URL 생성 오류: {result}")
                continue
            path, url = result
            url_map[path] = url
        
        return url_map
    
    async def list_user_videos(
        self, 
        username: str, 
        session_filter: Optional[str] = None
    ) -> list:
        """
        사용자의 동영상 파일 목록 조회
        
        Args:
            username: 사용자명
            session_filter: 세션 필터 (특정 세션만 조회)
            
        Returns:
            list: 동영상 파일 정보 목록
        """
        try:
            safe_username = sanitize_username_for_path(username)
            prefix = f"videos/{safe_username}/"
            
            if session_filter:
                prefix += f"{session_filter}/"
            
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            
            videos = []
            for blob in blobs:
                if blob.name.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                    videos.append({
                        "object_path": blob.name,
                        "filename": blob.name.split('/')[-1],
                        "size": blob.size,
                        "created": blob.time_created,
                        "content_type": blob.content_type,
                        "metadata": blob.metadata or {}
                    })
            
            return videos
            
        except Exception as e:
            print(f"파일 목록 조회 오류: {e}")
            return []
    


# 전역 GCS 서비스 인스턴스
_gcs_service: Optional[GCSService] = None


def get_gcs_service(settings: Settings) -> GCSService:
    """GCS 서비스 인스턴스 반환 (싱글톤 패턴)"""
    global _gcs_service
    if _gcs_service is None:
        _gcs_service = GCSService(settings)
    return _gcs_service
