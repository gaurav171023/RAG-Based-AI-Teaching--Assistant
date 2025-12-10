#!/usr/bin/env python
"""
Local verification script to test Render deployment setup.
Run this before pushing to Render to catch issues early.
"""
import os
import sys

def check_files():
    """Check if required files exist."""
    print("\n📦 Checking required files...")
    app_dir = os.path.join(os.path.dirname(__file__), 'RAG-assistance')
    embeddings_path = os.path.join(app_dir, 'embeddings.joblib')
    vec_path = os.path.join(app_dir, 'tfidf_vectorizer.joblib')
    
    all_good = True
    
    if os.path.exists(embeddings_path):
        size_mb = os.path.getsize(embeddings_path) / (1024 * 1024)
        print(f"  ✓ embeddings.joblib ({size_mb:.1f}MB)")
    else:
        print(f"  ✗ embeddings.joblib NOT FOUND")
        all_good = False
    
    if os.path.exists(vec_path):
        size_mb = os.path.getsize(vec_path) / (1024 * 1024)
        print(f"  ✓ tfidf_vectorizer.joblib ({size_mb:.1f}MB)")
    else:
        print(f"  ✗ tfidf_vectorizer.joblib NOT FOUND")
        # Not critical - can be regenerated
        print(f"    (Can be regenerated from embeddings)")
    
    return all_good

def check_imports():
    """Check if all required packages are installed."""
    print("\n📚 Checking required packages...")
    
    required = {
        'flask': 'Flask',
        'joblib': 'joblib',
        'sklearn': 'scikit-learn',
        'requests': 'requests',
        'numpy': 'numpy',
        'librosa': 'librosa',
        'torch': 'torch',
        'gdown': 'gdown (for Google Drive downloads)',
    }
    
    all_good = True
    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} NOT INSTALLED")
            all_good = False
    
    return all_good

def check_app_loads():
    """Check if app.py can load without errors."""
    print("\n🚀 Checking if app loads...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'RAG-assistance'))
        from app import app, df, vec
        
        print(f"  ✓ Flask app loads successfully")
        print(f"  ✓ DataFrame loaded ({len(df)} rows)")
        print(f"  ✓ TF-IDF vectorizer loaded")
        
        # Test that we can ask a question
        from app import answer_question
        results = answer_question("HTML basics", top_k=3)
        if results:
            print(f"  ✓ Query system works ({len(results)} results)")
        else:
            print(f"  ⚠ Query returned no results")
        
        return True
    except Exception as e:
        print(f"  ✗ Error loading app: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_env_vars():
    """Check if required environment variables are set (for Render)."""
    print("\n🔐 Checking environment variables (for Render)...")
    
    embeddings_url = os.getenv('EMBEDDINGS_URL')
    tfidf_url = os.getenv('TFIDF_VECTORIZER_URL')
    
    if embeddings_url:
        print(f"  ✓ EMBEDDINGS_URL set")
    else:
        print(f"  ⚠ EMBEDDINGS_URL not set (needed for Render)")
    
    if tfidf_url:
        print(f"  ✓ TFIDF_VECTORIZER_URL set")
    else:
        print(f"  ⚠ TFIDF_VECTORIZER_URL not set (needed for Render)")
    
    return True

def main():
    print("=" * 60)
    print("🔍 RAG Project Verification Script")
    print("=" * 60)
    
    checks = [
        ("Files", check_files),
        ("Packages", check_imports),
        ("App Loading", check_app_loads),
        ("Environment", check_env_vars),
    ]
    
    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All checks passed! Ready for Render deployment.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Fix issues above before deploying.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
