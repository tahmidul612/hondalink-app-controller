# Security Hardening Guide

This document describes the security features implemented in the HondaLink Controller and how to configure them properly.

## Security Layers

The HondaLink Controller implements multiple security layers to prevent unauthorized access:

1. **API Key Authentication** - Require valid API keys for all requests
2. **IP Whitelist** - Restrict access to specific IP addresses
3. **Rate Limiting** - Prevent abuse through request throttling
4. **Audit Logging** - Track all vehicle commands and security events
5. **HTTPS/TLS Support** - Encrypt traffic in transit

## Quick Start - Secure Configuration

### 1. Generate API Keys

```bash
# Generate a secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to your `.env` file:
```ini
REQUIRE_AUTHENTICATION=true
API_KEYS=your-generated-key-here
```

### 2. Configure IP Whitelist (Recommended)

Restrict access to your home network or specific devices:

```ini
# Allow only specific IPs (comma-separated)
ALLOWED_IPS=192.168.1.100,192.168.1.50

# Or allow all (not recommended for production)
ALLOWED_IPS=
```

### 3. Enable Rate Limiting

```ini
ENABLE_RATE_LIMITING=true
API_RATE_LIMIT=30          # General API calls per minute
COMMAND_RATE_LIMIT=10      # Vehicle commands per minute (stricter)
```

### 4. Set Up HTTPS/TLS

Generate self-signed certificate (for home use):

```bash
# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=localhost"
```

Update `.env`:
```ini
SSL_CERTFILE=cert.pem
SSL_KEYFILE=key.pem
```

Run with HTTPS:
```bash
uv run uvicorn src.hondalink.main:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

For production, use proper certificates from Let's Encrypt or a trusted CA.

## Configuration Reference

### Environment Variables

All security settings are configured via environment variables in `.env`:

```ini
# Authentication
REQUIRE_AUTHENTICATION=true
API_KEYS=key1,key2,key3  # Comma-separated

# IP Whitelist
ALLOWED_IPS=192.168.1.0/24,10.0.0.5  # CIDR notation or specific IPs

# Rate Limiting
ENABLE_RATE_LIMITING=true
API_RATE_LIMIT=30           # Requests per minute for /status, /debug
COMMAND_RATE_LIMIT=10       # Requests per minute for /action/*

# Audit Logging
AUDIT_LOG_FILE=logs/security_audit.jsonl

# JWT (for future token-based auth)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# TLS/HTTPS
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem
```

## Using the API with Authentication

### With API Key Header

```bash
# Store your API key
export API_KEY="your-api-key-here"

# Check status
curl -H "X-API-Key: $API_KEY" http://localhost:8000/status

# Execute command
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/action/lock
```

### Without Authentication (Testing Only)

```ini
# .env
REQUIRE_AUTHENTICATION=false
```

**WARNING**: Only use this for local testing. Never expose an unauthenticated server to the internet.

## Audit Logging

All security events and vehicle commands are logged to `logs/security_audit.jsonl`:

```json
{"timestamp": "2026-02-03T19:30:00Z", "event_type": "vehicle_command", "client_ip": "192.168.1.50", "user": "api-key-123", "details": {"command": "lock"}}
{"timestamp": "2026-02-03T19:30:01Z", "event_type": "vehicle_command_success", "client_ip": "192.168.1.50", "user": "api-key-123", "details": {"command": "lock"}}
```

Events logged:
- `vehicle_command` - Command initiated
- `vehicle_command_success` - Command succeeded
- `vehicle_command_failed` - Command failed
- `status_check` - Status endpoint accessed
- `debug_hierarchy_access` - Debug endpoint accessed
- `ip_blocked` - IP not in whitelist
- `rate_limit_exceeded` - Rate limit hit

### Viewing Audit Logs

```bash
# Tail live logs
tail -f logs/security_audit.jsonl

# Search for specific events
grep "vehicle_command" logs/security_audit.jsonl | jq .

# Find failed attempts
grep "failed\|blocked\|exceeded" logs/security_audit.jsonl | jq .
```

## Rate Limiting

Two separate rate limiters protect different endpoint types:

### API Rate Limiter
- Applies to: `/status`, `/debug/hierarchy`
- Default: 30 requests/minute per IP
- Prevents excessive polling

