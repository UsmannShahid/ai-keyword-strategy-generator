# 🎯 Quick Wins Finder - Free Version

A simplified, single-page keyword research tool that helps you find low-competition keywords and generate content briefs in minutes.

## ✅ What This Version Includes

### 🆓 Free Version Features
- **Single-page linear workflow** - No complex navigation
- **Step-by-step process** - Onboarding → Input → Discovery → Brief → Export
- **Quick wins identification** - AI-powered low-competition keyword detection
- **Content brief generation** - GPT-3.5-turbo powered content strategies
- **Simple exports** - CSV keywords + Word/Google Docs briefs
- **No signup required** - Use immediately
- **Luxury design** - Gold accents and smooth animations

## 🚀 Quick Start

### 1. Start API Server
```bash
cd api
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8002
```

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3005
```

### 3. Test the Flow
1. Go to http://localhost:3005
2. Fill in business setup (saved automatically)
3. Enter seed keyword like "microphone"
4. Get quick wins and generate brief
5. Export results

## 📁 Project Structure

```
free-version/
├── frontend/          # Next.js app (~500 lines)
│   ├── src/app/       # Single-page application
│   └── package.json   # Dependencies
├── api/              # FastAPI (~200 lines)
│   ├── main.py       # 2 endpoints: keywords + brief
│   ├── core/         # Business logic
│   └── .env          # OpenAI API key
└── README.md         # This file
```

## 🎯 Linear 5-Step Workflow

1. **Setup** - Business niche, audience, location (saved locally)
2. **Input** - Seed keyword or competitor URL
3. **Discovery** - 10 keywords with quick-wins scoring
4. **Brief** - AI-generated content strategy
5. **Export** - CSV + Word/Google Docs downloads

## 🎨 Design Philosophy

- **Luxury minimalism** - Clean, elegant, uncluttered
- **Gold accents** (#D4AF37) with warm off-white (#FAFAF8)
- **Smooth animations** - Framer Motion transitions
- **Mobile-first** - Single-column layout works everywhere

## 🔧 Technical Stack

- **Frontend**: Next.js 15.5.2 with Tailwind CSS
- **Backend**: FastAPI with OpenAI GPT-3.5-turbo
- **Design**: shadcn/ui components with luxury styling
- **Animations**: Framer Motion for smooth transitions

## 🎯 Ready to Launch

This free version is **production ready** and follows the original workflow perfectly. It's 90% simpler than the complex version while delivering the core value proposition.

**Ready to launch today! 🚀**