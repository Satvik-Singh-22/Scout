# Deployment Guide: Scout Project to Vercel & Render

## Project Structure
```
scout/
├── src/
│   ├── frontend/       (Next.js app → Vercel)
│   └── backend/        (Python Flask/FastAPI → Render)
└── (pushed to GitHub main branch)
```

---

## PART 1: DEPLOY FRONTEND TO VERCEL

### Step 1: Prepare Your Frontend for Vercel
1. Navigate to your `src/frontend` folder
2. Verify you have:
   - `package.json` ✓
   - `next.config.mjs` ✓
   - `tsconfig.json` ✓
   - `.gitignore` (should exclude `node_modules`, `.next`)

3. Commit and push any remaining changes:
   ```bash
   git add .
   git commit -m "Final frontend build configuration"
   git push origin main
   ```

### Step 2: Create Vercel Project from GitHub
1. Go to [vercel.com](https://vercel.com)
2. **Sign in or create account** (you can use GitHub OAuth for easy login)
3. Click **"Add New"** → **"Project"**
4. Click **"Import Git Repository"**
5. Search and select your **Scout repository**
6. Click **"Import"**

### Step 3: Configure Vercel Project Settings
1. After import, you'll see the **Project Configuration** page

2. **Root Directory Configuration:**
   - Find the **"Root Directory"** field
   - Click **"Edit"** (or it might say **"Configure"**)
   - Enter: `src/frontend`
   - Click **"Save"**

3. **Environment Variables (if any):**
   - Scroll to **"Environment Variables"**
   - Add any `.env` variables needed by your frontend:
     - Example: `NEXT_PUBLIC_API_URL` (if your frontend calls the backend)
     - Set the backend URL to your Render deployment URL (you'll get this after deploying backend)
   - For now, you can add placeholder values and update later

4. **Build Settings (usually auto-detected):**
   - Build Command: `npm run build` (should auto-detect)
   - Output Directory: `.next` (should auto-detect)
   - Leave as default if correct

### Step 4: Deploy Frontend
1. Click **"Deploy"** button
2. Vercel will:
   - Clone your repository
   - Navigate to `src/frontend`
   - Run `npm install`
   - Run `npm run build`
   - Deploy your Next.js app
3. Wait for deployment to complete (usually 2-5 minutes)
4. You'll get a URL like: `https://scout-xxxxx.vercel.app`
5. **Save this URL** - you'll need it for backend configuration

### Step 5: Update Frontend Environment Variables (after backend deployment)
1. Go to your Vercel project dashboard
2. Go to **Settings** → **Environment Variables**
3. Update `NEXT_PUBLIC_API_URL` with your Render backend URL
4. Vercel will automatically redeploy with new environment variables

---

## PART 2: DEPLOY BACKEND TO RENDER

### Step 1: Prepare Your Backend for Render
1. Navigate to `src/backend` folder
2. Verify you have:
   - `requirements.txt` ✓ (with all dependencies)
   - `main.py` (your FastAPI/Flask entry point) ✓
   - `render.yaml` (Render configuration) ✓

3. **Create/Update `render.yaml` in `src/backend/`:**
   ```yaml
   services:
     - type: web
       name: scout-backend
       runtime: python311
       buildCommand: "pip install -r requirements.txt"
       startCommand: "python main.py"
       envVars:
         - key: PYTHON_VERSION
           value: 3.11
   ```

4. **Verify `main.py` structure:**
   - Ensure it starts the server on `0.0.0.0:${PORT}` (Render uses PORT env var)
   - Example:
     ```python
     if __name__ == "__main__":
         import os
         port = int(os.getenv("PORT", 8000))
         uvicorn.run(app, host="0.0.0.0", port=port)
     ```

5. **Update `requirements.txt`:**
   ```bash
   cd src/backend
   pip freeze > requirements.txt
   ```

6. Commit and push:
   ```bash
   git add src/backend/requirements.txt src/backend/render.yaml
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

### Step 2: Create Render Project from GitHub
1. Go to [render.com](https://render.com)
2. **Sign in or create account** (use GitHub OAuth)
3. Click **"New"** → **"Web Service"**
4. Select **"Build and deploy from a Git repository"**
5. Search and select your **Scout repository**
6. Click **"Connect"**

### Step 3: Configure Render Service
1. **Service Name:**
   - Name: `scout-backend`

2. **Root Directory/Start Command:**
   - Find **"Root Directory"** option
   - Enter: `src/backend`
   - Leave "Start Command" empty if you've set it in `render.yaml`
   - Or set manually: `python main.py`

3. **Environment:**
   - Python Version: `3.11` (or your preferred version)
   - Runtime: Ensure it's set to Python

4. **Environment Variables:**
   - Click **"Add Environment Variable"**
   - Add any variables your backend needs:
     - `DATABASE_URL` (if using database)
     - `CORS_ORIGINS` (set to your Vercel frontend URL)
     - `API_KEY`, `SECRET_KEY`, etc.
   - Example for CORS:
     ```
     CORS_ORIGINS=https://scout-xxxxx.vercel.app
     ```

5. **Build Settings:**
   - Build Command: Leave empty or `pip install -r requirements.txt`
   - Start Command: Leave empty (using `render.yaml`) or `python main.py`

### Step 4: Deploy Backend
1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Navigate to `src/backend`
   - Install dependencies from `requirements.txt`
   - Start your application
3. Wait for deployment (usually 5-10 minutes)
4. You'll get a URL like: `https://scout-backend-xxxxx.onrender.com`
5. **Save this URL** - update your frontend with this

### Step 5: Verify Backend is Running
1. Go to your Render service dashboard
2. Check the **Logs** tab - should show no errors
3. Try accessing a health check endpoint:
   ```bash
   curl https://scout-backend-xxxxx.onrender.com/health
   ```

---

## PART 3: CONNECT FRONTEND TO BACKEND

### After Both Are Deployed:

1. **Update Frontend Environment Variables in Vercel:**
   - Go to Vercel Dashboard → Your Project → **Settings** → **Environment Variables**
   - Add/Update: `NEXT_PUBLIC_API_URL=https://scout-backend-xxxxx.onrender.com`
   - Save - Vercel will redeploy automatically

2. **Update Backend Environment Variables in Render (if needed):**
   - Go to Render Dashboard → Your Service → **Environment**
   - Add/Update: `CORS_ORIGINS=https://scout-xxxxx.vercel.app`
   - Save - Render will restart the service

3. **Test the Connection:**
   - Visit your Vercel frontend URL
   - Make a test API call to verify backend communication
   - Check browser console and network tab for any CORS issues

---

## PART 4: CONFIGURE CONTINUOUS DEPLOYMENT

### Vercel (Auto-enabled):
- Every push to `main` branch automatically deploys
- You can configure this in **Settings** → **Git** → **Deploy on push**

### Render (Auto-enabled):
- Every push to `main` branch automatically deploys
- Watch the **Events** tab on dashboard for deployment status

---

## TROUBLESHOOTING

### Vercel Frontend Issues:
```
Issue: Build fails
→ Check build logs in Vercel dashboard
→ Verify Root Directory is set to `src/frontend`
→ Ensure all dependencies in package.json are installable
```

```
Issue: Cannot connect to backend
→ Check NEXT_PUBLIC_API_URL environment variable
→ Verify backend CORS_ORIGINS includes your Vercel URL
→ Check browser network tab for CORS errors
```

### Render Backend Issues:
```
Issue: Service crashes after deploy
→ Check Logs in Render dashboard
→ Verify main.py listens on 0.0.0.0:${PORT}
→ Check requirements.txt has all dependencies
```

```
Issue: Port not available
→ Ensure main.py uses PORT environment variable
→ Render assigns dynamic port, don't hardcode 8000
```

---

## QUICK REFERENCE: Deployment URLs

After successful deployment:

| Service | Platform | Type | URL |
|---------|----------|------|-----|
| Frontend | Vercel | Next.js | `https://scout-xxxxx.vercel.app` |
| Backend | Render | Python | `https://scout-backend-xxxxx.onrender.com` |

---

## Optional: Custom Domains

**Add Custom Domain to Vercel:**
1. Settings → Domains
2. Add your domain
3. Follow DNS configuration steps

**Add Custom Domain to Render:**
1. Settings → Custom Domain
2. Add your domain
3. Follow DNS configuration steps

---

## Summary of Changes Needed Before Deploying

✅ **Backend (`src/backend/`):**
- [ ] `render.yaml` created/updated
- [ ] `main.py` configured for PORT environment variable
- [ ] `requirements.txt` up-to-date
- [ ] All files committed and pushed to GitHub

✅ **Frontend (`src/frontend/`):**
- [ ] No root directory changes needed (stays in `src/frontend`)
- [ ] All files committed and pushed to GitHub
- [ ] Environment variable support added (if needed)

✅ **GitHub:**
- [ ] All changes pushed to `main` branch
- [ ] Repository is public (or Vercel/Render has access)
