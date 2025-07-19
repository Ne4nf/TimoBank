# Render Environment Variables Setup Guide

## Required Environment Variables for TimoBanking Service:

### Database Configuration
DATABASE_URL=postgresql://tuthuc14:TOnGcTWIWuZP0CoDQ9QUH1yTRPCAd0NO@dpg-d1tu223ipnbc73con960-a.oregon-postgres.render.com/timo_banking

POSTGRES_HOST=dpg-d1tu223ipnbc73con960-a.oregon-postgres.render.com
POSTGRES_DB=timo_banking
POSTGRES_USER=tuthuc14
POSTGRES_PASSWORD=TOnGcTWIWuZP0CoDQ9QUH1yTRPCAd0NO
POSTGRES_PORT=5432

### API Configuration
API_HOST=0.0.0.0
PORT=10000
DEBUG=false

### Security
SECRET_KEY=timo-banking-production-secret-2024-render-v2
JWT_SECRET=timo-banking-jwt-production-secret-2024-render-v2

### Frontend CORS
FRONTEND_URL=https://timo-banking.vercel.app

### Monitoring
ENABLE_MONITORING=true
ALERT_EMAIL=admin@timobank.vn

### Compliance
REGULATORY_MODE=2345_QD_NHNN_2023
ENABLE_AUDIT_TRAIL=true
RETENTION_DAYS=2555

## Render Settings:
- Root Directory: (leave empty)
- Dockerfile Path: ./Dockerfile
- Docker Command: (leave empty - use CMD from Dockerfile)
- Auto-Deploy: On Commit
