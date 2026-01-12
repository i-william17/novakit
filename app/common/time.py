from datetime import datetime, timezone

from pydantic import field_serializer


def epoch_to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

def epoch_to_datetime(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)

@field_serializer("created_at")
def serialize_created_at(self, v: int):
    return datetime.fromtimestamp(v, tz=timezone.utc)
