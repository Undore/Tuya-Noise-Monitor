from datetime import timedelta


class TuyaConfig:
    class quotas:
        api_call_cooldown: timedelta = timedelta(minutes=1, seconds=30)