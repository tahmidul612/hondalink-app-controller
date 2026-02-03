import re
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_device_ip_address():
    """Get the IP address of the Waydroid Android device from the DHCP lease file."""
    # The IP address is queried from the DHCP lease file.
    lease_file = "/var/lib/misc/dnsmasq.waydroid0.leases"

    try:
        with open(lease_file) as f:
            return re.search(r"(\d{1,3}\.){3}\d{1,3}\s", f.read()).group().strip()
    except (Exception):
        pass

class Settings(BaseSettings):
    # Android device settings
    android_device_ip: str | None = (f"{get_device_ip_address()}:5555" or None)
    hondalink_package: str = "com.honda.hondalink.connect"
    hondalink_launcher_activity: str = (
        "com.honda.common.module.splash.view.activity.SplashActivity"
    )
    pin_code: str | None = None
    use_mock_driver: bool = False

    # Security settings
    require_authentication: bool = True
    api_keys: str = ""  # Comma-separated list of API keys
    allowed_ips: str = ""  # Comma-separated list of allowed IPs (empty = allow all)
    enable_rate_limiting: bool = True
    api_rate_limit: int = 30  # requests per minute for general API calls
    command_rate_limit: int = 10  # requests per minute for vehicle commands
    audit_log_file: Path = Path("logs/security_audit.jsonl")

    # JWT settings (for future expansion)
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # TLS/HTTPS settings (informational, handled by uvicorn)
    ssl_certfile: Path | None = None
    ssl_keyfile: Path | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
