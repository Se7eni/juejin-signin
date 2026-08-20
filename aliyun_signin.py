import json, urllib.request, urllib.error

TOKEN_URL = 'https://auth.aliyundrive.com/v2/account/token'
SIGN_URL = 'https://member.aliyundrive.com/v1/activity/sign_in_list'
REWARD_URL = 'https://member.aliyundrive.com/v1/activity/sign_in_reward'

def post(url, body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())

def refresh(refresh_token):
    r = post(TOKEN_URL, {'grant_type': 'refresh_token', 'refresh_token': refresh_token})
    if 'access_token' not in r:
        print(f'  refresh 失败: {r.get("code", "")} {r.get("message", "")}')
        return None, None
    return r['access_token'], r.get('refresh_token', refresh_token)

def sign_in(access_token):
    r = post(SIGN_URL, {'isReward': False}, access_token)
    if not r.get('success'):
        print(f'  签到失败: {r.get("message", "")}')
        return None, None
    result = r['result']
    count = result['signInCount']
    logs = result['signInLogs']
    today = logs[count - 1] if count <= len(logs) else {}
    return count, today

def get_reward(access_token, day):
    r = post(REWARD_URL, {'signInDay': day}, access_token)
    if not r.get('success'):
        return None
    return r.get('result')

def run(refresh_tokens):
    for token in refresh_tokens:
        token = token.strip()
        if not token:
            continue
        print(f'== 阿里云盘 ==')
        access_token, new_token = refresh(token)
        if not access_token:
            continue
        print(f'  token 已刷新')
        count, today = sign_in(access_token)
        if count is None:
            continue
        print(f'  本月签到 {count} 天')
        reward_info = today.get('reward', {})
        if today.get('isReward'):
            print(f'  今日奖励: {reward_info.get("name", "")} {reward_info.get("description", "")}')
        else:
            print(f'  今日签到: 无额外奖励')
        return new_token
    return None