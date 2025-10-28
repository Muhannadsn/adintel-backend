# AdIntel Startup Guide

Complete instructions for running the AdIntel frontend and backend servers.

---

## Quick Start (Recommended)

### Start Both Services at Once

```bash
# Kill any existing processes
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Start backend
cd /Users/muhannadsaad/Desktop/ad-intelligence/api && python3 main.py > /tmp/api.log 2>&1 &

# Wait for backend to start
sleep 2

# Start frontend
cd /Users/muhannadsaad/Desktop/adintel-frontend && npm run dev > /tmp/frontend.log 2>&1 &

# Done! Access at http://localhost:3000
echo "✓ Backend running on http://localhost:8001"
echo "✓ Frontend running on http://localhost:3000"
```

---

## Individual Service Startup

### Backend (FastAPI - Port 8001)

```bash
# Navigate to backend directory
cd /Users/muhannadsaad/Desktop/ad-intelligence

# Install Python dependencies (if needed)
pip3 install -r api/requirements.txt

# Start the API server
cd api
python3 main.py

# OR run in background with logging:
python3 main.py > /tmp/api.log 2>&1 &

# Verify it's running:
curl http://localhost:8001/
```

**Expected Response:**
```json
{
  "message": "AdIntel API is running",
  "version": "1.0.0",
  "endpoints": {
    "scrape": "/api/scrape",
    "analyze": "/api/analyze",
    "jobs": "/api/jobs/{job_id}",
    "competitors": "/api/competitors"
  }
}
```

---

### Frontend (Next.js - Port 3000)

```bash
# Navigate to frontend directory
cd /Users/muhannadsaad/Desktop/adintel-frontend

# Install Node dependencies (if needed)
npm install

# Start the development server
npm run dev

# OR run in background with logging:
npm run dev > /tmp/frontend.log 2>&1 &
```

**Access the app at:** http://localhost:3000

---

## Monitoring & Debugging

### Check Logs

```bash
# Backend logs
tail -f /tmp/api.log

# Frontend logs
tail -f /tmp/frontend.log

# View last 50 lines
tail -50 /tmp/api.log
tail -50 /tmp/frontend.log
```

### Check Running Processes

```bash
# Check backend (port 8001)
lsof -i:8001

# Check frontend (port 3000)
lsof -i:3000

# List all running processes
ps aux | grep -E "(uvicorn|python.*main.py|next-server)"
```

### Test Endpoints

```bash
# Test backend health
curl http://localhost:8001/

# Test competitors endpoint
curl http://localhost:8001/api/competitors

# Test insights endpoint
curl http://localhost:8001/api/insights/weekly
```

---

## Stop Services

### Stop All Services

```bash
# Kill backend
lsof -ti:8001 | xargs kill -9

# Kill frontend
lsof -ti:3000 | xargs kill -9
```

### Stop Individual Services

```bash
# Stop backend only
lsof -ti:8001 | xargs kill -9 2>/dev/null

# Stop frontend only
lsof -ti:3000 | xargs kill -9 2>/dev/null
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find and kill the process using port 8001
lsof -ti:8001 | xargs kill -9

# Find and kill the process using port 3000
lsof -ti:3000 | xargs kill -9
```

### Frontend Not Loading

1. Check if backend is running: `curl http://localhost:8001/`
2. Check frontend logs: `tail -f /tmp/frontend.log`
3. Restart frontend:
   ```bash
   lsof -ti:3000 | xargs kill -9
   cd /Users/muhannadsaad/Desktop/adintel-frontend && npm run dev
   ```

### Backend Not Responding

1. Check API logs: `tail -f /tmp/api.log`
2. Verify Python dependencies: `pip3 install -r api/requirements.txt`
3. Restart backend:
   ```bash
   lsof -ti:8001 | xargs kill -9
   cd /Users/muhannadsaad/Desktop/ad-intelligence/api && python3 main.py
   ```

### Cache/Build Issues

```bash
# Clear Next.js cache
cd /Users/muhannadsaad/Desktop/adintel-frontend
rm -rf .next
npm run dev

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

---

## Environment Variables

### Backend (.env)
Located in: `/Users/muhannadsaad/Desktop/ad-intelligence/.env`

```bash
# Add any required environment variables
ANTHROPIC_API_KEY=your_key_here
```

### Frontend (.env.local)
Located in: `/Users/muhannadsaad/Desktop/adintel-frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## Service URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs (if FastAPI auto-docs enabled)

---

## Development Workflow

1. Start both services using the Quick Start command
2. Make changes to code (auto-reloads enabled for both)
3. Monitor logs for errors
4. Stop services when done

**Happy developing!** 🚀
