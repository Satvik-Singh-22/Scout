# Pre-Deployment Checklist for Scout

## ✅ VERIFIED: Your Project is Ready!

### Backend (`src/backend/`) - ✓ READY
- ✅ `render.yaml` properly configured with uvicorn
- ✅ `main.py` uses `$PORT` environment variable via uvicorn
- ✅ CORS middleware already set up (includes Vercel wildcard: `"https://*.vercel.app"`)
- ✅ Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- ✅ Health check endpoint: `/health` configured
- ✅ Environment variables template ready in render.yaml

### Frontend (`src/frontend/`) - ✓ READY
- ✅ `package.json` configured with build scripts
- ✅ API client in `lib/api-client.ts` uses `NEXT_PUBLIC_API_URL` env var
- ✅ Fallback to `http://localhost:8000` for development
- ✅ Next.js 14.2.3 (latest, production-ready)
- ✅ TypeScript configured
- ✅ All dependencies in package.json

---

## FINAL STEPS BEFORE DEPLOYMENT

### 1️⃣ Add Environment Variable Support to Frontend (OPTIONAL - if not done)

**File:** `src/frontend/.env.local` (for development only)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Do NOT commit `.env.local` to GitHub** (should be in `.gitignore`)

### 2️⃣ Verify All Code is Committed

Run in terminal:
```bash
cd c:\Users\gupta\Desktop\Natwest Final\Scout
git status
```

Should show:
```
nothing to commit, working tree clean
```

If not, commit everything:
```bash
git add .
git commit -m "Final deployment preparation"
git push origin main
```

### 3️⃣ Verify GitHub Repository

- Go to: https://github.com/yourusername/scout
- Verify:
  - ✓ Repository is **public** (or give Vercel/Render access)
  - ✓ Main branch has latest code
  - ✓ Folder structure visible: `/src/frontend` and `/src/backend`

---

## DEPLOYMENT ORDER (IMPORTANT!)

### Phase 1: Deploy Backend First ⏱️ (5-10 minutes)
**Why?** You need the backend URL to configure the frontend.

