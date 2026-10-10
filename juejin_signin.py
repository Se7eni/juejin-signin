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
  listBtns: function() {
    var out = [];
    document.querySelectorAll('button').forEach(function(e) {
      var t = (e.textContent || '').trim();
      if (t) out.push(t.slice(0, 20));
    });
    return out;
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
      if (t && /签到|抽奖|抽一|宝箱|券|矿石|兑换/.test(t)) out.push(t.slice(0, 20));
    });
    return out;
  },
  dismissRisk: function() {
    var bs = document.querySelectorAll('button');
    for (var i = 0; i < bs.length; i++) {
      if ((bs[i].textContent || '').indexOf('我知道了') >= 0) { bs[i].click(); return 'dismissed'; }
    }
    return 'none';
  },
  todayStatus: function() {
    return fetch('https://api.juejin.cn/growth_api/v2/get_today_status?aid=2608&uuid=7675201317183194624&spider=0', {credentials: 'include'}).then(function(r){return r.text()});
  }
};'''

def run_chrome(headless):
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

def stop_chrome(p):
    """只关闭本脚本启动的 Chrome 进程树，不影响用户正在使用的 Chrome。"""
    if not p or p.poll() is not None:
        return
    subprocess.run(
        ['taskkill', '/F', '/T', '/PID', str(p.pid)],
        capture_output=True,
    )
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass

class Session:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=60)
        self.mid = 0
        self.resp = {}

    def send(self, method, params=None):
        self.mid += 1
        self.ws.send(json.dumps({'id': self.mid, 'method': method, 'params': params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == self.mid:
                return msg.get('result', {})

    def pump(self, t, on_msg=None):
        self.ws.settimeout(0.05)
        t0 = time.time()
        while time.time() - t0 < t:
            try:
                msg = json.loads(self.ws.recv())
                if on_msg:
                    on_msg(msg)
            except Exception:
                pass
        self.ws.settimeout(None)

    def evl(self, expr, await_p=False):
        r = self.send('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': await_p})
        return r.get('result', {}).get('value')

def net_capture(s):
    pending = {}
    def on_msg(msg):
        m = msg.get('method')
        if m == 'Network.responseReceived':
            url = msg['params']['response']['url']
            if 'api.juejin.cn' in url and any(k in url for k in ('check_in', 'lottery/draw')):
                pending[msg['params']['requestId']] = url
        elif m == 'Network.loadingFinished':
            rid = msg['params']['requestId']
            if rid in pending:
                try:
                    body = s.send('Network.getResponseBody', {'requestId': rid}).get('body', '')
                    url = pending.pop(rid)
                    s.resp[url.split('?')[0].split('/')[-1]] = body[:500]
                except Exception:
                    pending.pop(rid, None)
    return on_msg

def click(s, keys):
    keys_json = json.dumps(keys)
    return s.evl('(function(){var b = window.__jj.findBtn(%s); if (b) { b.el.click(); return "clicked:" + b.txt; } return "none"})()' % keys_json)

def prepare(s, headless):
    s.send('Page.enable')
    s.send('Network.enable')
    s.send('Runtime.enable')
    s.send('Page.navigate', {'url': 'https://juejin.cn/user/center/signin'})
    s.pump(15)
    btns = None
    for i in range(3):
        s.evl(EXPR_LIB)
        s.evl('window.__jj.dismissRisk()')
        s.pump(7)
        btns = s.evl('window.__jj.panelBtns()')
        if btns:
            return btns
        s.send('Page.reload')
        s.pump(10)
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
        on_msg = net_capture(s)
        btns = prepare(s, headless)
        if not btns:
            if headless:
                print('headless 被风控拦截，自动切换到有头模式...')
                stop_chrome(p)
                time.sleep(2)
                p, url = run_chrome(False)
                if not url:
                    print('FATAL: chrome cdp not up (headed)')
                    sys.exit(1)
                s = Session(url)
                on_msg = net_capture(s)
                btns = prepare(s, False)
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
            s.pump(8, on_msg)
            r = click(s, ['立即签到', '签到'])
            print('click checkin:', r)
            if r and r.startswith('clicked'):
                s.pump(6, on_msg)
            if 'check_in' in s.resp:
                print('check_in rsp:', s.resp['check_in'])
                if '"err_no":0' in s.resp['check_in']:
                    print('RESULT: 签到成功!')
                else:
                    print('RESULT:', s.resp['check_in'][:200])
            else:
                print('RESULT: 未捕获到 check_in 响应')

        r = click(s, ['去抽奖', '抽奖', '抽一次'])
        print('click lottery_link:', r)
        if r and r.startswith('clicked'):
            s.pump(6, on_msg)
            href = s.evl('location.href') or ''
            print('href:', href)
            if '/lottery' not in href:
                s.send('Page.navigate', {'url': 'https://juejin.cn/user/center/lottery?from=sign_in_success'})
                s.pump(10, on_msg)
            s.evl('window.__jj.dismissRisk()')
            s.pump(2, on_msg)
            r2 = s.evl('''(function(){
              var els = document.querySelectorAll('.turntable-item.lottery');
              for (var i = 0; i < els.length; i++) {
                var t = (els[i].textContent || '').trim();
                if (t.indexOf('免费') >= 0 || t.indexOf('单抽') >= 0) {
                  els[i].click();
                  return 'clicked:' + t.slice(0, 10);
                }
              }
              if (els.length > 0) { els[0].click(); return 'clicked:first-lottery'; }
              return 'none';
            })()''')
            print('click draw:', r2)
            if r2 and 'clicked' in r2:
                s.pump(6, on_msg)
        if 'draw' in s.resp:
            print('draw rsp:', s.resp['draw'][:300])
            try:
                j = json.loads(s.resp['draw'])
                if j.get('err_no') == 0:
                    print('RESULT: 抽奖成功，获得', j.get('data', {}).get('lottery_name', '?'))
                else:
                    print('RESULT:', j.get('err_msg', '')[:100])
            except Exception:
                print('RESULT: draw 响应解析失败')
        else:
            print('RESULT: 未捕获到 draw 请求（可能今日次数已用完，弹提示未发请求）')
    finally:
        stop_chrome(p)

if __name__ == '__main__':
    main()