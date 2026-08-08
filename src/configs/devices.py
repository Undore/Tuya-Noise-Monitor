from pydantic import field_validator

from interfaces.base_model_v2 import BaseModelV2


class AvgThreshold(BaseModelV2):
    threshold_dB: int

    @field_validator("threshold_dB")
    @classmethod
    def validate_threshold(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Threshold must be greater than 0")

        return value


class StrikeThreshold(BaseModelV2):
    threshold_dB: int
    threshold_strikes: int

    @field_validator("threshold_dB")
    @classmethod
    def validate_threshold(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Threshold must be greater than 0")

        return value

    @field_validator("threshold_strikes")
    @classmethod
    def validate_strikes_allowed(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Strikes allowed must be greater than 0")

        return value


class DeviceAlertConfig(BaseModelV2):
    alert_name: str
    active_hours: list[int]

    threshold_mode: AvgThreshold | StrikeThreshold

    threshold_window_minutes: int

    @field_validator("active_hours")
    @classmethod
    def validate_active_hours(cls, active_hours: list[int]) -> list[int]:
        if not all(0 <= hour <= 23 for hour in active_hours):
            raise ValueError(
                "Invalid active hours. "
                "Accepted values from 0 to 23 inclusive."
            )

        return active_hours

    @field_validator("threshold_window_minutes")
    @classmethod
    def validate_window(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Window must be greater than 0")

        return value


class Device(BaseModelV2):
    tuya_device_id: str
    device_name: str

    alerts: list[DeviceAlertConfig]

    def __str__(self) -> str:
        return f"{self.device_name} ({self.tuya_device_id})"

    def __repr__(self) -> str:
        return f"<Device id={self.tuya_device_id} name={self.device_name}>"

class DevicesConfig:
    devices = [
        Device(
            tuya_device_id="bf549fb518a81875f5dp7z",
            device_name="Датчик 1",

            alerts=[
                DeviceAlertConfig(
                    alert_name="8-21ч Среднее за 10 минут > 75дБ",
                    active_hours=list(
                        range(8, 21)
                    ),

                    threshold_window_minutes=10,
                    threshold_mode=AvgThreshold(
                        threshold_dB=75
                    )
                ),
                DeviceAlertConfig(
                    alert_name="21-22ч Среднее за 10 минут > 70дБ",
                    active_hours=[21],

                    threshold_window_minutes=10,
                    threshold_mode=AvgThreshold(
                        threshold_dB=70
                    )
                ),
                DeviceAlertConfig(
                    alert_name="22-8ч Среднее за 10 минут > 60дБ",
                    active_hours=[22, 23,
                                  *range(0, 8)],

                    threshold_window_minutes=10,
                    threshold_mode=AvgThreshold(
                        threshold_dB=60
                    )
                ),

                DeviceAlertConfig(
                    alert_name="8-21ч 10 Страйков > 85дБ за 10 минут",
                    active_hours=list(
                        range(8, 21)
                    ),

                    threshold_window_minutes=10,
                    threshold_mode=StrikeThreshold(
                        threshold_dB=85,
                        threshold_strikes=10
                    )
                ),

                DeviceAlertConfig(
                    alert_name="21-23ч 5 Страйков > 85дБ за 10 минут",
                    active_hours=list(
                        range(21, 23)
                    ),

                    threshold_window_minutes=10,
                    threshold_mode=StrikeThreshold(
                        threshold_dB=85,
                        threshold_strikes=5
                    )
                ),

                DeviceAlertConfig(
                    alert_name="23-8 1 Страйк > 85дБ за 10 минут",
                    active_hours=[23, *range(0, 8)],

                    threshold_window_minutes=10,
                    threshold_mode=StrikeThreshold(
                        threshold_dB=85,
                        threshold_strikes=1
                    )
                )
            ]
        )
    ]
