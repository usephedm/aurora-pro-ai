# Aurora Pro - Production Deployment Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Service Setup](#service-setup)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Performance Tuning](#performance-tuning)
10. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS:** Linux (Ubuntu 22.04 LTS, Debian 12, Kali Linux)
- **CPU:** 8 cores (Intel i7 or AMD Ryzen 7)
- **RAM:** 16 GB
- **Disk:** 100 GB SSD
- **Network:** 100 Mbps
- **Python:** 3.11+

### Recommended Requirements
- **OS:** Ubuntu 22.04 LTS or Kali Linux (latest)
- **CPU:** 32 cores (Intel i9-13900HX or AMD Ryzen 9)
- **RAM:** 64 GB
- **Disk:** 500 GB NVMe SSD
- **Network:** 1 Gbps
- **GPU:** NVIDIA RTX 4090 (24GB VRAM) - optional but recommended
- **Python:** 3.13+

### Software Dependencies
```bash
# Core
python3.11+
pip 24.0+
git

# System libraries
libxcb1
libxcb-xtest0
libx11-6
scrot or maim
tesseract-ocr

# Optional
ollama (for local inference)
redis-server (for distributed cache)
docker (for containerization)
```

---

## Pre-Deployment Checklist

### 1. Infrastructure
- [ ] Server provisioned with required specs
- [ ] Static IP address assigned
- [ ] Domain name configured (if needed)
- [ ] SSL certificate obtained
- [ ] Firewall rules configured
- [ ] Load balancer set up (if multi-server)

### 2. API Keys
- [ ] Anthropic API key (Claude)
- [ ] OpenAI API key (GPT-4)
- [ ] Google API key (Gemini)
- [ ] 2Captcha API key (optional)
- [ ] Any other service API keys

### 3. Access Control
- [ ] SSH key-based authentication enabled
- [ ] Root access disabled
- [ ] Sudo user created
- [ ] VPN/bastion host configured
- [ ] IP whitelist established

### 4. Monitoring
- [ ] Monitoring solution chosen (Prometheus, Datadog, etc.)
- [ ] Alerting configured
- [ ] Log aggregation set up
- [ ] Uptime monitoring enabled

---

## Installation

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3.11 python3.11-venv python3-pip \
    git curl wget \
    libxcb1 libxcb-xtest0 libx11-6 \
    scrot tesseract-ocr \
    redis-server \
    nginx \
    supervisor

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Ollama (for local inference)
curl https://ollama.ai/install.sh | sh
```

### Step 2: Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/aurora-pro
sudo chown $USER:$USER /opt/aurora-pro

# Clone repository
cd /opt/aurora-pro
git clone https://github.com/your-org/aurora-pro.git .

# Or copy files if already downloaded
# cp -r /root/aurora_pro/* /opt/aurora-pro/
```

### Step 3: Python Environment

```bash
cd /opt/aurora-pro

# Create virtual environment
python3.11 -m venv venv

# Activate environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import streamlit; print('Streamlit:', streamlit.__version__)"
```

### Step 4: Directory Structure

```bash
# Create necessary directories
mkdir -p /opt/aurora-pro/{logs,cache,config,plugins,data}
mkdir -p /opt/aurora-pro/logs/{screenshots,browser_screenshots,workflows,reasoning_contexts,tasks}

# Set permissions
chmod 755 /opt/aurora-pro
chmod 777 /opt/aurora-pro/logs
chmod 777 /opt/aurora-pro/cache
```

---

## Configuration

### Step 1: Environment Variables

Create `/opt/aurora-pro/.env`:

```bash
cat > /opt/aurora-pro/.env << 'EOF'
# Aurora Pro Environment Configuration

# API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY=your-google-api-key
TWOCAPTCHA_API_KEY=your-2captcha-key

# System Configuration
AURORA_ENV=production
AURORA_LOG_LEVEL=INFO
AURORA_API_PORT=8000
AURORA_API_HOST=0.0.0.0
AURORA_API_WORKERS=4

# Database
DATABASE_PATH=/opt/aurora-pro/data/aurora.db

# Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Multicore
MULTICORE_WORKERS=30

# Memory Limits
CACHE_MEMORY_MB=2048
MAX_MEMORY_GB=32

# Security
ALLOWED_ORIGINS=https://yourdomain.com,http://localhost:8501
API_AUTH_TOKEN=your-secure-token-here

# Monitoring
PROMETHEUS_PORT=9090
METRICS_ENABLED=true

# Optional Services
OLLAMA_URL=http://localhost:11434
PROXY_ENABLED=false

EOF

# Secure the file
chmod 600 /opt/aurora-pro/.env
```

### Step 2: Application Configuration

Create `/opt/aurora-pro/config/production.yaml`:

