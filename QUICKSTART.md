# VIMS Backend - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Option 1: Docker (Easiest - Recommended)

```powershell
# 1. Navigate to backend directory
cd C:\Users\tayey\360ground\VIMS\vims-backend

# 2. Start all services
docker-compose up -d

# 3. Wait for services to be healthy (30 seconds)
Start-Sleep -Seconds 30

# 4. Run database migrations
docker-compose exec web1 python manage.py migrate

# 5. Create admin user
docker-compose exec web1 python manage.py createsuperuser
# Follow prompts to create username/password

# 6. Access the application
# API: http://localhost/api/
# Admin: http://localhost/admin/
# Health: http://localhost/health/
```

**Done! Your backend is running with:**
- ✅ 3 Django web servers (load balanced)
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Celery workers for background tasks
- ✅ Nginx load balancer

---

### Option 2: Local Development (Without Docker)

#### Prerequisites
```powershell
# Install PostgreSQL
# Download from: https://www.postgresql.org/download/windows/

# Install Redis
# Download from: https://github.com/microsoftarchive/redis/releases

# Or use WSL2 for Linux tools
```

#### Setup Steps

```powershell
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up database
# Using psql:
psql -U postgres
CREATE DATABASE vims_db;
CREATE USER vims_user WITH PASSWORD 'vims_password';
GRANT ALL PRIVILEGES ON DATABASE vims_db TO vims_user;
\q

# 4. Configure environment
# Edit .env file with your database credentials

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Start development server
python manage.py runserver 0.0.0.0:8000

# 8. In separate terminals:
# Start Celery worker
celery -A vims worker -l info

# Start Celery beat (scheduler)
celery -A vims beat -l info
```

---

## 🧪 Test the API

### 1. Health Check
```powershell
curl http://localhost/health/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "VIMS Backend"
}
```

### 2. Login

```powershell
curl -X POST http://localhost/api/auth/login/ `
  -H "Content-Type: application/json" `
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Expected response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLC...",
  "user": {
    "user_id": "admin-001",
    "username": "superadmin",
    "full_name": "Super Administrator",
    ...
  }
}
```

### 3. Get Users (Authenticated)

```powershell
# Save token from login response
$token = "YOUR_ACCESS_TOKEN"

curl -H "Authorization: Bearer $token" `
  http://localhost/api/users/
```

---

## 📊 View Logs

### Docker Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web1
docker-compose logs -f celery_worker
docker-compose logs -f db
```

### Local Logs
```powershell
# Check logs folder
cat logs/vims.log
```

---

## 🛠️ Useful Commands

### Docker Commands
```powershell
# Stop all services
docker-compose down

# Restart service
docker-compose restart web1

# Rebuild after code changes
docker-compose up -d --build

# Run Django command
docker-compose exec web1 python manage.py [command]

# Access Django shell
docker-compose exec web1 python manage.py shell

# Access database
docker-compose exec db psql -U vims_user -d vims_db
```

### Django Management Commands
```powershell
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
pytest
```

---

## 🔧 Common Issues & Fixes

### Port Already in Use
```powershell
# Check what's using port 80
netstat -ano | findstr :80

# Kill the process
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
# Change "80:80" to "8080:80"
```

### Database Connection Error
```powershell
# Check if PostgreSQL is running
docker-compose ps db

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Redis Connection Error
```powershell
# Check if Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Migrations Fail
```powershell
# Reset migrations (DANGER: Deletes data!)
docker-compose exec web1 python manage.py migrate --fake [app_name] zero
docker-compose exec web1 python manage.py migrate [app_name]

# Or drop and recreate database
docker-compose down -v  # Removes volumes!
docker-compose up -d
docker-compose exec web1 python manage.py migrate
```

---

## 📱 Connect Frontend

### Update Frontend .env
```env
# In vims-admin-portal/.env
VITE_API_BASE_URL=http://localhost/api
VITE_WS_URL=ws://localhost/ws

# In vims-client/.env (Electron app)
REACT_APP_API_BASE_URL=http://localhost/api
```

### Test API Connection
```javascript
// In your frontend
const response = await fetch('http://localhost/api/health/');
const data = await response.json();
console.log(data); // { status: 'healthy', service: 'VIMS Backend' }
```

---

## 🎯 Next Steps

1. ✅ Backend is running!
2. 📖 Read [README.md](README.md) for full documentation
3. 🔐 Set up roles and permissions
4. 📊 Create test data
5. 🔌 Connect your frontend applications
6. 🚀 Deploy to production (see [README.md](README.md#deployment))

---

## 💡 Tips

- Use **Docker** for consistency across team members
- Run **migrations** after pulling new code
- Check **logs** when things don't work
- Use **Django admin** (`/admin/`) for quick data viewing
- Run **tests** before committing code
- Keep **.env** file secure (never commit!)

---

**Need Help?** Check [README.md](README.md#troubleshooting) or open an issue!





