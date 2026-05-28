import sys, subprocess
result = subprocess.run([sys.executable, '-c', 'import requests; print(requests.__version__)'], capture_output=True, text=True)
print('requests version:', result.stdout.strip() or 'NOT INSTALLED')
print('err:', result.stderr.strip())
