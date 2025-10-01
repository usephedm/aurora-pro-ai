# Aurora Pro AI - Deployment Guide

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### One-Click Deployment

```bash
./deploy.sh
```

This script will:
1. Check prerequisites
2. Create `.env` configuration
3. Build Docker images
4. Start all services
5. Verify health

### Manual Deployment

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Start services
docker-compose up -d

# 3. Check status
docker-compose ps
docker-compose logs -f
```

## Service Architecture

### Core Services

1. **FastAPI Backend** (Port 8000)
   - REST API endpoints
   - Multi-agent orchestration
   - Health monitoring
   - Metrics collection

2. **Streamlit GUI** (Port 8501)
   - Interactive web interface
   - Agent management
   - Task execution
   - System monitoring

3. **Redis Cache** (Port 6379)
   - Fast in-memory caching
   - Session storage
   - Model information cache

4. **Ollama LLM** (Port 11434)
   - Local LLM inference
   - Privacy-focused
   - Multiple model support

5. **Prometheus** (Port 9090)
   - Metrics collection
   - Performance monitoring
   - Health tracking

6. **Grafana** (Port 3000)
   - Visual dashboards
   - Alerting
   - Data exploration

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# Application
APP_NAME=aurora-pro-ai
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=sqlite:///./data/aurora.db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# LLM
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=llama2

# Security
SECRET_KEY=<generated-by-deploy-script>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Agents
MAX_AGENTS=10
ORCHESTRATION_MODE=sequential
```

## Usage

### API Examples

```bash
# Health check
curl http://localhost:8000/health/

# Create agent
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agent",
    "agent_type": "llm",
    "model_name": "llama2",
    "provider": "ollama"
  }'

# Execute task
curl -X POST http://localhost:8000/api/v1/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "my-agent",
    "prompt": "Hello, what can you do?"
  }'
```

### GUI Access

1. Open http://localhost:8501
2. Navigate to "Agents" page
3. Create your first agent
4. Go to "Tasks" page
5. Execute tasks

## Monitoring

### Health Checks

- API: http://localhost:8000/health/ready
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f gui

# Last 100 lines
docker-compose logs --tail=100
```

### Metrics

Access Prometheus metrics at:
- http://localhost:8000/metrics (FastAPI)
- http://localhost:9090 (Prometheus UI)

## Troubleshooting

### Service Not Starting

```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Rebuild image
docker-compose build --no-cache <service-name>
docker-compose up -d <service-name>
```

### Database Issues

```bash
# Reset database
docker-compose down
rm -rf data/*.db
docker-compose up -d
```

### Port Conflicts

Edit `docker-compose.yml` to change ports:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

## Backup & Recovery

### Backup

```bash
# Backup database
docker-compose exec api cp /app/data/aurora.db /app/data/aurora.db.backup

# Backup from host
cp data/aurora.db data/aurora.db.backup
```

### Recovery

```bash
# Restore database
cp data/aurora.db.backup data/aurora.db
docker-compose restart api
```

## Security

### Production Checklist

- [ ] Change default `SECRET_KEY` in `.env`
- [ ] Set strong passwords for Grafana
- [ ] Configure CORS origins appropriately
- [ ] Enable rate limiting
- [ ] Set up HTTPS with reverse proxy
- [ ] Review and restrict exposed ports
- [ ] Enable authentication for APIs
- [ ] Regular security updates

### Recommended Security Setup

```bash
# Use with reverse proxy (nginx, traefik)
# Don't expose all ports publicly
# Use SSL/TLS certificates
# Implement API authentication
# Regular backups
# Monitor security logs
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
api:
  deploy:
    replicas: 3
```

### Load Balancing

Use nginx or traefik as reverse proxy:

```nginx
upstream aurora-api {
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}
```

## Maintenance

### Updates

```bash
# Update images
docker-compose pull

# Restart services
docker-compose up -d

# Clean old images
docker image prune
```

### Database Migrations

```bash
# Create migration
docker-compose exec api alembic revision --autogenerate -m "migration message"

# Apply migration
docker-compose exec api alembic upgrade head
```

## Support

- Documentation: [docs/](docs/)
- API Docs: http://localhost:8000/docs
- Issues: https://github.com/usephedm/aurora-pro-ai/issues

## Additional Resources

- [API Documentation](API.md)
- [Plugin Development Guide](PLUGINS.md)
- [Architecture Overview](ARCHITECTURE.md)
