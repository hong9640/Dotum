#!/usr/bin/env python3
"""
GCS 파일 경로 테스트 스크립트 (간단 버전)
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.utils.gcs_client import gcs_client
from api.core.config import settings


def test_gcs_file_access():
    """GCS 파일 접근 테스트"""
    print("=== GCS 파일 접근 테스트 시작 ===")
    
    try:
        # 1. 설정 정보 출력
        print(f"1. 설정 정보 확인...")
        print(f"   - 프로젝트 ID: {settings.GCP_PROJECT_ID}")
        print(f"   - 버킷명: {settings.GCS_BUCKET}")
        print(f"   - 인증서 경로: {settings.GCS_CREDENTIAL_PATH}")
        print(f"   - 인증서 파일 존재: {os.path.exists(settings.GCS_CREDENTIAL_PATH)}")
        
        # 2. 특정 파일 경로 테스트
        test_file_path = "gs://brain-deck/images/face.jpg"
        print(f"\n2. 특정 파일 접근 테스트...")
        print(f"   - 테스트 파일 경로: {test_file_path}")
        
        # 파일 존재 여부 확인
        file_exists = gcs_client.file_exists(test_file_path)
        print(f"   - 파일 존재 여부: {'✓ 존재' if file_exists else '✗ 없음'}")
        
        # 3. 버킷 루트 디렉토리 파일 목록 조회
        print(f"\n3. 버킷 루트 디렉토리 파일 목록...")
        root_files = gcs_client.list_files("")
        print(f"   - 루트 디렉토리 파일 수: {len(root_files)}")
        
        if root_files:
            print("   - 파일 목록:")
            for file in root_files[:20]:  # 처음 20개만 출력
                print(f"     * {file}")
        
        # 4. images 디렉토리 파일 목록 조회
        print(f"\n4. images 디렉토리 파일 목록...")
        images_files = gcs_client.list_files("images/")
        print(f"   - images 디렉토리 파일 수: {len(images_files)}")
        
        if images_files:
            print("   - 파일 목록:")
            for file in images_files:
                print(f"     * {file}")
        
        # 5. models 디렉토리 파일 목록 조회
        print(f"\n5. models 디렉토리 파일 목록...")
        models_files = gcs_client.list_files("models/")
        print(f"   - models 디렉토리 파일 수: {len(models_files)}")
        
        if models_files:
            print("   - 파일 목록:")
            for file in models_files:
                print(f"     * {file}")
        
        # 6. 특정 파일 다운로드 테스트 (파일이 존재하는 경우)
        if file_exists:
            print(f"\n6. 파일 다운로드 테스트...")
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                download_success = gcs_client.download_file(test_file_path, tmp_path)
                print(f"   - 파일 다운로드: {'✓ 성공' if download_success else '✗ 실패'}")
                
                if download_success and os.path.exists(tmp_path):
                    file_size = os.path.getsize(tmp_path)
                    print(f"   - 다운로드된 파일 크기: {file_size} bytes")
                    
                    # 파일 정리
                    os.unlink(tmp_path)
                    
            except Exception as e:
                print(f"   - 다운로드 중 오류: {e}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            print(f"\n6. 파일 다운로드 테스트 건너뜀 (파일이 존재하지 않음)")
        
        print(f"\n=== GCS 파일 접근 테스트 완료 ===")
        return True
        
    except Exception as e:
        print(f"\n❌ GCS 파일 접근 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_gcs_file_access()
    sys.exit(0 if success else 1)
