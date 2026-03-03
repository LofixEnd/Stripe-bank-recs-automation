# Stripe Reconciliation Accelerator - Deployment Guide

## Quick Start (5 minutes)

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python app.py

# 2a. (optional) create the first administrative user
python create_user.py

# 3. Open browser
# Navigate to: http://localhost:5000
```

## Render.com Deployment

### Prerequisites
- Render.com account (free tier available)
- GitHub/GitLab repository with your code

### Step-by-Step Deployment

#### 1. Push Code to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

#### 2. Create Render Web Service
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Fill in the following:

| Field | Value |
|-------|-------|
| **Name** | stripe-reconciliation-accelerator |
| **Environment** | Python 3 |
| **Region** | Choose closest to users |
| **Branch** | main |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

#### 3. Set Environment Variables
In the Render dashboard, add:
- `FLASK_ENV` = `production`
- `SECRET_KEY` = `generate-a-random-string`

#### 4. Deploy
Click "Create Web Service" - deployment begins automatically.

### Access Your App
Once deployed, Render provides a URL:
```
https://stripe-reconciliation-accelerator.onrender.com
```

## Docker Deployment

### Build Docker Image
```bash
docker build -t stripe-recon:latest .
docker run -p 5000:5000 stripe-recon:latest
```

### Deploy to Docker Registry
```bash
# Tag for DockerHub
docker tag stripe-recon:latest yourusername/stripe-recon:latest

# Push to registry
docker push yourusername/stripe-recon:latest
```

## Production Checklist

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (Render handles this automatically)
- [ ] Configure logging to external service
- [ ] Set up database for client management (SQLite is used by default)
- [ ] Create an administrator account (`python create_user.py`)
- [ ] Implement user authentication (Flask-Login)
- [ ] Configure email delivery for reports
- [ ] Set up monitoring and alerts
- [ ] Test with sample data
- [ ] Document client onboarding process

## Scaling Considerations

### For 100+ Concurrent Users
1. **Database Integration**: Replace in-memory storage
   ```python
   # Use PostgreSQL or similar
   DATABASE_URL=postgresql://user:pass@host/dbname
   ```

2. **File Storage**: Use S3 or similar
   ```python
   # AWS S3 for large files
   AWS_S3_BUCKET=your-bucket-name
   ```

3. **Task Queue**: Use Celery for async processing
   ```python
   # For large batch processing
   CELERY_BROKER_URL=redis://localhost:6379
   ```

4. **Email Service**: Configure SendGrid
   ```python
   # For automated report delivery
   SENDGRID_API_KEY=your-api-key
   ```

## Monitoring

### Render.com Monitoring
- Access logs via Render dashboard
- Set up email alerts for errors
- Monitor CPU and memory usage

### Custom Monitoring
Add to `app.py`:
```python
import logging

# Configure to external service
logging.basicConfig(
    handlers=[
        logging.handlers.HTTPHandler(
            'logs.example.com',
            '/logs'
        )
    ]
)
```

## Troubleshooting Deployments

### Issue: Build Fails
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**: Ensure `requirements.txt` is in root directory

### Issue: Application Crashes
Check Render logs for detailed errors:
```bash
# View live logs
# Render Dashboard → Logs tab
```

### Issue: Static Files Not Loading
Ensure `FLASK_ENV=production` is set correctly

## Database Integration (Future)

When ready to add persistent storage:

```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, DateTime

db = SQLAlchemy(app)

class Client(db.Model):
    id = Column(String(50), primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
```

## API Endpoints for External Systems

Future integration with Zapier, Make, or custom webhooks:

```
POST /api/webhooks/stripe
- Receive real-time settlement notifications

GET /api/reports/<client_slug>
- Retrieve historical reconciliation reports

POST /api/schedule/<client_slug>
- Schedule automated daily reconciliations
```

## Support & Documentation

- **Live Demo**: https://stripe-recon-demo.onrender.com
- **API Docs**: https://docs.striperecon.com
- **Email Support**: support@striperecon.com
