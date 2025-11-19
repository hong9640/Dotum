import os
from google.cloud import storage
from google.cloud.exceptions import NotFound
from api.core.config import settings
from api.core.logger import logger


class GCSClient:
    """Google Cloud Storage 클라이언트 래퍼"""
    
    def __init__(self):
        """GCS 클라이언트 초기화"""
        try:
            # 서비스 계정 키 파일 경로 설정
            if settings.GCS_CREDENTIAL_PATH and os.path.exists(settings.GCS_CREDENTIAL_PATH):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GCS_CREDENTIAL_PATH
                logger.info(f"GCS credentials loaded from: {settings.GCS_CREDENTIAL_PATH}")
            else:
                logger.warning("GCS credentials path not found, using default authentication")
            
            self.client = storage.Client(project=settings.GCP_PROJECT_ID)
            self.bucket = self.client.bucket(settings.GCS_BUCKET)
            logger.info(f"GCS client initialized for bucket: {settings.GCS_BUCKET}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise

    def download_file(self, gs_path: str, local_path: str) -> bool:
        """
        GCS에서 파일 다운로드
        
        Args:
            gs_path: GCS 경로 (gs://bucket/path/to/file)
            local_path: 로컬 저장 경로
            
        Returns:
            bool: 다운로드 성공 여부
        """
        try:
            # gs://bucket/path/to/file -> path/to/file
            blob_name = self._extract_blob_name(gs_path)
            blob = self.bucket.blob(blob_name)
            
            # 로컬 디렉토리 생성
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            blob.download_to_filename(local_path)
            logger.info(f"Downloaded {gs_path} to {local_path}")
            return True
            
        except NotFound:
            logger.error(f"File not found in GCS: {gs_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to download {gs_path}: {e}")
            return False
    
    def upload_file(self, local_path: str, gs_path: str) -> bool:
        """
        로컬 파일을 GCS에 업로드
        
        Args:
            local_path: 로컬 파일 경로
            gs_path: GCS 업로드 경로 (gs://bucket/path/to/file)
            
        Returns:
            bool: 업로드 성공 여부
        """
        try:
            # gs://bucket/path/to/file -> path/to/file
            blob_name = self._extract_blob_name(gs_path)
            blob = self.bucket.blob(blob_name)
            
            blob.upload_from_filename(local_path)
            logger.info(f"Uploaded {local_path} to {gs_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to {gs_path}: {e}")
            return False
    
    def _extract_blob_name(self, gs_path: str) -> str:
        """
        gs://bucket/path/to/file에서 path/to/file 추출
        
        Args:
            gs_path: GCS 경로
            
        Returns:
            str: blob 이름
        """
        if gs_path.startswith(f"gs://{settings.GCS_BUCKET}/"):
            return gs_path[len(f"gs://{settings.GCS_BUCKET}/"):]
        elif gs_path.startswith("gs://"):
            # 다른 버킷의 경우 전체 경로에서 버킷명 제거
            parts = gs_path.split("/", 3)
            if len(parts) >= 4:
                return parts[3]
        return gs_path


# 전역 GCS 클라이언트 인스턴스
gcs_client = GCSClient()
