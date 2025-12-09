# Deploying to Render

## Prerequisites
1. GitHub account
2. Render.com account (free)

## Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin master
```

### 2. Connect to Render
1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository and branch (`master`)

### 3. Configure Service
- **Name**: `rag-assistant` (or your choice)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: Free

### 4. Deploy
Click **"Create Web Service"** and Render will automatically deploy your app.

## Important Notes

### File Requirements
Make sure these files are in your repository (committed to Git):
- `embeddings.joblib` ⚠️ Required
- `tfidf_vectorizer.joblib` ⚠️ Required
- All Python files
- `templates/` and `static/` folders

**Check file sizes**: Large `.joblib` files may cause issues. If they exceed 100MB, consider:
- Using a database or cloud storage instead
- Splitting embeddings into smaller chunks

### Cold Starts
- First request after 15 mins of inactivity will be slow (free tier limitation)
- Subsequent requests are fast
- Upgrade to paid tier for no cold starts

### Environment Variables (Optional)
If needed, add in Render dashboard:
- `FLASK_ENV`: Set to `production`

## Troubleshooting

**Build fails**: Check that all dependencies in `requirements.txt` are compatible with Python 3.10

**App crashes**: Check logs in Render dashboard. Common issues:
- Missing `.joblib` files
- File path issues (use absolute paths)
- Memory limits on free tier

**Slow responses**: This is normal on free tier due to cold starts and limited resources