```yaml
# Aurora Pro Production Configuration

system:
  name: "Aurora Pro"
  version: "2.0.0"
  environment: "production"
  debug: false

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: false
  log_level: "info"
  cors_origins:
    - "https://yourdomain.com"
    - "http://localhost:8501"

agents:
  multicore:
    workers: 30
    timeout: 300
  cache:
    memory_mb: 2048
    disk_enabled: true
    redis_enabled: true
  vision:
    screenshots_dir: "/opt/aurora-pro/logs/screenshots"
    ocr_enabled: true
  browser:
    headless: true
    stealth: true

llm:
  default_provider: "claude-sonnet-4-5"
  max_retries: 3
  timeout: 60
  cost_tracking: true

autonomous:
  max_actions_per_workflow: 100
  default_timeout: 600
  auto_verify: true

monitoring:
  prometheus_enabled: true
  metrics_interval: 1
  health_check_interval: 30

logging:
  level: "INFO"
  format: "json"
  rotation: "daily"
  retention_days: 30
```

### Step 3: Ollama Models

```bash
# Download recommended models
ollama pull qwen2.5:latest
ollama pull llama3.2:latest
ollama pull codellama:latest

# Verify
ollama list
```

---

## Service Setup

### Step 1: Systemd Services

#### Aurora API Service

Create `/etc/systemd/system/aurora-api.service`:

```ini
[Unit]
Description=Aurora Pro API Server
After=network.target redis-server.service

[Service]
Type=simple
User=aurora
Group=aurora
WorkingDirectory=/opt/aurora-pro
Environment="PATH=/opt/aurora-pro/venv/bin"
EnvironmentFile=/opt/aurora-pro/.env
ExecStart=/opt/aurora-pro/venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log \
    --no-use-colors
Restart=always
RestartSec=10
StandardOutput=append:/opt/aurora-pro/logs/api.log
StandardError=append:/opt/aurora-pro/logs/api_error.log

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

#### Control Panel Service

Create `/etc/systemd/system/aurora-panel.service`:

```ini
[Unit]
Description=Aurora Pro Control Panel
After=network.target aurora-api.service

[Service]
Type=simple
User=aurora
Group=aurora
WorkingDirectory=/opt/aurora-pro
Environment="PATH=/opt/aurora-pro/venv/bin"
EnvironmentFile=/opt/aurora-pro/.env
ExecStart=/opt/aurora-pro/venv/bin/streamlit run \
    web_control_panel.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
Restart=always
RestartSec=10
StandardOutput=append:/opt/aurora-pro/logs/panel.log
StandardError=append:/opt/aurora-pro/logs/panel_error.log

[Install]
WantedBy=multi-user.target
```

### Step 2: Create Service User

```bash
# Create aurora user
sudo useradd -r -s /bin/bash -d /opt/aurora-pro -m aurora

# Transfer ownership
sudo chown -R aurora:aurora /opt/aurora-pro

# Add to required groups
sudo usermod -aG video aurora  # For GPU access
sudo usermod -aG input aurora  # For mouse/keyboard
```

### Step 3: Enable & Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable redis-server
sudo systemctl enable aurora-api
sudo systemctl enable aurora-panel

# Start services
sudo systemctl start redis-server
sudo systemctl start aurora-api
sudo systemctl start aurora-panel

# Check status
sudo systemctl status aurora-api
sudo systemctl status aurora-panel
```

### Step 4: Nginx Reverse Proxy

Create `/etc/nginx/sites-available/aurora-pro`:

```nginx
# Aurora Pro Nginx Configuration

# API Server
upstream aurora_api {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
}

# Control Panel
upstream aurora_panel {
    server 127.0.0.1:8501;
}

# Main Server Block
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max body size (for file uploads)
    client_max_body_size 100M;

    # API Endpoints
    location /api/ {
        proxy_pass http://aurora_api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Control Panel
    location / {
        proxy_pass http://aurora_panel;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # WebSocket for Control Center
    location /ws/ {
        proxy_pass http://aurora_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Static files
    location /static/ {
        alias /opt/aurora-pro/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (no auth)
    location /health {
        proxy_pass http://aurora_api/health;
        access_log off;
    }
}
```

Enable the site:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/aurora-pro /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Or iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -P INPUT DROP
```

### 2. API Authentication

Add to `main.py`:

```python
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    expected_token = os.getenv("API_AUTH_TOKEN")
    if token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return token

# Apply to sensitive endpoints
@app.post("/control/emergency-stop", dependencies=[Security(verify_token)])
async def control_emergency_stop(...):
    ...
```

### 3. Rate Limiting

```bash
# Install slowapi
pip install slowapi

# Add to main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.post("/llm/generate")
@limiter.limit("10/minute")
async def llm_generate(...):
    ...
```

### 4. Secrets Management

```bash
# Use environment variables, never hardcode
# Consider using vault for production
sudo apt install vault

# Or use Docker secrets
docker secret create anthropic_key /path/to/key.txt
```

---

## Monitoring & Logging

### 1. Prometheus Metrics

Create `/etc/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'aurora-pro'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 2. Grafana Dashboard

