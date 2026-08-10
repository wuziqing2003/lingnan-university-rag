from __future__ import annotations
from datetime import datetime,timedelta,timezone
from fastapi import Request,HTTPException

from app.core.config import DEMO_IP_HOURLY_LIMIT,DEMO_IP_DAILY_LIMIT,DEMO_GLOBAL_DAILY_LIMIT
from app.core.redis_client import redis_client


def get_client_ip(request:Request)->str:
    if request.client and request.client.host:
        return request.client.host

    return "unknown"

def _seconds_until_next_hour(now:datetime)->int:
    nxt = now.replace(minute=0,second=0,microsecond=0) + timedelta(hours=1)
    return max(int((nxt - now).total_seconds()),1)

def _seconds_until_next_day(now:datetime)->int:
    nxt = now.replace(hour=0,minute=0,second=0,microsecond=0) + timedelta(days=1)
    return max(int((nxt - now).total_seconds()),1)

def _incr_with_expire(key:str,ttl_seconds:int)->int:
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key,ttl_seconds)
    return int(count)

def check_demo_rate_limit(ip:str)->None:
    now = datetime.now(timezone.utc)
    hour_tag = now.strftime("%Y%m%d%H")
    day_tag = now.strftime("%Y%m%d")

    global_key = f"demo:global:day:{day_tag}"
    ip_hour_key = f"demo:ip:{ip}:hour:{hour_tag}"
    ip_day_key = f"demo:ip:{ip}:day:{day_tag}"


    global_count = _incr_with_expire(global_key, _seconds_until_next_day(now))
    if global_count > DEMO_GLOBAL_DAILY_LIMIT:
        raise HTTPException(status_code=429,detail="今日全站演示额度已用完，请明天再试。")

    hour_count = _incr_with_expire(ip_hour_key, _seconds_until_next_hour(now))
    if hour_count > DEMO_IP_HOURLY_LIMIT:
        raise HTTPException(status_code=429,detail="当前网络请求过于频繁，请稍后再试。")

    day_count = _incr_with_expire(ip_day_key, _seconds_until_next_day(now))
    if day_count > DEMO_IP_DAILY_LIMIT:
        raise HTTPException(status_code=429,detail="当前IP今日演示额度已用完，请明天再试。")
        

   