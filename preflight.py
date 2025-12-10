#!/usr/bin/env python
"""
Pre-flight initialization script for Render deployment.
Ensures embeddings and vectorizer are downloaded before app starts.
"""
import os
import sys
import time

# Add RAG-assistance to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'RAG-assistance'))

def ensure_files_exist():
    """Ensure embeddings.joblib and tfidf_vectorizer.joblib exist."""
    app_dir = os.path.join(os.path.dirname(__file__), 'RAG-assistance')
    embeddings_path = os.path.join(app_dir, 'embeddings.joblib')
    vec_path = os.path.join(app_dir, 'tfidf_vectorizer.joblib')
    
    embeddings_url = os.getenv('EMBEDDINGS_URL')
    tfidf_url = os.getenv('TFIDF_VECTORIZER_URL')
    
    print("=" * 60)
    print("Pre-flight: Checking required files...")
    print("=" * 60)
    
    # Import download functions from app
    from app import _download_if_missing
    
    files_ready = True
    
    # Check embeddings
    if os.path.exists(embeddings_path):
        size_mb = os.path.getsize(embeddings_path) / (1024 * 1024)
        print(f"✓ embeddings.joblib found ({size_mb:.1f}MB)")
    elif embeddings_url:
        print(f"✗ embeddings.joblib not found, downloading...")
        try:
            _download_if_missing(embeddings_path, embeddings_url, max_retries=5)
            size_mb = os.path.getsize(embeddings_path) / (1024 * 1024)
            print(f"✓ embeddings.joblib downloaded ({size_mb:.1f}MB)")
        except Exception as e:
            print(f"✗ Failed to download embeddings: {e}")
            files_ready = False
    else:
        print(f"✗ embeddings.joblib not found and no EMBEDDINGS_URL provided")
        files_ready = False
    
    # Check vectorizer
    if os.path.exists(vec_path):
        size_mb = os.path.getsize(vec_path) / (1024 * 1024)
        print(f"✓ tfidf_vectorizer.joblib found ({size_mb:.1f}MB)")
    elif tfidf_url:
        print(f"✗ tfidf_vectorizer.joblib not found, downloading...")
        try:
            _download_if_missing(vec_path, tfidf_url, max_retries=5)
            size_mb = os.path.getsize(vec_path) / (1024 * 1024)
            print(f"✓ tfidf_vectorizer.joblib downloaded ({size_mb:.1f}MB)")
        except Exception as e:
            print(f"✗ Failed to download vectorizer: {e}")
            # Vectorizer can be regenerated, not critical
            print("  Note: Vectorizer will be regenerated from embeddings if needed")
    else:
        print(f"! tfidf_vectorizer.joblib not found and no TFIDF_VECTORIZER_URL provided")
        print("  Note: Vectorizer will be regenerated from embeddings")
    
    print("=" * 60)
    
    if not files_ready and not os.path.exists(embeddings_path):
        print("ERROR: Critical files not available. Cannot start application.")
        return False
    
    print("Pre-flight check complete. Ready to start application.")
    return True

if __name__ == '__main__':
    if ensure_files_exist():
        port = os.environ.get('PORT', '8000')
        print(f"\nStarting Gunicorn on port {port}...")
        # Re-exec into gunicorn (replace current process)
        try:
            os.execvp('gunicorn', ['gunicorn', 'wsgi:app', '--bind', f'0.0.0.0:{port}', '--workers', '1', '--timeout', '120'])
        except Exception as e:
            print(f"Error starting Gunicorn: {e}")
            sys.exit(1)
    else:
        print("Pre-flight check failed. Exiting.")
        sys.exit(1)
