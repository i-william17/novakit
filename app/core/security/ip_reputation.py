import aiohttp
from config.config import settings

class IPReputation:

    @staticmethod
    async def is_bad(ip: str):
        url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}"

        headers = {"Key": settings.ABUSEIPDB_KEY}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                score = data["data"]["abuseConfidenceScore"]
                return score >= settings.IP_REPUTATION_THRESHOLD
