"""
공통 유틸리티 함수들
파일 경로 생성, 날짜 처리 등 공통 기능
"""
import os
import re
from datetime import datetime
from typing import Optional


def sanitize_username_for_path(username: str) -> str:
    """
    사용자명을 파일 경로에 안전한 형태로 변환
    
    Args:
        username: 사용자명
        
    Returns:
        str: 안전한 경로 문자열
    """
    # 특수문자를 안전한 문자로 변환
    safe_username = username.replace("@", "_at_").replace(".", "_dot_")
    
    # 추가 특수문자 제거
    safe_username = re.sub(r'[^\w\-_]', '_', safe_username)
    
    return safe_username


def generate_file_path(
    base_path: str,
    username: str,
    session_id: str,
    train_id: Optional[int] = None,
    result_id: Optional[int] = None,
    word_id: Optional[int] = None,
    sentence_id: Optional[int] = None
) -> str:
    """
    파일 경로 생성
    형식: videos/{username}/{session_id}/(type:train/result)_(train_id/result_id)_(type:word/sentence)_(word_id/sentence_id).mp4
    
    Args:
        base_path: 기본 경로 (예: "videos")
        username: 사용자명
        session_id: 세션 ID (필수)
        train_id: 연습 ID (단어 연습용)
        result_id: 결과 ID (문장 연습용)
        word_id: 단어 ID
        sentence_id: 문장 ID
        
    Returns:
        str: 생성된 파일 경로
        
    Raises:
        ValueError: train_id+word_id 또는 result_id+sentence_id가 제공되지 않은 경우
    """
    # 안전한 사용자명 변환
    safe_username = sanitize_username_for_path(username)
    
    # 파일명 생성
    if train_id is not None and word_id is not None:
        filename = f"train_{train_id}_word_{word_id}.mp4"
    elif result_id is not None and sentence_id is not None:
        filename = f"result_{result_id}_sentence_{sentence_id}.mp4"
    else:
        raise ValueError("train_id+word_id 또는 result_id+sentence_id가 필요합니다")
    
    # 경로 구성: videos/{username}/{session_id}/{filename}
    return f"{base_path}/{safe_username}/{session_id}/{filename}"


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    고유한 파일명 생성
    
    Args:
        original_filename: 원본 파일명
        prefix: 파일명 접두사
        
    Returns:
        str: 고유한 파일명
    """
    # 파일명과 확장자 분리
    name, ext = os.path.splitext(original_filename)
    
    # 타임스탬프 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # UUID 생성 (짧은 버전)
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    # 최종 파일명 구성
    if prefix:
        new_name = f"{prefix}_{timestamp}_{unique_id}_{name}{ext}"
    else:
        new_name = f"{timestamp}_{unique_id}_{name}{ext}"
    
    return new_name


def validate_video_file(filename: str, content_type: str) -> tuple[bool, str]:
    """
    동영상 파일 유효성 검사
    
    Args:
        filename: 파일명
        content_type: MIME 타입
        
    Returns:
        tuple[bool, str]: (유효성, 오류 메시지)
    """
    # 지원하는 동영상 확장자
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
    
    # 지원하는 MIME 타입
    video_mime_types = {
        'video/mp4', 'video/avi', 'video/quicktime', 
        'video/x-msvideo', 'video/webm', 'video/x-flv'
    }
    
    # 파일 확장자 검사
    _, ext = os.path.splitext(filename.lower())
    if ext not in video_extensions:
        return False, f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(video_extensions)}"
    
    # MIME 타입 검사
    if content_type and not content_type.startswith('video/'):
        return False, "동영상 파일만 업로드 가능합니다."
    
    return True, ""


def format_file_size(size_bytes: int) -> str:
    """
    파일 크기를 읽기 쉬운 형태로 변환
    
    Args:
        size_bytes: 바이트 단위 크기
        
    Returns:
        str: 포맷된 크기 문자열
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_date_from_path(file_path: str) -> Optional[str]:
    """
    파일 경로에서 날짜 추출
    
    Args:
        file_path: 파일 경로 (예: "videos/user_at_example_dot_com/2024-01-15/video.mp4")
        
    Returns:
        str: 날짜 문자열 (YYYY-MM-DD) 또는 None
    """
    # 경로에서 날짜 패턴 찾기 (YYYY-MM-DD)
    date_pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(date_pattern, file_path)
    
    if match:
        return match.group(1)
    
    return None


def is_valid_date_string(date_str: str) -> bool:
    """
    날짜 문자열 유효성 검사
    
    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD 형식)
        
    Returns:
        bool: 유효성 여부
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
