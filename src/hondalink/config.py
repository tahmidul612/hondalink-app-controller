from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    android_device_ip: str | None = None  # None means connect to USB device or first available  # noqa: E501
    hondalink_package: str = (
        "com.honda.hondalink.connect"  # Guessing, user can override
    ) # Guessing, user can override
    pin_code: str | None = None
    use_mock_driver: bool = False

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
