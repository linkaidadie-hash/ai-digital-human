import sys, os, time, requests, subprocess, json
sys.path.insert(0, '.')

print('=== V1.1 ACCEPTANCE TEST ===')

# Start backend
print('1. Starting backend...')
env = {**os.environ}
env['PATH'] = r'C:\Users\Administrator\AppData\Local\Programs\FFmpeg\ffmpeg-8.1.1-essentials_build\bin;' + env.get('PATH', '')
server = subprocess.Popen(
    ['py', 'main.py'],
    cwd=r'C:\Users\Administrator\ai-digital-human\backend',
    env=env,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
)
time.sleep(3)
print('Backend PID:', server.pid)

try:
    # Health check
    print('2. Health check...')
    r = requests.get('http://localhost:8000/health', timeout=5)
    print('Health:', r.json())

    # Test render endpoint
    print('3. Running /api/pipeline/render/test ...')
    start = time.time()
    r = requests.post('http://localhost:8000/api/pipeline/render/test', timeout=120)
    data = r.json()
    elapsed = time.time() - start
    print('Status:', data.get('status'))
    print('Elapsed:', str(elapsed) + 's')
    print('Duration:', str(data.get('duration')) + 's')
    print('Size:', str(data.get('size_kb')) + ' KB')
    print('Video:', data.get('test_video'))

    if data.get('success'):
        result = 'PASS' if elapsed < 60 else 'SLOW'
        print('ACCEPTANCE:', result, '(' + str(round(elapsed, 1)) + 's)')
    else:
        print('ACCEPTANCE: FAIL -', data.get('detail', 'unknown error'))

finally:
    server.terminate()
    server.wait()
    print('Done.')