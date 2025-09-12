
# 🚀 INVENTARIO RETAIL - WEB DASHBOARD SYSTEM
## DEPLOYMENT GUIDE

### 📋 System Overview
Complete interactive web dashboard for your Argentine retail inventory system with:
- Real-time WebSocket dashboard with KPIs
- Mobile-responsive design for warehouse tablets
- Integration with all backend APIs (deposito:8000, negocio:8001, ml:8002)
- Docker containerization for easy deployment

### 🎯 Quick Deploy (Recommended)
```bash
cd /mnt/aidrive/inventario_retail_dashboard_web/
chmod +x deploy.sh
./deploy.sh
```

### 🔧 Manual Deployment Steps
1. **Download from AI Drive:**
   ```bash
   # Download the complete system
   cp -r /mnt/aidrive/inventario_retail_dashboard_web/ ~/inventario-dashboard/
   cd ~/inventario-dashboard/
   ```

2. **Start with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Access the Dashboard:**
   - URL: http://localhost:5000
   - Default login: admin/admin123

### 🌟 Key Features Implemented
✅ Redis Cache Intelligence (30s TTL + invalidation)
✅ OCR Advanced System (EasyOCR + Tesseract + PaddleOCR)  
✅ ML Intelligent Predictions (Purchase recommendations)
✅ Web Dashboard (Real-time + Mobile responsive)

### 📱 Mobile Optimization
- Optimized for warehouse tablets (768px+)
- Touch-friendly interface
- Offline capability with service workers
- Quick action buttons for common tasks

### 🔗 API Endpoints
- Dashboard: http://localhost:5000/dashboard
- Real-time data: WebSocket connection
- OCR Processing: /ocr/process
- Inventory API: /api/inventory
- ML Predictions: /api/ml/predict

### 🐳 Docker Services
- web: Flask application (Port 5000)
- redis: Cache system (Port 6379)
- postgres: Database (Port 5432)
- deposito: Inventory service (Port 8000)
- negocio: Business logic (Port 8001)
- ml: ML predictions (Port 8002)

### 📊 Argentine Retail Context
- ARS currency formatting
- 4.5% monthly inflation calculations
- CUIT validation for suppliers
- Buenos Aires timezone (UTC-3)

### 🛠️ Troubleshooting
1. **Port conflicts:** Change ports in docker-compose.yml
2. **Database issues:** Check PostgreSQL logs with `docker logs postgres`
3. **Redis connection:** Verify Redis service with `docker ps`
4. **API integration:** Ensure backend services are running

### 📈 Performance Optimizations
- Redis caching with smart invalidation
- Lazy loading for dashboard components
- Compressed static assets
- Database query optimization
- WebSocket connection pooling

### 🔒 Security Features
- User authentication system
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure headers configuration

### 📚 Additional Resources
- Full documentation in README.md
- API documentation in /docs
- Development guide in /dev-guide.md
- Testing instructions in /tests/README.md
