import subprocess, time, json, io, sys, os
import websocket, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = os.path.join(HERE, 'chrome_profile')
PORT = 9365

EXPR_LIB = r'''window.__jj = {
  findBtn: function(keys) {
    var els = document.querySelectorAll('button');
    for (var i = 0; i < els.length; i++) {
      var t = (els[i].textContent || '').trim();
      for (var j = 0; j < keys.length; j++) {
        if (t.indexOf(keys[j]) >= 0) return {el: els[i], txt: t.slice(0, 20)};
      }
    }
    return null;
  },
  toast: function() {
    var els = document.querySelectorAll('[class*=toast]');
    for (var i = 0; i < els.length; i++) {
      var t = (els[i].textContent || '').trim();
      if (t) return t.slice(0, 100);
    }
    return '';
  },
  panelBtns: function() {
    var out = [];
    document.querySelectorAll('button').forEach(function(e) {
      var t = (e.textContent || '').trim();
      if (t && /签到|抽奖|抽一|宝箱|券|矿石/.test(t)) out.push(t.slice(0, 20));
    });
    return out;
  },
  dismiss: function() {
    var b = window.__jj.findBtn(['我知道了']);
    if (b) { b.el.click(); return 'dismissed'; }
    return 'none';
  },
  todayStatus: function() {
    return fetch('https://api.juejin.cn/growth_api/v2/get_today_status?aid=2608&uuid=7675201317183194624&spider=0', {credentials: 'include'}).then(function(r){return r.text()});
  }
};'''

def run_chrome(headless):
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
    time.sleep(1)
    args = [CHROME, f'--remote-debugging-port={PORT}', f'--user-data-dir={PROFILE}',
            '--no-first-run', '--no-default-browser-check', '--remote-allow-origins=*',
            '--window-size=1600,900']
    if headless:
        args += ['--headless=new', '--disable-gpu']
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json', timeout=2) as r:
                targets = json.load(r)
                page = [t for t in targets if t['type'] == 'page']
                if page:
                    return p, page[0]['webSocketDebuggerUrl']
        except Exception:
            pass
        time.sleep(0.2)
    return p, None

class Session:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=60)
        self.mid = 0

    def send(self, method, params=None):
        self.mid += 1
        self.ws.send(json.dumps({'id': self.mid, 'method': method, 'params': params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == self.mid:
                return msg.get('result', {})

    def pump(self, t):
        self.ws.settimeout(0.05)
        t0 = time.time()
        while time.time() - t0 < t:
            try:
                json.loads(self.ws.recv())
            except Exception:
                pass
        self.ws.settimeout(None)

    def evl(self, expr, await_p=False):
        r = self.send('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': await_p})
        return r.get('result', {}).get('value')

def click(s, keys):
    keys_json = json.dumps(keys)
    return s.evl('(function(){var b = window.__jj.findBtn(%s); if (b) { b.el.click(); return "clicked:" + b.txt; } return "none"})()' % keys_json)

def wait_panel(s, tries=3):
    for i in range(tries):
        s.pump(8)
        btns = s.evl('window.__jj.panelBtns()')
        if btns:
            return btns
        print(f'  panel empty (try {i+1}/{tries}), reloading...')
        s.send('Page.reload')
        s.pump(10)
        s.evl('window.__jj.dismiss()')
    return None

def main():
    headless = '--headed' not in sys.argv
    p = None
    try:
        p, url = run_chrome(headless)
        if not url:
            print('FATAL: chrome cdp not up')
            sys.exit(1)
        s = Session(url)
        s.send('Page.enable')
        s.send('Runtime.enable')
        s.send('Page.navigate', {'url': 'https://juejin.cn/user/center/signin'})
        s.pump(11)
        s.evl(EXPR_LIB)
        s.evl('window.__jj.dismiss()')

        btns = wait_panel(s)
        if not btns:
            print('FATAL: 签到组件未渲染（可能被风控降级），稍后再试')
            sys.exit(2)
        print('panel:', btns)

        done = False
        r = s.evl('window.__jj.todayStatus()', await_p=True)
        if r and '"check_in_done":true' in r:
            print('today_status: 已签到')
            done = True

        if not done:
            r = click(s, ['立即签到', '签到'])
            print('click checkin:', r)
            if r and r.startswith('clicked'):
                s.pump(5)
            toast = s.evl('window.__jj.toast()')
            print('toast:', toast)
            r2 = s.evl('window.__jj.todayStatus()', await_p=True)
            if r2 and '"check_in_done":true' in r2:
                print('RESULT: 签到成功')
            else:
                print('RESULT: 签到结果待确认:', (toast or '无提示'))

        r = click(s, ['去抽奖', '抽奖', '抽一次'])
        print('click lottery:', r)
        if r and r.startswith('clicked'):
            s.pump(8)
        toast2 = s.evl('window.__jj.toast()')
        print('toast2:', toast2)
        if toast2:
            print('RESULT: 抽奖结果:', toast2)
    finally:
        if p:
            p.terminate()
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)

if __name__ == '__main__':
    main()