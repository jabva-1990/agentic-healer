# E-Commerce Microservices Platform

A comprehensive e-commerce platform built with microservices architecture.

## Architecture Overview

This platform consists of:
- **User Service**: Handles authentication and user management
- **Product Service**: Manages product catalog and inventory
- **Order Service**: Processes orders and payments
- **Notification Service**: Sends emails and notifications

## Technologies Used

- **Backend**: Python Flask, Node.js Express, Java Spring Boot
- **Database**: PostgreSQL, MongoDB, Redis
- **Container**: Docker & Docker Compose
- **Orchestration**: Kubernetes
- **CI/CD**: Jenkins Pipeline
- **Monitoring**: Prometheus, Grafana

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Build Docker images: `docker-compose build`
4. Deploy to Kubernetes: `kubectl apply -f k8s/`
5. Run tests: `pytest tests/`

## Services

### User Service (Port 3001)
- Authentication endpoint: `/api/auth/login`
- User registration: `/api/auth/register`
- Profile management: `/api/users/profile`

### Product Service (Port 3002)
- Product listing: `/api/products`
- Product details: `/api/products/{id}`
- Inventory management: `/api/inventory`

### Order Service (Port 3003)
- Create order: `/api/orders`
- Order history: `/api/orders/history`
- Payment processing: `/api/payments`

## Development

```bash
# Start development environment
docker-compose up -d

# Run specific service
cd backend/user-service
python app.py
```

## Testing

```bash
# Unit tests
pytest backend/tests/

# Integration tests
pytest tests/integration/

# Load tests
locust -f tests/load/locustfile.py
```

## Deployment

See [deployment guide](docs/deployment.md) for production setup.

## API Documentation

API documentation is available at `/docs` endpoint for each service.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## License

MIT License - see LICENSE file for details.
