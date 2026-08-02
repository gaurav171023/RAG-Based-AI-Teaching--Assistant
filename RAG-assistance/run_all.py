import subprocess
import sys
import os

ROOT = os.path.dirname(__file__)

def run(cmd_args):
    print('Running:', ' '.join(cmd_args))
    r = subprocess.run(cmd_args, capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print('STDERR:', r.stderr)
    if r.returncode != 0:
        print('Command failed with exit code', r.returncode)
        sys.exit(r.returncode)

# Step 1: Preprocess JSON -> embeddings.joblib
if __name__ == '__main__':
    run([sys.executable, os.path.join(ROOT, 'preprocess_json.py')])
    # Step 2: Run a sample query through process_incoming.py non-interactively
    query = "where is html concluded in this course"
    print('Running process_incoming.py with sample query: ', query)
    p = subprocess.Popen([sys.executable, os.path.join(ROOT, 'process_incoming.py')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(query + "\n")
    print(out)
    if err:
        print('ERR:', err)