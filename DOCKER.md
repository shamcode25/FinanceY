# Docker Deployment Guide

This guide explains how to dockerize and host the FinanceY application.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)
- OpenAI API key

## Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone <your-repo-url>
   cd AIProject
   ```

2. **Create `.env` file**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Quick start with Docker**:
   ```bash
   ./docker-start.sh
   ```
   
   Or manually:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - React Frontend: http://localhost:3000
   - Streamlit Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

5. **Production deployment**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Docker Commands

### Build and Start
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop and Remove
```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove containers, volumes, and images
docker-compose down -v --rmi all
```

### Rebuild
```bash
# Rebuild after code changes
docker-compose up -d --build
```

## Individual Services

### Backend Only
```bash
# Build backend image
docker build -f Dockerfile.backend -t financey-backend .

# Run backend container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -v $(pwd)/data:/app/data \
  --name financey-backend \
  financey-backend
```

### Frontend Only
```bash
# Build frontend image
docker build -f Dockerfile.frontend -t financey-frontend .

# Run frontend container
docker run -d \
  -p 8501:8501 \
  -e API_BASE_URL=http://localhost:8000 \
  --name financey-frontend \
  financey-frontend
```

## Environment Variables

### Backend
- `OPENAI_API_KEY` (required): Your OpenAI API key
- `OPENAI_MODEL`: Model to use (default: gpt-4o)
- `EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-small)
- `DATA_DIR`: Data directory (default: /app/data)
- `FILINGS_DIR`: Filings directory (default: /app/data/filings)
- `VECTOR_DB_PATH`: Vector database path (default: /app/data/vectorstore)

### Frontend
- `API_BASE_URL`: Backend API URL (default: http://localhost:8000)

## Production Deployment

### Option 1: Docker Compose on VPS

1. **Set up a VPS** (DigitalOcean, AWS EC2, Linode, etc.)
2. **Install Docker and Docker Compose**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Clone and deploy**:
   ```bash
   git clone <your-repo-url>
   cd AIProject
   cp .env.example .env
   # Edit .env with your API key
   docker-compose up -d
   ```

4. **Set up reverse proxy** (Nginx):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }

       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Option 2: Docker Compose on Railway

1. **Create Railway account** at https://railway.app
2. **Create new project** and connect your GitHub repo
3. **Add environment variables** in Railway dashboard:
   - `OPENAI_API_KEY`
   - Other optional variables
4. **Deploy** - Railway will automatically detect `docker-compose.yml`

### Option 3: Docker Compose on Render

1. **Create Render account** at https://render.com
2. **Create new Web Service**
3. **Connect GitHub repository**
4. **Configure**:
   - Build Command: `docker-compose build`
   - Start Command: `docker-compose up`
   - Add environment variables in dashboard

### Option 4: Individual Containers on Cloud Run / ECS

#### Google Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/financey-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/financey-frontend

# Deploy
gcloud run deploy financey-backend \
  --image gcr.io/PROJECT_ID/financey-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=your_key

gcloud run deploy financey-frontend \
  --image gcr.io/PROJECT_ID/financey-frontend \
  --platform managed \
  --region us-central1 \
  --set-env-vars API_BASE_URL=https://financey-backend-url
```

#### AWS ECS
1. **Push images to ECR** (Elastic Container Registry)
2. **Create ECS task definition** with your containers
3. **Create ECS service** and deploy

## Security Considerations

1. **Never commit `.env` file** - Use environment variables in production
2. **Use secrets management**:
   - AWS Secrets Manager
   - Google Secret Manager
   - HashiCorp Vault
   - Docker Secrets (Swarm mode)

3. **Enable HTTPS**:
   - Use Let's Encrypt with Certbot
   - Use cloud provider's load balancer with SSL termination

4. **Limit resource usage**:
   ```yaml
   # Add to docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 2G
       reservations:
         cpus: '0.5'
         memory: 1G
   ```

## Monitoring

### Health Checks
Both services have health checks configured:
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:8501/_stcore/health`

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Export logs
docker-compose logs > logs.txt
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Check if API key is set
docker-compose exec backend env | grep OPENAI_API_KEY

# Restart service
docker-compose restart backend
```

### Frontend can't connect to backend
```bash
# Check if backend is running
docker-compose ps

# Check network connectivity
docker-compose exec frontend curl http://backend:8000/health

# Update API_BASE_URL in docker-compose.yml
```

### Port conflicts
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Backend on 8001
  - "8502:8501"  # Frontend on 8502
```

## Data Persistence

Data is stored in the `./data` directory, which is mounted as a volume. To backup:
```bash
# Backup data
tar -czf data-backup.tar.gz data/

# Restore data
tar -xzf data-backup.tar.gz
```

## Updates

To update the application:
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

## Scaling

For production, consider:
1. **Load balancer** for multiple backend instances
2. **Database** for vector storage (PostgreSQL with pgvector)
3. **Redis** for caching
4. **CDN** for static assets
5. **Monitoring** (Prometheus, Grafana)

