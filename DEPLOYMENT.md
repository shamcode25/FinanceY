# FinanceY Deployment Guide

Complete guide for deploying FinanceY in production environments.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Docker Deployment](#local-docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Cloud Platform Deployment](#cloud-platform-deployment)
5. [Environment Variables](#environment-variables)
6. [SSL/HTTPS Setup](#sslhttps-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Scaling](#scaling)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- OpenAI API key
- 2GB+ RAM available
- 10GB+ disk space

### Local Development

```bash
# 1. Clone repository
git clone <your-repo-url>
cd AIProject

# 2. Create .env file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start with Docker Compose
docker-compose up -d

# 4. Access application
# - React Frontend: http://localhost
# - Streamlit Frontend: http://localhost:8501
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Production Deployment

```bash
# 1. Create .env file with production settings
cp .env.example .env
# Edit .env with production values

# 2. Deploy with production compose file
docker-compose -f docker-compose.prod.yml up -d

# 3. Check status
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## Local Docker Deployment

### Option 1: Using Docker Compose (Recommended)

```bash
# Start all services
./docker-start.sh

# Or manually:
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Individual Containers

#### Backend Only

```bash
# Build image
docker build -f Dockerfile.backend -t financey-backend .

# Run container
docker run -d \
  --name financey-backend \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -v $(pwd)/data:/app/data \
  financey-backend
```

#### React Frontend Only

```bash
# Build image
docker build -f Dockerfile.frontend-react -t financey-frontend-react .

# Run container
docker run -d \
  --name financey-frontend-react \
  -p 80:80 \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  financey-frontend-react
```

#### Streamlit Frontend Only

```bash
# Build image
docker build -f Dockerfile.frontend -t financey-frontend-streamlit .

# Run container
docker run -d \
  --name financey-frontend-streamlit \
  -p 8501:8501 \
  -e API_BASE_URL=http://localhost:8000 \
  financey-frontend-streamlit
```

## Production Deployment

### Option 1: VPS with Docker Compose

#### Setup on Ubuntu/Debian

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Clone repository
git clone <your-repo-url>
cd AIProject

# 4. Create .env file
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY

# 5. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 6. Set up Nginx reverse proxy (optional)
sudo apt install nginx
sudo cp docker/nginx.prod.conf /etc/nginx/sites-available/financey
sudo ln -s /etc/nginx/sites-available/financey /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Option 2: Railway

1. **Create Railway account** at https://railway.app
2. **Create new project** and connect GitHub repository
3. **Add environment variables** in Railway dashboard:
   - `OPENAI_API_KEY`
   - Other optional variables
4. **Deploy** - Railway will auto-detect `docker-compose.yml`

### Option 3: Render

1. **Create Render account** at https://render.com
2. **Create new Web Service**
3. **Connect GitHub repository**
4. **Configure**:
   - Build Command: `docker-compose build`
   - Start Command: `docker-compose up`
   - Environment: Add variables in dashboard

### Option 4: Google Cloud Run

```bash
# 1. Enable Cloud Run API
gcloud services enable run.googleapis.com

# 2. Build and push images
gcloud builds submit --tag gcr.io/PROJECT_ID/financey-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/financey-frontend-react

# 3. Deploy backend
gcloud run deploy financey-backend \
  --image gcr.io/PROJECT_ID/financey-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=your_key \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2

# 4. Deploy frontend
gcloud run deploy financey-frontend \
  --image gcr.io/PROJECT_ID/financey-frontend-react \
  --platform managed \
  --region us-central1 \
  --set-env-vars VITE_API_BASE_URL=https://financey-backend-url \
  --allow-unauthenticated \
  --memory 512Mi
```

### Option 5: AWS ECS/Fargate

1. **Push images to ECR** (Elastic Container Registry)
2. **Create ECS task definition** with both containers
3. **Create ECS service** and deploy
4. **Set up Application Load Balancer** for public access
5. **Configure environment variables** in task definition

### Option 6: DigitalOcean App Platform

1. **Create DigitalOcean account**
2. **Create new App** from GitHub repository
3. **Configure**:
   - Build command: `docker-compose build`
   - Run command: `docker-compose up`
   - Environment variables in dashboard
4. **Deploy**

## Environment Variables

### Required Variables

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Optional Variables

```env
# OpenAI Configuration
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.0
OPENAI_MAX_TOKENS=2000

# Embedding Configuration
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5

# Data Paths
DATA_DIR=./data
FILINGS_DIR=./data/filings
VECTOR_DB_PATH=./data/vectorstore
TRANSCRIPTS_DIR=./data/transcripts
NEWS_DIR=./data/news

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000
```

## SSL/HTTPS Setup

### Using Let's Encrypt with Nginx

1. **Install Certbot**:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Obtain certificate**:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **Auto-renewal**:
   ```bash
   sudo certbot renew --dry-run
   ```

### Using Cloud Provider SSL

- **Cloudflare**: Use Cloudflare SSL/TLS with proxy
- **AWS**: Use ACM (AWS Certificate Manager) with ALB
- **GCP**: Use Google Managed SSL with Load Balancer
- **Azure**: Use Azure Application Gateway with SSL

## Monitoring & Logging

### Health Checks

All services have health check endpoints:
- Backend: `http://localhost:8000/health`
- Streamlit: `http://localhost:8501/_stcore/health`
- React: `http://localhost/health`

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f frontend-react

# Export logs
docker-compose logs > logs.txt
```

### Monitoring Tools

- **Prometheus + Grafana**: For metrics and dashboards
- **Datadog**: For APM and logging
- **New Relic**: For application monitoring
- **Sentry**: For error tracking

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    # Use load balancer in front
```

### Vertical Scaling

```yaml
# Increase resources in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### Database for Vector Store

For production, consider using:
- **PostgreSQL with pgvector**: For vector storage
- **Pinecone**: Managed vector database
- **Weaviate**: Open-source vector database
- **Qdrant**: Vector similarity search engine

## Backup & Recovery

### Backup Data

```bash
# Backup data directory
tar -czf financey-backup-$(date +%Y%m%d).tar.gz data/

# Backup to cloud storage
aws s3 cp financey-backup-*.tar.gz s3://your-bucket/backups/
```

### Restore Data

```bash
# Restore from backup
tar -xzf financey-backup-YYYYMMDD.tar.gz

# Restore to Docker volume
docker run --rm -v financey_backend_data:/data -v $(pwd):/backup \
  alpine tar -xzf /backup/financey-backup-YYYYMMDD.tar.gz -C /data
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Check environment variables
docker-compose exec backend env | grep OPENAI

# Restart service
docker-compose restart backend
```

### Frontend Can't Connect to Backend

```bash
# Check if backend is running
docker-compose ps

# Check network connectivity
docker-compose exec frontend-react wget -O- http://backend:8000/health

# Update API_BASE_URL in frontend environment
```

### Port Conflicts

```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Backend on 8001
  - "8502:8501"  # Streamlit on 8502
  - "8080:80"    # React on 8080
```

### Out of Memory

```bash
# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 8G
```

### Database/Vector Store Issues

```bash
# Rebuild index
docker-compose exec backend python -c "from backend.rag.retriever import RAGRetriever; r = RAGRetriever(); r.build_index(...)"

# Clear and restart
docker-compose down -v
docker-compose up -d
```

## Security Best Practices

1. **Never commit `.env` file** - Use environment variables
2. **Use secrets management**:
   - AWS Secrets Manager
   - Google Secret Manager
   - HashiCorp Vault
   - Docker Secrets

3. **Enable HTTPS** in production
4. **Use firewall** to restrict access
5. **Regular updates** - Keep Docker images updated
6. **Resource limits** - Set CPU and memory limits
7. **Non-root user** - Run containers as non-root (already configured)

## Performance Optimization

1. **Use CDN** for static assets
2. **Enable caching** in Nginx
3. **Optimize Docker images** - Multi-stage builds
4. **Use connection pooling** for database
5. **Enable compression** - Gzip in Nginx
6. **Monitor resource usage** - Set up alerts

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Check health: `curl http://localhost:8000/health`
- Review documentation: `README.md` and `DOCKER.md`
- Open an issue on GitHub

