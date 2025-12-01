# E-commerce API Documentation

## Overview

This document describes the REST API for the e-commerce microservices platform.

**Base URL:** `https://api.ecommerce.com/api/v1`  
**Version:** 1.0.0  
**Last Updated:** January 2023  <!-- OUTDATED -->

## Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Authentication Flow

1. **Login:** POST `/auth/login`
2. **Get Token:** Extract `access_token` from response
3. **Use Token:** Include in `Authorization` header: `Bearer <token>`

### Token Expiration

- **Access Token:** 1 hour  <!-- SHORT EXPIRATION -->
- **Refresh Token:** 7 days

### Example

```bash
# Login
curl -X POST https://api.ecommerce.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Use token
curl -H "Authorization: Bearer <access_token>" \
  https://api.ecommerce.com/api/v1/users/profile
```

## User Service API

### Base URL: `/users`

#### POST `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+1-555-0123"  // Optional
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "createdAt": "2024-01-15T10:30:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors:**
- `400`: Invalid input data
- `409`: Email already exists
- `422`: Validation errors  <!-- MISSING DETAILS -->

#### POST `/auth/login`

Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "firstName": "John",
      "lastName": "Doe"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  }
}
```

#### GET `/profile`

🔒 **Requires Authentication**

Get current user profile.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1-555-0123",
    "address": {
      "street": "123 Main St",
      "city": "New York",
      "state": "NY",
      "zipCode": "10001",
      "country": "US"
    },
    "preferences": {
      "newsletter": true,
      "notifications": false
    },
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-20T14:22:00Z"
  }
}
```

#### PUT `/profile`

🔒 **Requires Authentication**

Update user profile.

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Smith",
  "phone": "+1-555-0124",
  "address": {
    "street": "456 Oak Ave",
    "city": "Los Angeles",
    "state": "CA",
    "zipCode": "90210",
    "country": "US"
  }
}
```

<!-- MISSING ENDPOINTS:
- POST /auth/forgot-password
- POST /auth/reset-password
- POST /auth/refresh-token
- DELETE /profile (delete account)
- GET /users/{id} (admin only)
- GET /users (admin only, with pagination)
-->

## Product Service API

### Base URL: `/products`

#### GET `/products`

Get list of products with filtering and pagination.

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 20, max: 100) - Items per page
- `category` (string) - Filter by category
- `minPrice` (number) - Minimum price filter
- `maxPrice` (number) - Maximum price filter
- `search` (string) - Search in name/description
- `sortBy` (string) - Sort field (name, price, createdAt)
- `sortOrder` (string) - Sort direction (asc, desc)
- `inStock` (boolean) - Filter by availability

**Example Request:**
```bash
GET /api/v1/products?page=1&limit=10&category=electronics&minPrice=100&sortBy=price&sortOrder=asc
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": "prod_123",
        "name": "Smartphone XYZ",
        "description": "Latest smartphone with advanced features",
        "price": 699.99,
        "currency": "USD",
        "category": "electronics",
        "subcategory": "phones",
        "brand": "TechBrand",
        "sku": "TB-SM-XYZ-001",
        "images": [
          "https://cdn.ecommerce.com/products/prod_123/image1.jpg",
          "https://cdn.ecommerce.com/products/prod_123/image2.jpg"
        ],
        "inventory": {
          "quantity": 50,
          "inStock": true,
          "reserved": 5
        },
        "specifications": {
          "color": "Black",
          "storage": "128GB",
          "screen": "6.1 inch"
        },
        "rating": {
          "average": 4.5,
          "count": 127
        },
        "createdAt": "2024-01-10T08:15:00Z",
        "updatedAt": "2024-01-18T16:42:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 156,
      "totalPages": 16,
      "hasNext": true,
      "hasPrev": false
    },
    "filters": {
      "appliedFilters": {
        "category": "electronics",
        "minPrice": 100
      },
      "availableCategories": ["electronics", "clothing", "home"],
      "priceRange": {
        "min": 9.99,
        "max": 1299.99
      }
    }
  }
}
```

#### GET `/products/{id}`

Get single product details.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "prod_123",
    "name": "Smartphone XYZ",
    "description": "Latest smartphone with advanced features...",
    "longDescription": "This cutting-edge smartphone features...",
    "price": 699.99,
    "currency": "USD",
    "category": "electronics",
    "subcategory": "phones",
    "brand": "TechBrand",
    "sku": "TB-SM-XYZ-001",
    "images": [
      "https://cdn.ecommerce.com/products/prod_123/image1.jpg",
      "https://cdn.ecommerce.com/products/prod_123/image2.jpg",
      "https://cdn.ecommerce.com/products/prod_123/image3.jpg"
    ],
    "inventory": {
      "quantity": 50,
      "inStock": true,
      "reserved": 5,
      "lowStockThreshold": 10
    },
    "specifications": {
      "color": "Black",
      "storage": "128GB",
      "screen": "6.1 inch",
      "battery": "4000mAh",
      "camera": "48MP",
      "os": "Android 12"
    },
    "rating": {
      "average": 4.5,
      "count": 127,
      "distribution": {
        "5": 65,
        "4": 42,
        "3": 15,
        "2": 3,
        "1": 2
      }
    },
    "tags": ["smartphone", "5g", "wireless-charging"],
    "variants": [
      {
        "id": "var_124",
        "color": "White",
        "price": 699.99,
        "sku": "TB-SM-XYZ-002"
      },
      {
        "id": "var_125",
        "storage": "256GB",
        "price": 799.99,
        "sku": "TB-SM-XYZ-256"
      }
    ],
    "relatedProducts": ["prod_124", "prod_125", "prod_126"],
    "createdAt": "2024-01-10T08:15:00Z",
    "updatedAt": "2024-01-18T16:42:00Z"
  }
}
```

