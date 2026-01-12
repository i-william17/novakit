from pydantic import EmailStr
from redis.asyncio import Redis
from config.config import settings
from app.core.security.ip_blocker import IPBlocker

redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)


class BruteForceService:

    @staticmethod
    async def key_user(username: str) -> str:
        return f"bf:user:{username.lower()}"

    @staticmethod
    async def key_ip(ip: str) -> str:
        return f"bf:ip:{ip}"

    # ------------------------------------------------------
    # Check if blocked
    # ------------------------------------------------------
    @staticmethod
    async def is_blocked(username: str | EmailStr, ip: str):
        user_ttl = await redis.ttl(f"bf:user:{username.lower()}:blocked")
        ip_ttl = await redis.ttl(f"bf:ip:{ip}:blocked")
        scatter = await IPBlocker.is_blocked(ip)

        return {
            "user_blocked": user_ttl > 0,
            "ip_blocked": ip_ttl > 0,
            "scatter_blocked": scatter,
        }

    # ------------------------------------------------------
    # Register failed authentication attempt
    # ------------------------------------------------------
    @staticmethod
    async def register_failure(username: str|EmailStr, ip: str):
        user_key = await BruteForceService.key_user(username)
        ip_key = await BruteForceService.key_ip(ip)

        # increment counters
        user_attempts = await redis.incr(user_key)
        ip_attempts = await redis.incr(ip_key)

        # set TTL window
        await redis.expire(user_key, settings.BRUTE_FORCE_WINDOW)
        await redis.expire(ip_key, settings.BRUTE_FORCE_WINDOW)

        # --------------------------------------------------
        # 🔥 NEW: IP Username Scatter Protection
        # --------------------------------------------------
        await IPBlocker.add_username_attempt(ip, username)

        distinct = await IPBlocker.distinct_username_count(ip)

        if distinct >= settings.IP_DISTINCT_USERNAME_THRESHOLD:
            # block the whole IP
            await IPBlocker.block_ip(ip, reason="many_distinct_usernames")
            return  # stop here, no need to proceed

        # --------------------------------------------------
        # Normal brute-force lockout
        # --------------------------------------------------
        if user_attempts >= settings.BRUTE_FORCE_ATTEMPTS:
            await redis.set(f"{user_key}:blocked", 1, ex=settings.BRUTE_FORCE_LOCKOUT)

        if ip_attempts >= settings.BRUTE_FORCE_ATTEMPTS:
            await redis.set(f"{ip_key}:blocked", 1, ex=settings.BRUTE_FORCE_LOCKOUT)

        print("FAILED LOGIN:", username, ip)

    # ------------------------------------------------------
    # Successful login → clear counters
    # ------------------------------------------------------
    @staticmethod
    async def reset(username: str|EmailStr, ip: str):
        await redis.delete(await BruteForceService.key_user(username))
        await redis.delete(await BruteForceService.key_ip(ip))
