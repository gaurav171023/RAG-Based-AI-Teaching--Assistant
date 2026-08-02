# Render Deployment - What Happens Next

## Current Status

You've pushed the latest fixes to GitHub. Render should now use the **corrected Procfile** which calls `python preflight.py` instead of directly starting gunicorn.

## Expected Deployment Flow

When you trigger a new deploy on Render (or it auto-deploys when you push), here's what should happen:

### 1. **Build Phase** ✓
```
==> Build started...
==> Installing Python 3.10
==> pip install -r requirements.txt
    - Installs Flask, torch, scikit-learn, joblib, requests, gdown, etc.
==> Build successful 🎉
```

### 2. **Deploy Phase** (The Fix)
```
==> Deploying...
==> Running 'python preflight.py'
```

**Before** (failing):
```
==> Running 'gunicorn wsgi:app --bind 0.0.0.0:$PORT'
ERROR: embeddings.joblib not found
==> Exited with status 1
```

**After** (should work):
```
==> Running 'python preflight.py'

============================================================
🔍 RAG Project Verification Script
============================================================

📦 Checking required files...
  ⏳ embeddings.joblib not found, downloading...
  ✓ Downloading from Google Drive (using gdown)...
  ✓ Download complete: embeddings.joblib (64.5MB)

  ✓ tfidf_vectorizer.joblib found (X.XMB)

============================================================
Pre-flight check complete. Ready to start application.

Starting Gunicorn on port 10000...
[2025-12-11 ...] [INFO] Starting gunicorn 21.2.0
[2025-12-11 ...] [INFO] Listening at: http://0.0.0.0:10000 (pid)
[2025-12-11 ...] [INFO] Using worker: sync
[2025-12-11 ...] [INFO] Booted worker (pid)
```

### 3. **Success** ✅
- App loads and binds to the port
- Your RAG Teaching Assistant is now **LIVE**
- Access it at: https://rag-based-ai-teaching-assistant-3.onrender.com

## Key Changes Made

| File | Change | Reason |
|------|--------|--------|
| `Procfile` | `web: python preflight.py` | Ensures downloads before app starts |
| `RAG-assistance/Procfile` | DELETED | Was overriding root Procfile |
| `preflight.py` | NEW | Pre-flight checks and gdown setup |
| `requirements.txt` | Added `gdown==5.1.0` | More reliable Google Drive downloads |
| `app.py` | Enhanced download logic | Better error handling and retries |

## If It Still Fails

### Error: "gdown not found"
**Solution**: Make sure `requirements.txt` includes `gdown==5.1.0`
```bash
grep gdown requirements.txt
# Should show: gdown==5.1.0
```

### Error: "Still can't download from Google Drive"
**Solutions** (in order of ease):

1. **Check Google Drive URLs are correct**:
   - EMBEDDINGS_URL in render.yaml
   - TFIDF_VECTORIZER_URL in render.yaml
   - Make sure IDs are not truncated

2. **Use alternative storage** (if Google Drive keeps failing):
   - Upload to AWS S3 (free tier)
   - Upload to Hugging Face Hub (free)
   - Use a CDN like Cloudflare R2

3. **Commit files to Git with Git LFS**:
   ```bash
   git lfs install
   git lfs track "*.joblib"
   git add .gitattributes *.joblib
   git commit -m "Track large files with Git LFS"
   git push
   ```

## How to Trigger New Deployment

### Option 1: Push to GitHub (Recommended)
```bash
git add .
git commit -m "Deploy latest changes"
git push origin master
# Render auto-deploys on push
```

### Option 2: Manual Trigger on Render
1. Go to https://dashboard.render.com/
2. Find "rag-assistant"
3. Click "Manual Deploy" → "Deploy latest commit"

### Option 3: Check Logs
1. Go to dashboard.render.com
2. Click on "rag-assistant" service
3. Go to "Logs" tab
4. See real-time deployment output
5. Look for the preflight script output

## What to Look For in Logs

**Good signs**:
✓ `Pre-flight: Checking required files...`
✓ `✓ embeddings.joblib found`
✓ `Pre-flight check complete. Ready to start application.`
✓ `Starting Gunicorn on port`
✓ `Listening at: http://0.0.0.0:PORT`

**Bad signs**:
✗ `embeddings.joblib not found`
✗ `gdown failed and fallback failed`
✗ `All download attempts failed`
✗ `Exited with status 1` (without preflight messages)

## Testing Locally

Before deploying, verify locally:
```powershell
# Run verification script
python verify_setup.py

# Should show: ✅ All checks passed!

# Or test preflight manually
$env:EMBEDDINGS_URL = "https://drive.google.com/uc?export=download&id=1k11N6Kcso7uT1aDJJsxEgRmd-DcapgZl"
$env:TFIDF_VECTORIZER_URL = "https://drive.google.com/uc?export=download&id=1CG9IsIcZIvDj8LAGpVt7LH5mkdqfTJmW"
python preflight.py
# Should download files and start Gunicorn
```

## Next Actions

1. **Verify files are committed**: `git status` (should be clean)
2. **Trigger new Render deploy**: Push to master or use manual deploy
3. **Monitor logs**: Watch Render dashboard for preflight output
4. **Test the app**: Visit your Render URL once deployed
5. **Try a query**: Go to /ask endpoint and test the RAG system

---

## Summary of Fixed Issues

| Problem | Solution | Status |
|---------|----------|--------|
| Direct gunicorn call skipped downloads | Use preflight.py | ✅ Fixed |
| Google Drive downloads unreliable | Added gdown package | ✅ Fixed |
| No retries on download failure | Added exponential backoff (5 retries) | ✅ Fixed |
| Duplicate/conflicting Procfiles | Removed subfolder Procfile | ✅ Fixed |
| Poor error messages | Added clear preflight logging | ✅ Fixed |

You're now set up for a successful deployment! 🚀