1. Go to [render.com](https://render.com)
2. Deploy from `src/backend` (see DEPLOYMENT_GUIDE.md Part 2)
3. **Note the URL**: `https://scout-backend-xxxxx.onrender.com`

### Phase 2: Deploy Frontend ⏱️ (2-5 minutes)
1. Go to [vercel.com](https://vercel.com)
2. Deploy from `src/frontend` (see DEPLOYMENT_GUIDE.md Part 1)
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://scout-backend-xxxxx.onrender.com`

### Phase 3: Test Connection ⏱️ (5 minutes)
1. Visit your Vercel frontend
2. Test API calls to backend
3. Check browser console for CORS errors
4. If errors, update backend CORS_ORIGINS in Render

---

## IMPORTANT ENVIRONMENT VARIABLES

### Render Backend (`src/backend`)
These will need values in Render dashboard:

```
DATABASE_URL          = [Your PostgreSQL connection string]
GROQ_API_KEY          = [Your GROQ API key]
RESEND_API_KEY        = [Your Resend email API key]
JWT_SECRET            = [Generate a strong random string]
JWT_ALGORITHM         = HS256 (already set)
JWT_EXPIRE_MINUTES    = 1440 (already set)
CHROMA_PERSIST_PATH   = ./chroma_data (already set)
PYTHON_VERSION        = 3.11.0 (already set)
```

### Vercel Frontend (`src/frontend`)
These will need values in Vercel dashboard:

```
NEXT_PUBLIC_API_URL   = https://scout-backend-xxxxx.onrender.com
```

---

## QUICK START: Deploy Now

### Step A: Terminal Commands (Verify Everything)
```bash
cd "c:\Users\gupta\Desktop\Natwest Final\Scout"

# Verify backend is ready
cd src/backend
cat requirements.txt | wc -l  # Should show count of dependencies
cat render.yaml | grep startCommand  # Should show uvicorn command

# Verify frontend is ready
cd ../frontend
cat package.json | grep "next"  # Should show Next.js version
cat lib/api-client.ts | grep "NEXT_PUBLIC_API_URL"  # Should show env var usage

# Verify GitHub
cd ../..
git log --oneline -3  # Should show recent commits
git branch -a  # Should show main branch
```

### Step B: Deploy Backend on Render
1. Visit https://render.com
2. Click "New" → "Web Service"
3. Select your Scout GitHub repository
4. Configure:
   - Root Directory: `src/backend`
   - Start Command: (leave empty - using render.yaml)
   - Add environment variables from above
5. Click "Create Web Service"
6. **Wait for deployment** - watch logs for errors
7. **Copy the URL** when deployment succeeds

### Step C: Deploy Frontend on Vercel
1. Visit https://vercel.com
2. Click "Add New" → "Project"
3. Select "Import Git Repository"
4. Configure:
   - Root Directory: `src/frontend`
   - Environment Variable: `NEXT_PUBLIC_API_URL=[backend-url-from-step-b]`
5. Click "Deploy"
6. **Wait for deployment** - should be faster than backend

### Step D: Test
1. Visit your Vercel URL
2. Try making an API request
3. Check browser DevTools → Network tab
4. If no CORS errors → Success! ✅

---

## TROUBLESHOOTING QUICK REFERENCE

| Issue | Solution |
|-------|----------|
| **"Root directory not found"** | Verify directory path in platform settings (should be `src/frontend` or `src/backend`) |
| **"Module not found" error** | Backend: Check `requirements.txt` has all dependencies. Frontend: Check `package.json` versions |
| **CORS errors in browser** | Update Render backend `CORS_ORIGINS` env var with your Vercel URL |
| **Backend won't start** | Check `main.py` has `--host 0.0.0.0 --port $PORT` in render.yaml startCommand |
| **"Port already in use"** | Render assigns PORT dynamically - main.py must not hardcode port |
| **Deployment stuck** | Check deployment logs in Vercel/Render dashboard - usually shows exact error |

---

## After Success: Set Up Auto-Updates

Both Vercel and Render support automatic deployments:

- **Vercel**: Automatically deploys on every push to main
- **Render**: Automatically deploys on every push to main

No additional config needed! Just push to GitHub and both platforms will auto-deploy.

---

## MONITORING & LOGS

### Vercel
- Dashboard → Your Project → **Deployments** tab
- Click any deployment to see build logs
- Settings → **Logs** for runtime logs

### Render
- Dashboard → Your Service → **Logs** tab
- Shows real-time logs
- Helpful for debugging API issues

---

## File Structure Verification

Before deploying, verify this exact structure on GitHub:

```
scout/                          (GitHub repo root)
├── .git/
├── .gitignore
├── README.md
├── requirements.txt             (root requirements)
├── DEPLOYMENT_GUIDE.md          (this file)
├── DEPLOYMENT_CHECKLIST.md
└── src/
    ├── backend/
    │   ├── main.py              ← Render looks here
    │   ├── requirements.txt
    │   ├── render.yaml          ← Render config
    │   ├── alembic.ini
    │   ├── agents/
    │   ├── api/
    │   ├── db/
    │   ├── services/
    │   ├── tests/
    │   └── vectorstore/
    │
    └── frontend/
        ├── package.json         ← Vercel looks here
        ├── next.config.mjs
        ├── tsconfig.json
        ├── tailwind.config.ts
        ├── app/
        ├── components/
        ├── lib/
        │   └── api-client.ts    ← Uses NEXT_PUBLIC_API_URL
        └── public/
```

✅ If your GitHub matches this structure → **You're ready to deploy!**

---

## FINAL SUMMARY

| Component | Platform | Config File | Status |
|-----------|----------|-------------|--------|
| Frontend | Vercel | `next.config.mjs` | ✅ Ready |
| Backend | Render | `render.yaml` | ✅ Ready |
| API Client | Both | `lib/api-client.ts` | ✅ Ready |
| Environment | Both | To be configured | ⏳ Ready when deployed |

**Total Expected Deployment Time:** 15-20 minutes

**Success Indicators:**
- ✅ Backend returns 200 on `/health`
- ✅ Frontend loads without CORS errors
- ✅ Frontend successfully calls backend API
- ✅ Can log in and use the application

---

## Next: See DEPLOYMENT_GUIDE.md for Step-by-Step Instructions
