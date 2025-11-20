from datetime import datetime
from zoneinfo import ZoneInfo


def now_kst() -> datetime:
    """KST 기준 현재 시각"""
    return datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None)

def today_kst() -> datetime:
    """KST 기준 월-일 00:00:00"""
    kst = ZoneInfo("Asia/Seoul")
    now_kst = datetime.now(kst)
    today_midnight_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    return today_midnight_kst.replace(tzinfo=None)
