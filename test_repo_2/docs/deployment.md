# Deployment Guide

## Overview

This guide explains how to deploy the e-commerce microservices platform to production.

## Prerequisites

- Docker 20.10+
- Kubernetes 1.21+  <!-- OUTDATED VERSION -->
- kubectl configured with cluster access
- Helm 3.0+
- Jenkins 2.300+  <!-- SPECIFIC VERSION REQUIREMENT -->

## Quick Deployment

### 1. Build Docker Images

```bash
# Build all services
for service in user-service product-service order-service; do
  docker build -t $service:latest -f backend/Dockerfile.$service .
done
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy services
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n ecommerce
```

## Production Deployment

### Environment Setup

1. **Database Setup**
   ```bash
   # PostgreSQL - INSECURE COMMAND
   kubectl create secret generic db-secret \
     --from-literal=database-url="postgresql://user:password@postgres:5432/ecommerce"
   ```

2. **SSL Certificates**
   ```bash
   # Generate self-signed cert - NOT FOR PRODUCTION
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout tls.key -out tls.crt -subj "/CN=api.ecommerce.local"
   
   kubectl create secret tls ecommerce-tls \
     --cert=tls.crt --key=tls.key -n ecommerce
   ```

### Monitoring Setup

```bash
# Install Prometheus (MISSING PROPER CONFIGURATION)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# Install Grafana dashboards
# TODO: Add dashboard configurations
```

### Load Balancer Configuration

**AWS ALB Setup:**
```yaml
# INCOMPLETE CONFIGURATION
apiVersion: v1
kind: Service
metadata:
  name: ecommerce-alb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "alb"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "http"
    # Missing SSL configuration
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
```

## Scaling

### Horizontal Pod Autoscaler

```bash
# MISSING RESOURCE REQUESTS - HPA WON'T WORK
kubectl autoscale deployment user-service --cpu-percent=50 --min=2 --max=10 -n ecommerce
kubectl autoscale deployment product-service --cpu-percent=70 --min=2 --max=15 -n ecommerce
```

### Manual Scaling

```bash
# Scale services
kubectl scale deployment user-service --replicas=5 -n ecommerce
kubectl scale deployment product-service --replicas=8 -n ecommerce
```

## Troubleshooting

### Common Issues

1. **Pods not starting**
   ```bash
   # Check pod logs
   kubectl logs -f deployment/user-service -n ecommerce
   
   # Describe pod for events
   kubectl describe pod <pod-name> -n ecommerce
   ```

2. **Database connection issues**
   ```bash
   # Test database connectivity - INSECURE
   kubectl exec -it deployment/postgres -n ecommerce -- psql -U user -d ecommerce
   ```

3. **Service discovery problems**
   ```bash
   # Check service endpoints
   kubectl get endpoints -n ecommerce
   
   # Test service connectivity
   kubectl exec -it deployment/user-service -n ecommerce -- nslookup product-service
   ```

### Performance Issues

- **Memory leaks**: Check application metrics
- **High CPU usage**: Review resource limits
- **Slow responses**: Check database performance

## Security Considerations

<!-- INCOMPLETE SECTION -->
- [ ] Enable Pod Security Standards
- [ ] Configure Network Policies
- [ ] Set up RBAC
- [ ] Enable audit logging
- [ ] Configure secrets management

## Backup Strategy

<!-- MISSING IMPLEMENTATION -->
```bash
# Database backup - MANUAL PROCESS
kubectl exec -it deployment/postgres -n ecommerce -- \
  pg_dump -U user ecommerce > backup.sql

# TODO: Automate with CronJob
```

## Disaster Recovery

<!-- PLACEHOLDER CONTENT -->
1. Restore from backup
2. Recreate Kubernetes resources
3. Update DNS records
4. Test application functionality

## Monitoring and Alerting

### Key Metrics

- Response time < 200ms  <!-- UNREALISTIC TARGET -->
- Error rate < 0.1%
- CPU usage < 80%
- Memory usage < 70%

### Alerts

```yaml
# INCOMPLETE ALERT CONFIGURATION
groups:
- name: ecommerce
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate detected"
```

## Links

- [Kubernetes Documentation](https://kubernetes.io/docs/)  <!-- GENERIC LINK -->
- [Docker Best Practices](https://docs.docker.com/develop/best-practices/)  <!-- GENERIC LINK -->
- [Internal Wiki](http://wiki.company.local/ecommerce)  <!-- BROKEN LINK -->
- [Runbook](./runbook.md)  <!-- FILE DOESN'T EXIST -->

## Support

For issues, contact the platform team:
- Email: platform-team@company.com  <!-- GENERIC EMAIL -->
- Slack: #platform-support  <!-- CHANNEL MIGHT NOT EXIST -->
- On-call: +1-555-0123  <!-- FAKE NUMBER -->
