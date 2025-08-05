# Vercel Deployment Guide

This guide shows how to deploy the Transistor Database web application to Vercel.

## 📁 Project Structure for Vercel

```
gui_web/
├── api/                    # Vercel serverless functions
│   ├── main.py            # Main API entry point
│   ├── transistors.py     # Transistor endpoints
│   └── topology.py        # Topology calculator endpoints
├── src/                   # Vue.js frontend source
├── dist/                  # Built frontend (auto-generated)
├── package.json           # Frontend dependencies & build scripts
├── requirements.txt       # Python dependencies for API
├── vercel.json           # Vercel configuration
└── vite.config.js        # Vite build configuration
```

## 🚀 Deployment Steps

### 1. **Prepare Repository**

Ensure your project structure matches the above layout. The key files are:

- `vercel.json` - Vercel deployment configuration
- `requirements.txt` - Python dependencies for serverless functions
- `api/` directory - Contains Python serverless functions
- Frontend code in `src/` with build output to `dist/`

### 2. **Deploy to Vercel**

#### Option A: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to gui_web directory
cd transistordatabase/gui_web

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Scope: Your account
# - Link to existing project? No
# - Project name: transistor-database
# - Directory: ./
# - Override settings? No
```

#### Option B: Deploy via GitHub Integration

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "New Project"
   - Import your repository
   - Set root directory to `transistordatabase/gui_web`
   - Deploy

### 3. **Environment Configuration**

#### Build Settings (Auto-detected):
- **Framework Preset:** Vite
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

#### API Routes:
Vercel automatically handles:
- Frontend: `https://your-app.vercel.app/`
- API: `https://your-app.vercel.app/api/*`

## 🔧 Configuration Files

### `vercel.json`
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "dist" }
    },
    {
      "src": "api/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/$1" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

### `requirements.txt`
```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
```

## 🌐 API Endpoints

Once deployed, your API will be available at:

- **Health Check:** `GET /api/health`
- **Transistors:** `GET /api/transistors`
- **Search:** `POST /api/transistors/search`
- **Upload:** `POST /api/transistors/upload`
- **Topology Calculator:** `POST /api/topology/calculate`

## 🎯 Features Available in Production

✅ **Frontend Features:**
- Advanced transistor search and filtering
- Interactive topology calculator
- Multi-format export tools
- Transistor comparison charts
- Responsive design with dark/light themes

✅ **Backend Features:**
- RESTful API with FastAPI
- Transistor data management
- Power converter calculations
- File upload/download
- Search and filtering

## 🔍 Testing Deployment

### Local Testing:
```bash
# Install dependencies
npm install

# Build frontend
npm run build

# Preview production build
npm run preview
```

### Production Testing:
1. Visit your Vercel URL
2. Test all 5 tabs of the interface
3. Verify API endpoints at `/api/health`
4. Test file upload/download functionality

## 📊 Monitoring & Analytics

Vercel provides built-in:
- **Performance Analytics:** Page load times, Core Web Vitals
- **Function Logs:** Serverless function execution logs
- **Error Tracking:** Runtime errors and issues
- **Usage Statistics:** API calls and bandwidth

Access these from your Vercel dashboard.

## 🔒 Production Considerations

### Security:
- Update CORS origins in `api/main.py` to your domain
- Add authentication for sensitive operations
- Implement rate limiting for API endpoints

### Performance:
- Enable Vercel's Edge Caching
- Optimize images and assets
- Use Vercel's CDN for static files

### Database:
- For production, consider using:
  - Vercel Postgres for relational data
  - MongoDB Atlas for document storage
  - Supabase for full-stack solution

## 🚨 Troubleshooting

### Common Issues:

1. **Build Fails:**
   - Check `package.json` scripts
   - Verify Node.js version compatibility
   - Check for missing dependencies

2. **API Not Working:**
   - Verify `requirements.txt` has all Python dependencies
   - Check function logs in Vercel dashboard
   - Ensure proper API route configuration

3. **Frontend Not Loading:**
   - Check build output in `dist/` directory
   - Verify `index.html` exists in output
   - Check browser console for errors

### Debug Commands:
```bash
# Local development
npm run dev

# Build and preview
npm run build && npm run preview

# Check API locally
vercel dev
```

## 📈 Scaling

Vercel automatically scales:
- **Frontend:** Global CDN with edge caching
- **API Functions:** Auto-scaling serverless functions
- **Database:** Connect external database for persistence

For high-traffic applications, consider upgrading to Vercel Pro for enhanced performance and analytics.
