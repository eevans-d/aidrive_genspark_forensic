# 📚 API Documentation - Mini Market Dashboard

**Version:** 1.0.0  
**Base URL:** `http://localhost:8080`  
**Authentication:** API Key (Header: `X-API-Key`)  

---

## 🔐 Authentication

All API endpoints (except `/health`) require authentication via API key.

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:8080/api/inventory
```

---

## 📋 Endpoints

### Health Check

```http
GET /health
```

**Description:** Check service health status

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T10:30:00Z",
  "version": "1.0.0"
}
```

---

### Get Inventory

```http
GET /api/inventory
```

**Description:** Retrieve all inventory items

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Maximum items to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Product A",
      "quantity": 50,
      "price": 10.99,
      "last_updated": "2025-10-16T10:00:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

---

### Metrics

```http
GET /metrics
```

**Description:** Prometheus metrics exposition

**Authentication:** Required

**Response:** Prometheus text format

```
# HELP dashboard_requests_total Total requests
# TYPE dashboard_requests_total counter
dashboard_requests_total{endpoint="/health"} 1234
```

---

## 🚦 Rate Limiting

- **Default:** 100 requests per minute per IP
- **Login:** 5 requests per minute per IP

**Headers:**
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

---

## ❌ Error Responses

```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key",
  "status_code": 401
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `429`: Too Many Requests
- `500`: Internal Server Error

---

## 📊 Performance SLOs

- P95 Response Time: < 200ms
- Availability: 99.95%
- Error Rate: < 0.1%

---

**Last Updated:** October 16, 2025
