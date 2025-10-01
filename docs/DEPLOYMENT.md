# Deployment Guide

## Containers

- Build: `docker build -f docker/Dockerfile -t aurora-pro .`
- Compose: `docker compose -f docker/docker-compose.yml up -d`

## Native

- `bash /root/aurora_pro/scripts/link_and_start.sh`
- `bash /root/aurora_pro/scripts/verify.sh`