### Command Rate Limiter
- Applies to: `/action/*` (lock, unlock, start, stop)
- Default: 10 requests/minute per IP
- Prevents rapid-fire vehicle commands

When rate limit is exceeded:
- HTTP 429 (Too Many Requests)
- `Retry-After: 60` header
- Audit log entry created

## Network Security

### Reverse Proxy Setup (Recommended)

Use nginx or Caddy as a reverse proxy for additional security:

**nginx example:**
```nginx
server {
    listen 443 ssl http2;
    server_name car.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Firewall Rules

Restrict access at the firewall level:

```bash
# UFW (Ubuntu)
sudo ufw allow from 192.168.1.0/24 to any port 8000

# iptables
sudo iptables -A INPUT -p tcp --dport 8000 -s 192.168.1.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP
```

## Security Best Practices

### DO:
- ✅ Use strong, randomly generated API keys (32+ characters)
- ✅ Enable IP whitelist for home network
- ✅ Use HTTPS/TLS for all production deployments
- ✅ Monitor audit logs regularly
- ✅ Keep API keys secret (never commit to git)
- ✅ Use environment variables, not hardcoded values
- ✅ Run behind a reverse proxy in production
- ✅ Keep dependencies updated

### DON'T:
- ❌ Expose to public internet without authentication
- ❌ Use weak or guessable API keys
- ❌ Disable rate limiting
- ❌ Ignore audit log warnings
- ❌ Share API keys between multiple users
- ❌ Store API keys in application code
- ❌ Use self-signed certs in production (get proper CA certs)

## Testing Security Features

### Test API Key Authentication

```bash
# Should fail (no key)
curl http://localhost:8000/status
# Response: 401 Unauthorized

# Should succeed
curl -H "X-API-Key: your-key" http://localhost:8000/status
# Response: 200 OK
```

### Test Rate Limiting

```bash
# Rapid fire requests (should hit rate limit)
for i in {1..35}; do
  curl -H "X-API-Key: your-key" http://localhost:8000/status
done
# After 30 requests: 429 Too Many Requests
```

### Test IP Whitelist

```bash
# From allowed IP: succeeds
# From blocked IP: 403 Forbidden
```

## Troubleshooting

### "Missing API key" error
- Ensure `X-API-Key` header is set
- Check API key matches value in `.env`
- Try: `REQUIRE_AUTHENTICATION=false` for testing

### "IP address not authorized"
- Add your IP to `ALLOWED_IPS` in `.env`
- Check actual IP with: `curl ipinfo.io/ip`
- Disable whitelist: `ALLOWED_IPS=` (empty)

### "Rate limit exceeded"
- Wait 60 seconds before retrying
- Increase limits in `.env` if legitimate use
- Check audit logs for abuse

### HTTPS certificate errors
- For self-signed certs, use `curl -k` to skip verification
- For production, use proper CA-signed certificates
- Check cert/key file paths in `.env`

## Generating Multiple API Keys

```bash
# Generate and add multiple keys
python3 << 'EOF'
import secrets
keys = [secrets.token_urlsafe(32) for _ in range(3)]
print("API_KEYS=" + ",".join(keys))
EOF
```

Add output to `.env`, then distribute keys to different users/devices.

## Rotating API Keys

1. Generate new key(s)
2. Add to existing `API_KEYS` (comma-separated)
3. Update clients with new keys
4. Remove old keys from `API_KEYS` after transition period
5. Monitor audit logs for old key usage

## Emergency Lockdown

If you suspect unauthorized access:

1. **Stop the server immediately**
   ```bash
   pkill -f uvicorn
   ```

2. **Rotate all API keys**
   ```bash
   # Generate new keys
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   # Update .env with new keys only
   ```

3. **Review audit logs**
   ```bash
   grep -E "blocked|failed|exceeded" logs/security_audit.jsonl | jq .
   ```

4. **Enable IP whitelist**
   ```ini
   ALLOWED_IPS=only-your-trusted-ip
   ```

5. **Restart with new configuration**

## Contact & Support

For security issues, please:
1. Do NOT open public GitHub issues
2. Contact maintainer directly
3. Include audit log excerpts (redact sensitive info)
