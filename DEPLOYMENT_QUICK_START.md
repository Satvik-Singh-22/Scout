# 🚀 SCOUT DEPLOYMENT - QUICK REFERENCE

> **Your project is production-ready. Follow these exact steps to deploy both services.**

---

## ⏱️ Total Time: ~20 minutes

---

## STEP 1: Verify GitHub (2 min)

```bash
cd "c:\Users\gupta\Desktop\Natwest Final\Scout"
git status
git log --oneline -n 3
git push origin main  # Ensure latest code is pushed
```

**Expected:** 
- ✅ "nothing to commit"
- ✅ Recent commits visible
- ✅ Successfully pushed

---

## STEP 2: DEPLOY BACKEND on Render (8 min)

### A. Create Render Account
- Go to: https://render.com
- Click "Sign up with GitHub"
- Authorize GitHub access
- Create account

### B. Create Web Service
1. Click **"New"** → **"Web Service"**
2. Click **"Build and deploy from Git repository"**
3. Search: `Scout` (or your repo name)
4. **Click "Connect"** next to your repository
5. Fill form:
   - **Name:** `scout-backend`
   - **Root Directory:** `src/backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** (Leave empty - using render.yaml)
   - **Python Version:** `3.11`

### C. Add Environment Variables
Click **"Add Environment Variable"** for each:

```
DATABASE_URL          → [Your PostgreSQL URL]
GROQ_API_KEY          → [Your API key]
RESEND_API_KEY        → [Your API key]
JWT_SECRET            → [Generate: e.g., "abc123xyz789secret"]
CORS_ORIGINS          → https://yourdomain.vercel.app
```

⚠️ **IMPORTANT:** Leave empty for now, get from your actual services/config

### D. Deploy
- Click **"Create Web Service"**
- ⏱️ Wait 5-10 minutes for deployment
- ✅ When done, copy the URL at top: `https://scout-backend-xxxxx.onrender.com`
- 📌 **SAVE THIS URL**

### E. Verify Backend
```bash
# In browser, visit:
https://scout-backend-xxxxx.onrender.com/health

# Expected: {"status": "ok"} or 404 (either is fine, means it's running)
```

---

## STEP 3: DEPLOY FRONTEND on Vercel (5 min)

### A. Create Vercel Account
- Go to: https://vercel.com
- Click "Sign up with GitHub"
- Authorize GitHub access
- Create account

### B. Import Project
1. Click **"New Project"**
2. Click **"Import Git Repository"**
3. Search: `Scout` (or your repo name)
4. **Click "Import"**

### C. Configure Project
1. **Framework Preset:** Should auto-detect "Next.js" ✅
2. **Root Directory:** Click "Edit"
   - Enter: `src/frontend`
   - Click "Save"
3. **Environment Variables:** Click "Edit"
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://scout-backend-xxxxx.onrender.com` (from Step 2)
   - Click "Save"

### D. Deploy
- Click **"Deploy"**
- ⏱️ Wait 2-5 minutes
- ✅ When done, copy the URL: `https://scout-xxxxx.vercel.app`
- 📌 **SAVE THIS URL**

---

## STEP 4: Connect Backend to Frontend (2 min)

### Update Backend CORS

1. Go to Render Dashboard → Your Service (`scout-backend`)
2. Click **"Environment"**
3. Find `CORS_ORIGINS` variable
4. **Update to:** `https://scout-xxxxx.vercel.app` (your Vercel URL)
5. Click **"Save"**
6. Wait 1-2 minutes for service to restart ✅

---

## STEP 5: Test Deployment (3 min)

1. **Visit frontend:**
   ```
   https://scout-xxxxx.vercel.app
   ```
   
2. **Open browser DevTools** (F12)
   - Go to "Network" tab
   
3. **Try making an API call**
   - Log in or perform any action that calls backend
   
4. **Check Network tab:**
   - ✅ Requests to `scout-backend-xxxxx.onrender.com` should be **200 OK**
   - ❌ No **red CORS errors**
   - ❌ No **404 errors**

5. **If all green:** 🎉 **DEPLOYMENT SUCCESSFUL!**

---

## ❌ TROUBLESHOOTING

### Backend deployment stuck/failing:
```
→ Check Render Logs: Dashboard → Logs tab
→ Common issue: Missing environment variables
→ Solution: Add all DATABASE_URL, API keys, etc.
```

### Frontend shows blank page:
```
→ Check Vercel Logs: Dashboard → Deployments → click deployment → Logs
→ Common issue: Root Directory not set to src/frontend
→ Solution: Check Settings → Root Directory = src/frontend
```

### Cannot connect to backend (CORS error):
```
→ Backend CORS_ORIGINS doesn't match your Vercel URL
→ Solution: Update CORS_ORIGINS in Render to exactly match Vercel URL
→ Render restarts automatically after env var change
```

### 404 when visiting backend /health:
```
→ Render backend might not have /health endpoint
→ That's OK! Means server is running
→ More important: Can frontend call backend API?
```

### Deployment still failing?
```
1. Check platform-specific logs (Render Logs / Vercel Logs)
2. Look for the actual error message
3. Google the exact error
4. Common causes:
   - Missing/wrong environment variables
   - Python dependency conflicts
   - Root directory misconfigured
   - GitHub repo not public
```

---

## 📊 FINAL STATUS CHECK

**After all steps, verify:**

| ✅ | Item | Check |
|----|------|-------|
| ✅ | Backend running | https://scout-backend-xxxxx.onrender.com (should load) |
| ✅ | Frontend running | https://scout-xxxxx.vercel.app (should load) |
| ✅ | Connection works | Open DevTools → Network → make API call → no errors |
| ✅ | CORS configured | Backend can reach frontend, frontend can reach backend |
| ✅ | Auto-deploy enabled | Push to GitHub → both platforms auto-deploy |

---

## 🔄 FUTURE UPDATES

From now on, just:

```bash
git add .
git commit -m "Update description"
git push origin main
```

Both Vercel and Render automatically deploy on push to main! 🚀

---

## 📞 QUICK LINKS

| Platform | Link | Dashboard |
|----------|------|-----------|
| **Vercel** | https://vercel.com | Manage frontend |
| **Render** | https://render.com | Manage backend |
| **GitHub** | https://github.com | Manage code |

---

## 💾 YOUR DEPLOYMENT URLS (Save These!)

```
Frontend:  https://scout-xxxxx.vercel.app
Backend:   https://scout-backend-xxxxx.onrender.com
```

**Total Time from start to live:** 20-25 minutes 🎉

---

*For detailed explanations, see DEPLOYMENT_GUIDE.md*
*For checklist, see DEPLOYMENT_CHECKLIST.md*
