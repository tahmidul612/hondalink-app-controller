import json
import logging
import secrets
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class RateLimiter:
    """Simple in-memory rate limiter per IP address."""

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        """Check if request from identifier is allowed based on rate limit."""
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Remove old requests outside the window
        self.requests[identifier] = [
            req_time
            for req_time in self.requests[identifier]
            if req_time > window_start
        ]

        # Check if under limit
        if len(self.requests[identifier]) >= self.requests_per_minute:
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        now = time.time()
        window_start = now - 60
        recent = [req for req in self.requests[identifier] if req > window_start]
        return max(0, self.requests_per_minute - len(recent))


# Global rate limiter instances
command_rate_limiter = RateLimiter(requests_per_minute=settings.command_rate_limit)
api_rate_limiter = RateLimiter(requests_per_minute=settings.api_rate_limit)


class AuditLogger:
    """Audit logger for security events and vehicle commands."""

    def __init__(self, log_file: Path | None = None):
        self.log_file = log_file or Path("security_audit.jsonl")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_type: str,
        client_ip: str,
        details: dict | None = None,
        user: str | None = None,
    ):
        """Log a security or audit event."""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "client_ip": client_ip,
            "user": user or "unknown",
            "details": details or {},
        }

        # Log to file
        with self.log_file.open("a") as f:
            f.write(json.dumps(event) + "\n")

        # Also log to application logger
        logger.info(
            f"AUDIT: {event_type} from {client_ip} "
            f"(user: {user or 'unknown'}) - {details}"
        )


# Global audit logger
audit_logger = AuditLogger(log_file=settings.audit_log_file)


def verify_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    """Verify API key from request header."""
    if not settings.require_authentication:
        return "unauthenticated"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check against configured API keys
    valid_keys = [k.strip() for k in settings.api_keys.split(",") if k.strip()]

    if not valid_keys:
        logger.error("No API keys configured but authentication is required!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not properly configured",
        )

    # Use constant-time comparison to prevent timing attacks
    if not any(secrets.compare_digest(api_key, valid_key) for valid_key in valid_keys):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting proxy headers."""
    # Check X-Forwarded-For header (if behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP in chain
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection
    if request.client:
        return request.client.host

    return "unknown"


def verify_ip_whitelist(request: Request) -> str:
    """Verify client IP is in whitelist (if configured)."""
    client_ip = get_client_ip(request)

    # If no whitelist configured, allow all
    if not settings.allowed_ips:
        return client_ip

    allowed = [ip.strip() for ip in settings.allowed_ips.split(",") if ip.strip()]

    if client_ip not in allowed:
        audit_logger.log_event(
            event_type="ip_blocked",
            client_ip=client_ip,
            details={"reason": "IP not in whitelist"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP address not authorized",
        )

    return client_ip


def check_rate_limit(request: Request, limiter: RateLimiter, limit_type: str = "api"):
    """Check rate limit for client."""
    if not settings.enable_rate_limiting:
        return

    client_ip = get_client_ip(request)

    if not limiter.is_allowed(client_ip):
        remaining = limiter.get_remaining(client_ip)
        audit_logger.log_event(
            event_type="rate_limit_exceeded",
            client_ip=client_ip,
            details={"limit_type": limit_type, "remaining": remaining},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {limit_type}",
            headers={"Retry-After": "60"},
        )


def check_api_rate_limit(request: Request):
    """Check general API rate limit."""
    check_rate_limit(request, api_rate_limiter, "api")


def check_command_rate_limit(request: Request):
    """Check vehicle command rate limit (stricter)."""
    check_rate_limit(request, command_rate_limiter, "command")


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return pwd_context.hash(api_key)


def verify_hashed_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify a plain API key against its hash."""
    return pwd_context.verify(plain_key, hashed_key)


# JWT token functions (optional, for future expansion)
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(hours=24)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