```bash
# Install Grafana
sudo apt install -y grafana

# Enable and start
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Access: http://localhost:3000
# Default login: admin/admin
```

Import Aurora Pro dashboard (create JSON with panels for):
- CPU/Memory usage
- Request rate
- Error rate
- LLM costs
- Agent health

### 3. Log Aggregation

```bash
# Install Filebeat
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.10.0-amd64.deb
sudo dpkg -i filebeat-8.10.0-amd64.deb

# Configure
sudo cat > /etc/filebeat/filebeat.yml << 'EOF'
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /opt/aurora-pro/logs/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]

setup.kibana:
  host: "localhost:5601"
EOF

# Start
sudo systemctl enable filebeat
sudo systemctl start filebeat
```

---

## Backup & Recovery

### 1. Database Backup

```bash
# Create backup script
cat > /opt/aurora-pro/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/aurora-pro/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /opt/aurora-pro/data/aurora.db $BACKUP_DIR/aurora_$TIMESTAMP.db

# Backup logs (last 7 days)
tar -czf $BACKUP_DIR/logs_$TIMESTAMP.tar.gz /opt/aurora-pro/logs/*.log

# Backup configs
tar -czf $BACKUP_DIR/config_$TIMESTAMP.tar.gz /opt/aurora-pro/.env /opt/aurora-pro/config/

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
EOF

chmod +x /opt/aurora-pro/scripts/backup.sh
```

### 2. Automated Backups

```bash
# Add to crontab
sudo crontab -e

# Add line (daily at 2 AM)
0 2 * * * /opt/aurora-pro/scripts/backup.sh >> /opt/aurora-pro/logs/backup.log 2>&1
```

### 3. Recovery Procedure

```bash
# Stop services
sudo systemctl stop aurora-api aurora-panel

# Restore database
cp /opt/aurora-pro/backups/aurora_YYYYMMDD_HHMMSS.db /opt/aurora-pro/data/aurora.db

# Restore configs
tar -xzf /opt/aurora-pro/backups/config_YYYYMMDD_HHMMSS.tar.gz -C /

# Start services
sudo systemctl start aurora-api aurora-panel

# Verify
curl http://localhost:8000/health
```

---

## Performance Tuning

### 1. Multicore Optimization

```python
# In main.py, adjust based on CPU cores
multicore_manager = get_multicore_manager(num_workers=CPU_COUNT - 2)

# For 32-core system: num_workers=30
# For 16-core system: num_workers=14
# For 8-core system: num_workers=6
```

### 2. Cache Configuration

```bash
# Redis tuning
sudo cat >> /etc/redis/redis.conf << 'EOF'
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

sudo systemctl restart redis-server
```

### 3. Database Optimization

```python
# Enable WAL mode for better concurrency
import sqlite3
conn = sqlite3.connect('/opt/aurora-pro/data/aurora.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA synchronous=NORMAL')
conn.execute('PRAGMA cache_size=-64000')  # 64MB cache
conn.close()
```

### 4. Uvicorn Workers

```bash
# Adjust based on CPU cores
# Formula: (2 x CPU cores) + 1
# For 32-core: --workers 65
# For 16-core: --workers 33
# For 8-core: --workers 17

# Update in systemd service
ExecStart=/opt/aurora-pro/venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 33 \
    ...
```

---

## Troubleshooting

### Common Issues

#### Issue: Services won't start

```bash
# Check logs
sudo journalctl -u aurora-api -f
sudo journalctl -u aurora-panel -f

# Check permissions
ls -la /opt/aurora-pro
ls -la /opt/aurora-pro/logs

# Check if ports are in use
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :8501
```

#### Issue: High memory usage

```bash
# Check memory
free -h
sudo ps aux --sort=-%mem | head

# Reduce cache size
# Edit .env
CACHE_MEMORY_MB=1024

# Reduce workers
# Edit main.py
multicore_manager = get_multicore_manager(num_workers=15)
```

#### Issue: LLM API errors

```bash
# Verify API keys
cat /opt/aurora-pro/.env | grep API_KEY

# Test APIs
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json"
```

---

## Deployment Checklist

### Pre-Launch
- [ ] All services running
- [ ] Health checks passing
- [ ] SSL certificates valid
- [ ] Backups configured
- [ ] Monitoring active
- [ ] Logs rotating
- [ ] Security hardened
- [ ] Performance tuned

### Launch
- [ ] DNS updated
- [ ] Load balancer configured
- [ ] Canary deployment (if applicable)
- [ ] Smoke tests passed
- [ ] Documentation updated
- [ ] Team notified

### Post-Launch
- [ ] Monitor for 24 hours
- [ ] Review error logs
- [ ] Check performance metrics
- [ ] Verify backups working
- [ ] Update runbooks

---

**Last Updated:** 2025-09-30
**Version:** Aurora Pro 2.0.0
**Deployment Status:** ✅ Production Ready