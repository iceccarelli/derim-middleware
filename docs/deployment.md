# DERIM Deployment Guide

This guide covers deploying the DERIM middleware in various environments, from local development to production infrastructure.

## Local Development

The simplest way to run DERIM is with SQLite storage and no external dependencies.

```bash
# Create and activate a virtual environment.
python -m venv .venv
source .venv/bin/activate

# Install dependencies and the package.
pip install -r requirements/base.txt
pip install -e .

# Copy the environment template.
cp .env.example .env

# Start the development server with auto-reload.
uvicorn derim.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`. SQLite will automatically create a database file at the path specified in `SQLITE_DB_PATH`.

## Docker Deployment

### Building the Image

```bash
docker build -t derim-middleware:latest .
```

### Running with Docker Compose

The included `docker-compose.yml` orchestrates the full stack.

```bash
# Start API + InfluxDB.
docker compose up -d

# Verify services are running.
docker compose ps

# View API logs.
docker compose logs -f api

# Stop all services.
docker compose down
```

### Optional Services

Additional services can be enabled using Docker Compose profiles.

```bash
# Include Grafana monitoring dashboard.
docker compose --profile monitoring up -d

# Include Jupyter Lab for ML notebooks.
docker compose --profile ml up -d

# Include Mosquitto MQTT broker.
docker compose --profile mqtt up -d

# Enable all optional services.
docker compose --profile monitoring --profile ml --profile mqtt up -d
```

### Environment Variables

Override default settings by creating a `.env` file in the project root or by passing environment variables to Docker.

```bash
# Example: Custom InfluxDB credentials.
INFLUXDB_TOKEN=my-production-token
INFLUXDB_ORG=my-utility
INFLUXDB_BUCKET=der_production
LOG_LEVEL=WARNING
```

## Production Considerations

### Reverse Proxy

For production deployments, place the DERIM API behind a reverse proxy such as Nginx or Traefik to handle TLS termination, rate limiting, and load balancing.

```nginx
server {
    listen 443 ssl;
    server_name derim.example.com;

    ssl_certificate     /etc/ssl/certs/derim.crt;
    ssl_certificate_key /etc/ssl/private/derim.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Scaling

The FastAPI application is stateless (all state is in the storage backend), so it can be horizontally scaled by running multiple Uvicorn workers or multiple container replicas behind a load balancer.

```bash
# Multiple workers in a single container.
uvicorn derim.main:app --host 0.0.0.0 --port 8000 --workers 4

# Multiple replicas with Docker Compose.
docker compose up -d --scale api=3
```

### Monitoring

For production monitoring, enable the Grafana profile and configure InfluxDB as a data source. The health endpoint at `/health` returns the application version, storage backend status, and uptime, making it suitable for integration with monitoring tools such as Prometheus, Datadog, or Nagios.

### Backup

InfluxDB data is stored in a Docker volume. Regular backups should be configured using InfluxDB's built-in backup commands.

```bash
# Backup InfluxDB data.
docker exec derim-influxdb influx backup /tmp/backup
docker cp derim-influxdb:/tmp/backup ./backups/

# Restore from backup.
docker cp ./backups/backup derim-influxdb:/tmp/backup
docker exec derim-influxdb influx restore /tmp/backup
```
