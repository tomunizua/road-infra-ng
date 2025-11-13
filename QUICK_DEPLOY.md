# ⚡ Quick Deploy Guide

## 🎯 Deploy in 15 Minutes

### Step 1: Deploy Backend (Render)

1. Go to https://render.com and sign in with GitHub
2. Click **"New +"** → **"Web Service"**
3. Select your **road-infra-ng** repository
4. Settings:
   - **Name**: `roadwatch-backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python backend/integrated_backend.py`
5. Click **"Create Web Service"**
6. **Copy your backend URL**: `https://roadwatch-backend.onrender.com`

---

### Step 2: Update Frontend Config

1. Open `frontend/config.js`
2. Replace the URL on line 14:
   ```javascript
   return window.ENV_API_URL || 'https://roadwatch-backend.onrender.com';
   ```
   (Use your actual Render URL from Step 1)

3. **Commit and push changes**:
   ```bash
   git add frontend/config.js
   git commit -m "Update API URL for production"
   git push
   ```

---

### Step 3: Deploy Frontend (Vercel)

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Deploy:
   ```bash
   vercel
   ```

4. Answer prompts:
   - Set up and deploy? **Y**
   - Link to existing project? **N**
   - Project name? **roadwatch-nigeria**
   - Deploy? **Y**

5. **Copy your frontend URL**: `https://roadwatch-nigeria.vercel.app`

---

### Step 4: Update Backend CORS

1. Open `backend/integrated_backend.py`
2. Find line 48 (CORS configuration)
3. Add your Vercel URL:
   ```python
   "origins": [
       "http://localhost:5500",
       "http://127.0.0.1:5500",
       "https://roadwatch-nigeria.vercel.app",  # ADD THIS
   ],
   ```

4. **Commit and push** (Render will auto-deploy):
   ```bash
   git add backend/integrated_backend.py
   git commit -m "Update CORS for production"
   git push
   ```

---

### Step 5: Add Config Script to HTML

1. Open `frontend/citizen_portal.html`
2. Add **BEFORE** line 850 (before existing scripts):
   ```html
   <script src="config.js"></script>
   ```

3. Open `frontend/admin.html`
4. Add **BEFORE** line 866 (before existing scripts):
   ```html
   <script src="config.js"></script>
   ```

5. **Commit and deploy**:
   ```bash
   git add frontend/
   git commit -m "Add config script"
   git push
   vercel --prod
   ```

---

## ✅ You're Live!

- **Frontend**: https://roadwatch-nigeria.vercel.app
- **Admin**: https://roadwatch-nigeria.vercel.app/admin
- **API**: https://roadwatch-backend.onrender.com/api

---

## 🧪 Test Your Deployment

1. Visit your frontend URL
2. Try submitting a test report
3. Check if it appears in admin dashboard
4. Test tracking a report

---

## ⚠️ Common Issues

**"CORS Error"**
- Make sure you added Vercel URL to CORS in `integrated_backend.py`
- Push changes to GitHub (Render auto-redeploys)

**"API not responding"**
- Check Render logs: Render Dashboard → Logs
- Verify backend URL in `frontend/config.js`

**"Vercel shows 404"**
- Make sure `vercel.json` exists in root
- Redeploy: `vercel --prod`

---

Need more details? See `DEPLOYMENT.md`
