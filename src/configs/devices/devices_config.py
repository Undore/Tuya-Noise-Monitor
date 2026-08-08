from configs.devices.devices_config_interfaces import AvgThreshold, StrikeThreshold, DeviceAlertConfig, Device


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
