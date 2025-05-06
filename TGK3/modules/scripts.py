import settings
from datetime import datetime, timedelta


def get_seconds_since_midnight():
    now = datetime.now(settings.TZ)
    midnight = datetime.combine(now.date(), datetime.min.time(), tzinfo=settings.TZ)
    seconds_since_midnight = (now - midnight).seconds
    return int(seconds_since_midnight)

