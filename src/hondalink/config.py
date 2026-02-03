from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    android_device_ip: str | None = None  # None means connect to USB device or first available
    hondalink_package: str = "com.honda.auto" # Guessing, user can override
    pin_code: str | None = None
    use_mock_driver: bool = False

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
