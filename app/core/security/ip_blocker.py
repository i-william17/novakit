from redis.asyncio import Redis
from config.config import settings

redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)


class IPBlocker:
    """
    High-level helpers for IP-level detection and blocking.
    """

    @staticmethod
    def key_ip_userset(ip: str) -> str:
        return f"bf:ip:userset:{ip}"

    @staticmethod
    def key_ip_blocked(ip: str) -> str:
        return f"bf:ip:blocked:{ip}"

    @staticmethod
    def key_ip_counter(ip: str) -> str:
        return f"bf:ip:{ip}"

    @staticmethod
    async def add_username_attempt(ip: str, username: str):
        """
        Record that `ip` attempted `username`. Use a SET so we count distinct usernames.
        Also set TTL for the set to the distinct window.
        """
        ks = IPBlocker.key_ip_userset(ip)
        await redis.sadd(ks, username.lower())
        # ensure TTL exists (reset TTL on each add to act like sliding window)
        await redis.expire(ks, int(getattr(settings, "IP_DISTINCT_WINDOW", 300)))

    @staticmethod
    async def distinct_username_count(ip: str) -> int:
        ks = IPBlocker.key_ip_userset(ip)
        return await redis.scard(ks) or 0

    @staticmethod
    async def block_ip(ip: str, reason: str = "abuse"):
        key = IPBlocker.key_ip_blocked(ip)
        await redis.set(key, reason, ex=int(getattr(settings, "IP_BLOCK_LOCKOUT", 3600)))

    @staticmethod
    async def is_blocked(ip: str) -> bool:
        key = IPBlocker.key_ip_blocked(ip)
        ttl = await redis.ttl(key)
        return ttl > 0

    @staticmethod
    async def unblock_ip(ip: str):
        await redis.delete(IPBlocker.key_ip_blocked(ip))
        await redis.delete(IPBlocker.key_ip_userset(ip))
        await redis.delete(IPBlocker.key_ip_counter(ip))
