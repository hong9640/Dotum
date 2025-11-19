"""
JSON 직렬화를 위한 NaN/Inf 정규화 유틸리티

이 모듈은 JSON 직렬화 시 발생할 수 있는 NaN, Infinity, -Infinity 값을
안전하게 None으로 변환하는 함수를 제공합니다.
"""
import math
from collections.abc import Mapping, Sequence
from typing import Any


def sanitize_json(obj: Any) -> Any:
    """
    딕셔너리, 리스트, 또는 단일 값에서 NaN/Inf 값을 None으로 변환합니다.
    
    재귀적으로 딕셔너리와 리스트를 순회하며 모든 float 값을 검사합니다.
    넘파이 스칼라 타입도 자동으로 처리합니다.
    
    Args:
        obj: 정규화할 객체 (dict, list, 또는 단일 값)
    
    Returns:
        NaN/Inf가 None으로 변환된 객체
    
    Examples:
        >>> sanitize_json({"value": float("nan"), "nested": {"inf": float("inf")}})
        {'value': None, 'nested': {'inf': None}}
        
        >>> sanitize_json([1.0, float("nan"), 3.0])
        [1.0, None, 3.0]
    """
    # 넘파이 타입 확인 (선택적)
    try:
        import numpy as np
        np_types = (np.floating, np.integer)
    except ImportError:
        np_types = tuple()
    
    # 딕셔너리 처리
    if isinstance(obj, Mapping):
        return {k: sanitize_json(v) for k, v in obj.items()}
    
    # 리스트/튜플 처리 (문자열, 바이트 제외)
    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        return [sanitize_json(x) for x in obj]
    
    # 넘파이 스칼라 처리
    if np_types and isinstance(obj, np_types):
        obj = float(obj)
    
    # float 타입의 NaN/Inf 검사
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    
    return obj

