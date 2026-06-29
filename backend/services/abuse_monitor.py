"""轻量滥用监控：仅打 warning 日志，不拦截请求。内存 map TTL + max keys。"""
import time, threading
from services.log_sanitizer import safe_log

_WINDOW = 600      # 10 分钟
_MAX_KEYS = 5000
_lock = threading.Lock()

_analyze_by_ip: dict[str, dict] = {}       # ip → {count, users, coords, _ts}
_login_fail_by_ip: dict[str, dict] = {}    # ip → {count, _ts}
_consecutive_failures: dict[str, list] = {}  # service → [timestamps]


def _prune():
    now = time.time()
    # 过期清理
    for d in [_analyze_by_ip, _login_fail_by_ip]:
        stale = [k for k, v in d.items() if v.get("_ts", 0) < now - _WINDOW]
        for k in stale:
            del d[k]
    for d in [_consecutive_failures]:
        stale = [k for k, v in d.items() if not any(t > now - _WINDOW for t in v)]
        for k in stale:
            del d[k]
    # 容量上限
    for d in [_analyze_by_ip, _login_fail_by_ip, _consecutive_failures]:
        while len(d) > _MAX_KEYS:
            oldest = min(d, key=lambda k: (
                d[k].get("_ts", 0) if isinstance(d[k], dict)
                else min(d[k]) if isinstance(d[k], list) and d[k] else now + 1))
            del d[oldest]


def note_analyze(ip: str, user_id: int, lat: float, lng: float):
    with _lock:
        now = time.time()
        entry = _analyze_by_ip.get(ip, {"count": 0, "users": set(), "coords": set(), "_ts": now})
        entry["count"] += 1
        entry["users"].add(user_id)
        entry["coords"].add(f"{lat:.3f},{lng:.3f}")
        entry["_ts"] = now
        _analyze_by_ip[ip] = entry
        if entry["count"] >= 20 or len(entry["users"]) >= 5 or len(entry["coords"]) >= 15:
            safe_log("[ABUSE] high-frequency", ip=ip, analyze_count=entry["count"],
                     users=len(entry["users"]), coords=len(entry["coords"]))
        _prune()


def note_login_fail(ip: str):
    with _lock:
        now = time.time()
        entry = _login_fail_by_ip.get(ip, {"count": 0, "_ts": now})
        entry["count"] += 1
        entry["_ts"] = now
        _login_fail_by_ip[ip] = entry
        if entry["count"] >= 10:
            safe_log("[ABUSE] login-fail-spike", ip=ip, fail_count=entry["count"])
        _prune()


def note_service_fail(service: str):
    with _lock:
        now = time.time()
        ts = _consecutive_failures.get(service, [])
        ts = [t for t in ts if t > now - _WINDOW]
        ts.append(now)
        _consecutive_failures[service] = ts
        if len(ts) >= 10:
            safe_log("[ABUSE] service-fail-spike", service=service, fails_10m=len(ts))
        _prune()
