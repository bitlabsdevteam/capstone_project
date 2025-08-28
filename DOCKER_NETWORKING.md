# Docker Networking Architecture

## Overview

This project uses direct service-to-service communication within Docker Compose networking, eliminating the need for a reverse proxy like Nginx. This approach follows industry best practices for microservices architecture in containerized environments.

## Architecture Benefits

### 1. **Simplified Architecture**
- Reduced complexity by removing proxy layer
- Fewer moving parts to maintain and debug
- Direct service discovery through Docker's internal DNS

### 2. **Performance Optimization**
- Eliminates proxy overhead and latency
- Direct TCP connections between services
- Reduced network hops and processing time

### 3. **Development Efficiency**
- Faster development cycles without proxy configuration
- Simplified debugging and logging
- Easier service scaling and load balancing

## Service Communication

### Frontend → Backend Communication

**Internal Communication (Container-to-Container):**
```
frontend:3000 → backend:8000
```

**External Access (Host-to-Container):**
```
localhost:3000 → frontend:3000 → backend:8000
localhost:8000 → backend:8000 (direct API access)
```

### Environment Variables

**Frontend Service:**
- `NEXT_PUBLIC_API_URL=http://backend:8000` - Public API endpoint
- `NEXT_PUBLIC_WS_URL=ws://backend:8000` - WebSocket endpoint
- `INTERNAL_API_URL=http://backend:8000` - Internal API calls

**Backend Service:**
- `ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000`
- `CORS_ALLOW_CREDENTIALS=true`
- `CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS,PATCH`
- `CORS_ALLOW_HEADERS=*`

## Network Configuration

### Docker Compose Network

```yaml
networks:
  app-network:
    driver: bridge
```

**All services connect to the same bridge network:**
- `backend` - FastAPI application
- `frontend` - Next.js application
- `postgres` - PostgreSQL database
- `redis` - Redis cache

### Service Discovery

Docker's built-in DNS resolution enables services to communicate using service names:
- `backend` resolves to the backend container's IP
- `postgres` resolves to the database container's IP
- `redis` resolves to the cache container's IP

## Security Best Practices

### 1. **CORS Configuration**
```python
# Backend CORS settings
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://frontend:3000"
]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

### 2. **Network Isolation**
- Services communicate only within the Docker network
- External access limited to exposed ports (3000, 8000)
- Database and Redis not directly accessible from host

### 3. **Environment-based Configuration**
- Different settings for development/production
- Secure credential management through environment variables
- Configurable CORS origins based on deployment environment

## API Routing

### Next.js API Rewrites

```typescript
// next.config.ts
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: `${process.env.INTERNAL_API_URL}/api/:path*`,
    },
  ];
}
```

**Benefits:**
- Transparent API proxying from frontend to backend
- Consistent API endpoints for client-side code
- Environment-based backend URL configuration

## Health Checks

### Service Health Monitoring

**Backend Health Check:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**Frontend Health Check:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:3000 || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Development Workflow

### 1. **Starting Services**
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Check service status
docker compose ps
```

### 2. **Service Communication Testing**
```bash
# Test backend health
curl http://localhost:8000/docs

# Test frontend
curl http://localhost:3000

# Test internal communication
docker compose exec frontend curl http://backend:8000/docs
```

### 3. **Debugging Network Issues**
```bash
# Inspect network
docker network ls
docker network inspect vizuara_capstoneproject_app-network

# Check service connectivity
docker compose exec frontend ping backend
docker compose exec backend ping postgres
```

## Production Considerations

### 1. **Load Balancing**
- Use Docker Swarm or Kubernetes for production
- Implement service mesh for advanced traffic management
- Consider external load balancers for high availability

### 2. **Security Hardening**
- Implement proper authentication and authorization
- Use secrets management for sensitive data
- Enable TLS/SSL for production deployments
- Restrict CORS origins to production domains

### 3. **Monitoring and Observability**
- Implement distributed tracing
- Add metrics collection (Prometheus/Grafana)
- Centralized logging (ELK stack or similar)
- Service mesh observability tools

### 4. **Scalability**
- Horizontal scaling with multiple container instances
- Database connection pooling
- Redis clustering for cache scalability
- CDN integration for static assets

## Troubleshooting

### Common Issues

**1. Service Connection Refused**
```bash
# Check if service is running
docker compose ps

# Check service logs
docker compose logs backend

# Verify network connectivity
docker compose exec frontend ping backend
```

**2. CORS Errors**
- Verify ALLOWED_ORIGINS includes frontend service name
- Check browser developer tools for specific CORS errors
- Ensure credentials are properly configured

**3. Environment Variable Issues**
```bash
# Check environment variables
docker compose exec backend env | grep API
docker compose exec frontend env | grep NEXT_PUBLIC
```

## Migration from Nginx

This architecture replaces the previous Nginx reverse proxy setup with direct service communication, providing:

- **Reduced Complexity**: Fewer configuration files and services
- **Better Performance**: Direct connections without proxy overhead
- **Easier Debugging**: Simplified request flow and logging
- **Development Speed**: Faster iteration without proxy reconfiguration

The migration maintains all functionality while improving maintainability and performance.