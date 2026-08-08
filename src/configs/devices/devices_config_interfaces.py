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
