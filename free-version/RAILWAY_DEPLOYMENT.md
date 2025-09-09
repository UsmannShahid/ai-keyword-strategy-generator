# 🚀 Railway Deployment Guide

## Quick Setup (5 minutes)

### 1. Create Railway Account
- Go to [railway.app](https://railway.app)
- Sign up with GitHub
- Get $5 free credits monthly

### 2. Deploy to Railway

#### Option A: One-Click Deploy
```bash
# From the free-version directory
railway login
railway link
railway up
```

#### Option B: GitHub Integration
1. Push your code to GitHub
2. Connect Railway to your GitHub repo
3. Railway will auto-deploy on every push

### 3. Add PostgreSQL Database
```bash
# Add Postgres addon
railway add postgresql

# Your DATABASE_URL will be automatically set
# No manual configuration needed!
```

### 4. Set Environment Variables
Go to your Railway project dashboard and add:
```
OPENAI_API_KEY=your_openai_key_here
ADMIN_KEY=your_admin_key_here
```

### 5. Deploy API
Your API will be available at:
```
https://your-app-name.up.railway.app
```

## Local Development with Railway DB

### 1. Get Database URL
```bash
railway run --service postgres env
# Copy the DATABASE_URL
```

### 2. Update Local .env
```bash
# In free-version/api/.env
DATABASE_URL=postgresql+asyncpg://postgres:password@...
```

### 3. Install Dependencies
```bash
cd free-version/api
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python core/init_db.py
```

### 5. Start Local Server
```bash
python -m uvicorn main:app --reload --port 8002
```

## Features Included

✅ **Query Storage**: All keyword searches stored in PostgreSQL  
✅ **Smart Caching**: 24h cache for keywords, 7d cache for briefs  
✅ **Usage Analytics**: Track user sessions and API usage  
✅ **Auto-scaling**: Railway handles traffic spikes automatically  
✅ **Zero-downtime**: Hot-reload and health checks included  

## Database Schema

### Tables Created:
- `keyword_queries` - Store all user searches
- `keyword_cache` - Cache keyword results (24h TTL)
- `content_briefs` - Store generated briefs
- `brief_cache` - Cache brief results (7d TTL)
- `user_sessions` - Track user activity

### Benefits:
- **Faster responses** - Cached results return instantly
- **Cost savings** - Reduced OpenAI API calls
- **Analytics** - Track popular keywords and user behavior
- **Reliability** - Fallback to cache if APIs fail

## Deployment Commands

```bash
# Deploy from free-version directory
cd free-version

# Login to Railway
railway login

# Create new project
railway init

# Add PostgreSQL
railway add postgresql

# Deploy
railway up

# View logs
railway logs

# Open deployed app
railway open
```

## Production Checklist

- [ ] Set `DATABASE_URL` environment variable
- [ ] Add `OPENAI_API_KEY` to Railway
- [ ] Set `ADMIN_KEY` for admin endpoints
- [ ] Update CORS origins to your frontend domain
- [ ] Enable Railway's built-in SSL
- [ ] Set up custom domain (optional)

## Cost Estimate

**Railway Free Tier:**
- $5/month credit included
- PostgreSQL: ~$1-2/month
- API hosting: ~$1-3/month
- **Total: $0-5/month** (covered by free credits)

**Scaling:**
- Automatic scaling based on usage
- Pay only for what you use
- Perfect for MVP and production

## Support

Railway provides:
- Built-in monitoring
- Automatic backups
- 99.9% uptime SLA
- Discord community support

Your keyword tool is now production-ready! 🎉