#### POST `/products` 🔒

**Requires Authentication (Admin/Seller role)**

Create a new product.

**Request Body:**
```json
{
  "name": "New Product",
  "description": "Product description",
  "price": 99.99,
  "category": "electronics",
  "subcategory": "accessories",
  "brand": "BrandName",
  "sku": "BN-ACC-001",
  "inventory": {
    "quantity": 100,
    "lowStockThreshold": 10
  },
  "specifications": {
    "color": "Blue",
    "material": "Plastic"
  }
}
```

<!-- MISSING ENDPOINTS:
- PUT /products/{id}
- DELETE /products/{id}
- POST /products/{id}/images
- DELETE /products/{id}/images/{imageId}
- GET /products/{id}/reviews
- POST /products/{id}/reviews
- GET /categories
- GET /brands
-->

## Order Service API

### Base URL: `/orders`

<!-- INCOMPLETE SECTION - MAJOR DOCUMENTATION GAP -->

#### GET `/orders` 🔒

**Requires Authentication**

Get user's orders.

**Query Parameters:**
- `status` (string) - Filter by order status
- `page` (integer) - Page number
- `limit` (integer) - Items per page

**Response (200):**
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "id": "order_123",
        "status": "shipped",
        "total": 149.98,
        "currency": "USD",
        "createdAt": "2024-01-15T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "total": 5
    }
  }
}
```

<!-- MISSING ORDER ENDPOINTS:
- POST /orders (create order)
- GET /orders/{id} (order details)
- PUT /orders/{id}/status (update status)
- POST /orders/{id}/cancel
- GET /orders/{id}/tracking
-->

## Error Responses

### Standard Error Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "The provided input is invalid",
    "details": [
      {
        "field": "email",
        "message": "Email format is invalid"
      }
    ],
    "timestamp": "2024-01-20T10:15:30Z",
    "requestId": "req_abc123"
  }
}
```

### HTTP Status Codes

- `200` - OK
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Unprocessable Entity
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_INPUT` | Request body validation failed |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

## Rate Limiting

- **Authenticated requests:** 1000 requests per hour
- **Unauthenticated requests:** 100 requests per hour  <!-- VERY RESTRICTIVE -->
- **Admin requests:** 5000 requests per hour

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1642694400
```

## Webhooks

<!-- INCOMPLETE SECTION -->

The API supports webhooks for real-time notifications:

- `order.created`
- `order.updated`
- `order.cancelled`
- `payment.completed`
- `payment.failed`

<!-- MISSING WEBHOOK DOCUMENTATION -->

## SDKs and Libraries

<!-- OUTDATED LINKS -->

- **JavaScript/Node.js:** [ecommerce-js-sdk](https://npm.im/ecommerce-sdk)  <!-- FICTIONAL PACKAGE -->
- **Python:** [ecommerce-python](https://pypi.org/project/ecommerce-sdk/)  <!-- FICTIONAL PACKAGE -->
- **PHP:** [ecommerce-php](https://packagist.org/packages/company/ecommerce-sdk)  <!-- FICTIONAL PACKAGE -->

## Support

- **Documentation:** [https://docs.ecommerce.com](https://docs.ecommerce.com)  <!-- GENERIC URL -->
- **API Status:** [https://status.ecommerce.com](https://status.ecommerce.com)  <!-- GENERIC URL -->
- **Support Email:** api-support@ecommerce.com  <!-- GENERIC EMAIL -->

---

**Note:** This documentation may be outdated. Please refer to the latest version in the developer portal.  <!-- WARNING ABOUT OUTDATED DOCS -->
