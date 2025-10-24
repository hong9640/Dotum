#!/usr/bin/env python3
"""
GCS 연결 테스트 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.utils.gcs_client import gcs_client
from api.core.config import settings


def test_gcs_connection():
    """GCS 연결 테스트"""
    print("=== GCS 연결 테스트 시작 ===")
    
    try:
        # 1. 기본 연결 테스트
        print(f"1. GCS 클라이언트 초기화...")
        print(f"   - 프로젝트 ID: {settings.GCP_PROJECT_ID}")
        print(f"   - 버킷명: {settings.GCS_BUCKET}")
        print(f"   - 인증서 경로: {settings.GCS_CREDENTIAL_PATH}")
        
        # 2. 버킷 파일 목록 조회
        print(f"\n2. 버킷 파일 목록 조회...")
        files = gcs_client.list_files("")
        print(f"   - 전체 파일 수: {len(files)}")
        
        # 3. 모델 폴더 확인
        print(f"\n3. 모델 폴더 확인...")
        model_files = gcs_client.list_files("models/")
        print(f"   - 모델 파일 수: {len(model_files)}")
        
        if model_files:
            print("   - 모델 파일 목록:")
            for file in model_files[:10]:  # 처음 10개만 출력
                print(f"     * {file}")
        
        # 4. 필수 모델 파일 존재 확인
        print(f"\n4. 필수 모델 파일 존재 확인...")
        required_models = [
            "freevc-s.pth",
            "freevc-s.json", 
            "Wav2Lip_gan.pth"
        ]
        
        for model in required_models:
            model_path = gcs_client.get_model_path(model)
            exists = gcs_client.file_exists(model_path)
            status = "✓ 존재" if exists else "✗ 없음"
            print(f"   - {model}: {status}")
        
        # 5. 테스트 파일 업로드/다운로드
        print(f"\n5. 테스트 파일 업로드/다운로드...")
        test_content = "GCS connection test file"
        test_filename = "test_connection.txt"
        
        # 임시 파일 생성
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(test_content)
            tmp_path = tmp_file.name
        
        try:
            # 업로드
            test_gs_path = f"gs://{settings.GCS_BUCKET}/test/{test_filename}"
            upload_success = gcs_client.upload_file(tmp_path, test_gs_path)
            print(f"   - 파일 업로드: {'✓ 성공' if upload_success else '✗ 실패'}")
            
            if upload_success:
                # 다운로드
                download_path = tmp_path + "_downloaded"
                download_success = gcs_client.download_file(test_gs_path, download_path)
                print(f"   - 파일 다운로드: {'✓ 성공' if download_success else '✗ 실패'}")
                
                # 파일 내용 확인
                if download_success and os.path.exists(download_path):
                    with open(download_path, 'r') as f:
                        downloaded_content = f.read()
                    content_match = downloaded_content == test_content
                    print(f"   - 파일 내용 확인: {'✓ 일치' if content_match else '✗ 불일치'}")
                    
                    # 다운로드 파일 정리
                    os.unlink(download_path)
        
        finally:
            # 임시 파일 정리
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        print(f"\n=== GCS 연결 테스트 완료 ===")
        return True
        
    except Exception as e:
        print(f"\n❌ GCS 연결 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_gcs_connection()
    sys.exit(0 if success else 1)
