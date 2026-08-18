from configs.devices.devices_config_interfaces import AvgThreshold, StrikeThreshold, DeviceAlertConfig, Device


class DevicesConfig:
    """
    WARNING: Max 20 devices supported
    """

    devices = [
        Device(
            tuya_device_id="bf549fb518a81875f5dp7z",
            device_name="Device 1",

            alerts=[
                DeviceAlertConfig(
                    alert_name="Name",
                    active_hours=list(
                        range(8, 21)
                    ),

                    threshold_window_minutes=10,
                    threshold_mode=AvgThreshold(
                        threshold_dB=65
                    )
                ),
                DeviceAlertConfig(
                    alert_name="Name",
                    active_hours=[21],

                    threshold_window_minutes=10,
                    threshold_mode=AvgThreshold(
                        threshold_dB=55
                    )
                ),
                DeviceAlertConfig(
                    alert_name="Name",
                    active_hours=[22, 23,
                                  *range(0, 8)],

                    threshold_window_minutes=10,
                    threshold_mode=AvgThreshold(
                        threshold_dB=50
                    )
                ),

                DeviceAlertConfig(
                    alert_name="Name",
                    active_hours=list(
                        range(8, 21)
                    ),

                    threshold_window_minutes=10,
                    threshold_mode=StrikeThreshold(
                        threshold_dB=65,
                        threshold_strikes=10
                    )
                ),

                DeviceAlertConfig(
                    alert_name="Name",
                    active_hours=list(
                        range(21, 23)
                    ),

                    threshold_window_minutes=10,
                    threshold_mode=StrikeThreshold(
                        threshold_dB=65,
                        threshold_strikes=5
                    )
                ),

                DeviceAlertConfig(
                    alert_name="Name",
                    active_hours=[23, *range(0, 8)],

                    threshold_window_minutes=10,
                    threshold_mode=StrikeThreshold(
                        threshold_dB=65,
                        threshold_strikes=1
                    )
                )
            ]
        )
    ]
