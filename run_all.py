import sys, os, json, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print('=' * 50)

# 掘金签到
try:
    print('\n>>> 掘金签到 <<<')
    from juejin_signin import main as juejin_main
    juejin_main()
except Exception as e:
    print(f'  掘金签到异常: {e}')

# 阿里云盘签到
ALIYUN_TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aliyun_tokens.json')

print('\n>>> 阿里云盘签到 <<<')
try:
    from aliyun_signin import run as aliyun_run
    if os.path.exists(ALIYUN_TOKEN_FILE):
        with open(ALIYUN_TOKEN_FILE, 'r') as f:
            tokens = [t.strip() for t in f.read().strip().split('\n') if t.strip()]
    else:
        tokens = [os.environ.get('ALIYUN_REFRESH_TOKEN', '')]
    tokens = [t for t in tokens if t]
    if tokens:
        new_token = aliyun_run(tokens)
        if new_token and os.path.exists(ALIYUN_TOKEN_FILE):
            with open(ALIYUN_TOKEN_FILE, 'w') as f:
                f.write(new_token + '\n')
    else:
        print('  未配置 refresh_token，跳过')
except Exception as e:
    print(f'  阿里云盘签到异常: {e}')

print('\n' + '=' * 50)
