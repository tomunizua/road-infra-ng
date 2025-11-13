# 🚀 RoadWatch Nigeria - Deployment Guide

This guide covers deploying your Flask backend + HTML/CSS/JS frontend application.

## 📋 Deployment Architecture

**Recommended Setup:**
- **Frontend**: Vercel (Static HTML/CSS/JS)
- **Backend**: Render or Railway (Flask Python API)

---

## 🎯 Option 1: Vercel + Render (RECOMMENDED)

### Part A: Deploy Backend on Render

1. **Create a Render Account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     ```
     Name: roadwatch-backend
     Region: Ohio (or closest to you)
     Branch: main
     Root Directory: (leave blank)
     Runtime: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: python backend/integrated_backend.py
     ```

3. **Set Environment Variables**
   ```
   PYTHON_VERSION=3.11.0
   FLASK_ENV=production
   PORT=10000
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Copy your backend URL: `https://roadwatch-backend.onrender.com`

5. **Update CORS in Backend**
   - Open `backend/integrated_backend.py`
   - Find the CORS configuration (around line 48)
   - Update to include your Vercel domain:
   ```python
   CORS(app, resources={
       r"/api/*": {
           "origins": [
               "http://localhost:5500",
               "http://127.0.0.1:5500",
               "https://your-vercel-app.vercel.app",  # Add your Vercel URL
               "https://roadwatch-nigeria.vercel.app"  # Your custom domain
           ],
           ...
       }
   })
   ```
   - Commit and push changes

---

### Part B: Deploy Frontend on Vercel

1. **Update Frontend API Configuration**
   - Open `frontend/config.js`
   - Replace `'https://your-backend-url-here.onrender.com'` with your actual Render URL:
   ```javascript
   return window.ENV_API_URL || 'https://roadwatch-backend.onrender.com';
   ```

2. **Add Config Script to HTML Files**
   - Open `frontend/citizen_portal.html`
   - Add BEFORE other script tags:
   ```html
   <script src="config.js"></script>
   ```

   - Open `frontend/admin.html`
   - Add BEFORE other script tags:
   ```html
   <script src="config.js"></script>
   ```

3. **Update API Calls in JavaScript**
   - In `citizen_portal.js` and `admin.js`
   - Replace all `'http://localhost:5000'` with `API_BASE_URL`
   - Example:
   ```javascript
   // OLD:
   const response = await fetch('http://localhost:5000/api/submit-report', {

   // NEW:
   const response = await fetch(`${API_BASE_URL}/api/submit-report`, {
   ```

4. **Deploy to Vercel**
   - Install Vercel CLI: `npm install -g vercel`
   - Login: `vercel login`
   - Deploy: `vercel`
   - Follow prompts:
     ```
     Set up and deploy? Y
     Which scope? [Your account]
     Link to existing project? N
     Project name? roadwatch-nigeria
     In which directory is your code located? ./
     Want to override settings? N
     ```
   - Your app will be deployed to: `https://roadwatch-nigeria.vercel.app`

5. **Set Custom Domain (Optional)**
   - In Vercel dashboard → Settings → Domains
   - Add your custom domain

---

## 🎯 Option 2: Railway (Alternative Backend)

### Deploy Backend on Railway

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Deploy from GitHub**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python

3. **Configure**
   - Railway uses `railway.json` (already created)
   - Set environment variables:
     ```
     PYTHON_VERSION=3.11
     PORT=5000
     FLASK_ENV=production
     ```

4. **Deploy**
   - Railway auto-deploys
   - Get your URL: `https://roadwatch-backend.railway.app`
   - Update frontend config with this URL

---

## 🎯 Option 3: All-in-One Vercel (Advanced)

If you want everything on Vercel, you need to convert backend to serverless functions.

**NOT RECOMMENDED** for this project because:
- Your app uses SQLite (not ideal for serverless)
- Large ML models won't work well in serverless
- Requires significant restructuring

---

## ✅ Post-Deployment Checklist

### Backend
- [ ] Backend is accessible at `/api/health`
- [ ] Database tables created automatically
- [ ] CORS allows your frontend domain
- [ ] File uploads work (if using persistent storage)

### Frontend
- [ ] API calls point to production backend
- [ ] Citizen portal loads correctly
- [ ] Admin dashboard loads correctly
- [ ] Forms submit successfully
- [ ] Images upload and display

### Testing
- [ ] Test report submission end-to-end
- [ ] Test report tracking
- [ ] Test admin dashboard
- [ ] Test on mobile devices

---

## 🔧 Troubleshooting

### CORS Errors
**Problem**: "Access to fetch at ... has been blocked by CORS policy"

**Solution**: Update `backend/integrated_backend.py` CORS origins to include your Vercel URL

### API Connection Failed
**Problem**: Frontend can't connect to backend

**Solution**:
1. Check `frontend/config.js` has correct backend URL
2. Verify backend is running (visit `/api/health`)
3. Check browser console for actual error

### Database Not Persisting
**Problem**: Data disappears after backend restarts

**Solution**: On Render/Railway, use PostgreSQL instead of SQLite:
1. Add PostgreSQL database
2. Update `database.py` to use PostgreSQL URI
3. Install `psycopg2` in requirements.txt

### Large Files / AI Models
**Problem**: Deployment fails due to size limits

**Solution**:
1. Store models in external storage (S3, Google Cloud Storage)
2. Download models on first run
3. Or use model APIs instead of local models

---

## 📊 Environment Variables Reference

### Backend (Render/Railway)
```bash
PYTHON_VERSION=3.11.0
FLASK_ENV=production
PORT=10000  # Render uses 10000, Railway auto-assigns
DATABASE_URL=your_postgres_url  # Optional: for PostgreSQL
```

### Frontend (Vercel)
```bash
ENV_API_URL=https://your-backend.onrender.com
```

---

## 🔒 Security Considerations

1. **API Keys**: Store in environment variables, never in code
2. **Database**: Use PostgreSQL for production, not SQLite
3. **HTTPS**: Both Vercel and Render provide free SSL
4. **CORS**: Only allow your specific domains
5. **Authentication**: Add admin authentication for production

---

## 💰 Cost Breakdown

### Free Tier
- **Vercel**: Free for personal projects
- **Render**: Free tier available (sleeps after 15 min inactivity)
- **Railway**: $5 credit/month free

### Paid Options
- **Render**: $7/month (always on, better performance)
- **Railway**: Pay as you go (~$5-10/month)
- **Vercel Pro**: $20/month (if needed)

---

## 📝 Notes

- **First deployment** takes longer (5-10 minutes)
- **Subsequent deployments** are faster (1-2 minutes)
- **Free tier backends** may sleep after inactivity (30s wake-up time)
- **Database**: Consider PostgreSQL for production (better than SQLite)
- **File storage**: Use cloud storage (S3, Cloudinary) for uploaded images

---

## 🆘 Need Help?

1. Check backend logs in Render/Railway dashboard
2. Check browser console for frontend errors
3. Verify environment variables are set correctly
4. Test API endpoints directly using Postman/curl

---

## 🎉 Success!

Once deployed:
- Frontend: `https://your-app.vercel.app`
- Backend API: `https://your-backend.onrender.com/api`
- Admin: `https://your-app.vercel.app/admin`

Happy deploying! 🚀
