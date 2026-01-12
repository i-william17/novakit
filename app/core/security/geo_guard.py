import geoip2.database
from config.config import settings

class GeoGuard:
    reader = geoip2.database.Reader(settings.GEOIP_DB_PATH)

    @staticmethod
    async def get_country(ip: str) -> str | None:
        try:
            resp = GeoGuard.reader.country(ip)
            return resp.country.iso_code
        except:
            return None
