import subprocess, time, json, io, sys, shutil
import websocket, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9334
PROFILE = r"C:\Users\dell\AppData\Local\Temp\opencode\chrome_profile"

subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)

p = subprocess.Popen([CHROME, f'--remote-debugging-port={PORT}', f'--user-data-dir={PROFILE}',
                      '--no-first-run', '--no-default-browser-check', '--remote-allow-origins=*',
                      'https://juejin.cn/user/signin?from=default'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def cdp_url():
    for _ in range(100):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json', timeout=2) as r:
                targets = json.load(r)
                page = [t for t in targets if t['type'] == 'page']
                if page:
                    return page[0]['webSocketDebuggerUrl']
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError('CDP not up')

ws = websocket.create_connection(cdp_url(), timeout=30)
mid = 0
def send(method, params=None):
    global mid
    mid += 1
    ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get('id') == mid:
            return msg.get('result', {})

send('Network.enable')
send('Page.enable')
print('>>> 浏览器窗口已打开，请在弹出的 Chrome 里登录掘金（扫码/账号）')
print('>>> 登录成功后本脚本自动保存 cookie，无需其他操作')
print()

poll = 0
while poll < 300:
    r = send('Network.getAllCookies')
    cookies = r.get('cookies', [])
    jj = [c for c in cookies if 'juejin.cn' in c.get('domain', '') or 'bytedance.com' in c.get('domain', '')]
    sid = [c for c in jj if c.get('name') in ('sessionid', 'sessionid_ss', 'sid_tt') and c.get('value')]
    if sid:
        with open(r'C:\Users\dell\AppData\Local\Temp\opencode\cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=1)
        names = sorted({c['name'] for c in jj})
        print('!!! 已检测到登录态: sessionid =', sid[0]['value'][:12], '...')
        print('!!! 共存', len(jj), '个 juejin/bytedance cookie -> cookies.json')
        ws.close()
        sys.exit(0)
    poll += 1
    if poll % 10 == 0:
        print(f'... 等待登录中 ({poll*2}s), 已有 cookie: {len(jj)}')
    time.sleep(2)

print('超时未检测到登录')
ws.close()
sys.exit(1)