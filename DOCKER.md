# Docker Deployment Guide

## Quick Start

### 1. Build the Image

```bash
docker compose build
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run the Container

```bash
docker compose up -d
```

### 4. Check Logs

```bash
docker compose logs -f
```

### 5. Access the API

```bash
curl http://localhost:8000/health
```

## Configuration

### Network Modes

**Host Mode (Default)**
- Container uses host network directly
- Required for local USB ADB devices
- Android device discovery via USB

**Bridge Mode**
- Isolated network
- Use when Android device is remote (via IP)
- Better security isolation

To switch to bridge mode:
```yaml
# In docker-compose.yml, change:
network_mode: host
# To:
# network_mode: bridge
# Then uncomment ports section
```

### USB Device Access

For USB-connected Android devices, uncomment in docker-compose.yml:

```yaml
devices:
  - /dev/bus/usb:/dev/bus/usb
```

### Resource Limits

Current settings:
- CPU: 1.0 core max, 0.25 core reserved
- Memory: 512MB max, 128MB reserved

Adjust in docker-compose.yml based on your needs:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G
```

## Optimization Features

### Multi-Stage Build
- Builder stage: Installs dependencies
- Runtime stage: Minimal production image
- Result: ~200MB final image vs ~1GB+ standard Python

### Resource Efficiency
- Single worker process (stateful Android connection)
- No access logging (reduces I/O)
- Alpine-style slim base image
- Minimal runtime dependencies

### Security Hardening
- Non-root user execution
- Dropped all capabilities except NET_BIND_SERVICE
- no-new-privileges security option
- Minimal attack surface

## Management Commands

### Start Service
```bash
docker compose up -d
```

### Stop Service
```bash
docker compose down
```

### Restart Service
```bash
docker compose restart
```

### View Logs
```bash
docker compose logs -f
```

### Update Container
```bash
docker compose pull
docker compose up -d
```

### Shell Access
```bash
docker compose exec hondalink-controller /bin/bash
```

### Check Health
```bash
docker compose ps
```

## Troubleshooting

### ADB Connection Issues

Check ADB devices from container:
```bash
docker compose exec hondalink-controller adb devices
```

Connect to device:
```bash
docker compose exec hondalink-controller adb connect <IP>:5555
```

### Permission Errors

Ensure logs directory exists and is writable:
```bash
mkdir -p logs
chmod 777 logs
```

### Container Won't Start

Check logs for errors:
```bash
docker compose logs
```

Verify .env configuration:
```bash
docker compose config
```

### High Memory Usage

Reduce resource limits in docker-compose.yml:
```yaml
memory: 256M
```

Or disable rate limiting to reduce memory overhead:
```bash
ENABLE_RATE_LIMITING=false
```

## Production Deployment

### With HTTPS/TLS

1. Generate certificates:
```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365
```

2. Mount certificates:
```yaml
volumes:
  - ./cert.pem:/app/cert.pem:ro
  - ./key.pem:/app/key.pem:ro
```

3. Update CMD in Dockerfile:
```dockerfile
CMD ["uvicorn", "src.hondalink.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8443", \
     "--ssl-certfile", "/app/cert.pem", \
     "--ssl-keyfile", "/app/key.pem"]
```

### Behind Reverse Proxy

Use nginx or Traefik for:
- SSL termination
- Load balancing
- Advanced routing

Example nginx config:
```nginx
server {
    listen 443 ssl;
    server_name hondalink.yourdomain.com;
    
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Monitoring

### Health Check Status
```bash
docker inspect hondalink-controller | jq '.[0].State.Health'
```

### Resource Usage
```bash
docker stats hondalink-controller
```

### Audit Logs
```bash
tail -f logs/security_audit.jsonl
```

## Backup & Restore

### Backup Audit Logs
```bash
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### Restore Configuration
```bash
docker compose down
# Restore .env and logs/
docker compose up -d
```
