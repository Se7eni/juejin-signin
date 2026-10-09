# 项目交接文档

> 最后更新：2026-09-15
> 交接目的：供其他 AI 管理本项目

---

## 一、项目概述

本项目实现两个平台的每日自动签到：

| 平台 | 方式 | 脚本 | 状态 |
|------|------|------|------|
| 掘金 | Chrome CDP 浏览器驱动 | `juejin_signin.py` | ✅ 正常运行 |
| 阿里云盘 | 纯 API（无需浏览器） | `aliyun_signin.py` | ✅ 正常运行 |

合并入口：`run_all.py`（先掘金后阿里云盘）

---

## 二、目录结构

```
D:\opencode\juejin-signin\
├── juejin_signin.py       # 掘金签到+抽奖主脚本（Chrome CDP）
├── aliyun_signin.py       # 阿里云盘签到（纯API）
├── run_all.py             # 合并入口，计划任务实际运行的脚本
├── run.bat                # 计划任务调用的批处理
├── login_capture.py       # 掘金登录态抓取（手动运行，登录后保存 cookies.json）
├── add_watermark.py       # 图片加水印工具（独立，与签到无关）
├── sign.js                # Node 签名服务（研究用，当前不需要）
├── bdms.js                # 掘金原版 SDK（sign.js 依赖，研究用）
├── cookies.json           # 掘金登录态（gitignore，过期需重新登录）
├── aliyun_tokens.json     # 阿里云盘 refresh_token（gitignore，会轮换）
├── signin_log.txt         # 签到日志（gitignore）
├── chrome_profile/        # Chrome 持久化 profile（gitignore）
├── .gitignore
├── requirements.txt       # websocket-client>=1.0
└── README.md
```

GitHub 仓库：`https://github.com/Se7eni/juejin-signin`
分支：`master`

---

## 三、掘金签到原理

### 为什么用浏览器而不是纯 API

掘金 2026 年更新了接口，且有 TLS/HTTP2 指纹风控：
- 直连（urllib/curl/requests）会被网关按设备指纹分组路由，部分接口静默空体 200
- 必须用真实浏览器（Chrome）的页面内 `fetch()` + `credentials:'include'` 才能正常调用
- `a_bogus` 签名由页面加载的 bdms.js 自动完成，无需手动计算

### 接口路径（2026 版）

| 功能 | 方法 | 路径 |
|------|------|------|
| 签到状态 | GET | `growth_api/v2/get_today_status` |
| 签到 | POST | `growth_api/v1/check_in` |
| 抽奖 | POST | `growth_api/v1/lottery/draw` |

### 工作流程

1. 启动 Chrome（headless 优先，风控拦截则自动回退有头模式）
2. CDP 连接，导航到 `https://juejin.cn/user/center/signin`
3. 注入 JS 查找签到按钮 → 点击「立即签到」
4. 导航到 `https://juejin.cn/user/center/lottery`
5. 点击 `.turntable-item.lottery`（含"免费"或"单抽"）
6. 通过 Network 事件捕获 draw 响应，输出奖品名

### 关键配置

- Chrome 路径：`C:\Program Files\Google\Chrome\Application\chrome.exe`
- CDP 端口：`9365`
- Chrome profile：`D:\opencode\juejin-signin\chrome_profile\`（持久化登录态）
- 用户 UUID：`7675201317183194624`
- 用户 profile_id：`2926247859192336`

### 已知问题

- **Headless 常被风控拦截**：签到组件不渲染，脚本自动回退有头模式（窗口闪一下）
- **cookies.json 过期**：需手动运行 `python login_capture.py` 重新登录
- **msToken**：持久会话级，同一 profile 内稳定，无需每次抓取

---

## 四、阿里云盘签到原理

纯 API，无需浏览器。

### 接口

| 功能 | 方法 | URL |
|------|------|-----|
| 刷新 token | POST | `https://auth.aliyundrive.com/v2/account/token` |
| 签到列表 | POST | `https://member.aliyundrive.com/v1/activity/sign_in_list` |
| 领取奖励 | POST | `https://member.aliyundrive.com/v1/activity/sign_in_reward` |

### 使用方法

```python
from aliyun_signin import run
new_token = run(['refresh_token_1', 'refresh_token_2'])
```

### refresh_token 获取

1. 登录阿里云盘网页版 `https://www.aliyundrive.com/drive/`
2. F12 控制台执行：`console.log(JSON.parse(localStorage.token).refresh_token)`
3. 保存到 `aliyun_tokens.json`（一行一个 token）

### 重要

- refresh_token 会定期轮换，`run()` 返回新 token，需写回 `aliyun_tokens.json`
- 当前 token：`0671f830a415460394937ec5544a6675`

---

## 五、定时任务

| 项目 | 值 |
|------|-----|
| 任务名 | `JuejinAutoSignIn` |
| 触发时间 | 每天 08:00 |
| 运行命令 | `D:\opencode\juejin-signin\run.bat` |
| 日志 | `D:\opencode\juejin-signin\signin_log.txt` |
| 运行账户 | dell |

### 查看任务状态

```cmd
schtasks /query /tn "JuejinAutoSignIn" /fo list /v
```

### 手动触发

```cmd
schtasks /run /tn "JuejinAutoSignIn"
```

---

## 六、环境要求

| 依赖 | 说明 |
|------|------|
| Python | 3.10.32 位（`D:\Python\Python310-32\python.exe`） |
| Chrome | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| Node.js | `C:\Program Files\nodejs\node.exe`（仅研究用，不在 PATH） |
| Python 包 | `websocket-client>=1.0`, `Pillow`（水印工具用） |
| 代理 | `HTTP_PROXY=http://127.0.0.1:7897`（git push 需要） |
| gh CLI | `C:\Program Files\GitHub CLI\gh.exe`（GitHub 操作） |

---

## 七、常见故障处理

### 掘金签到失败（cookies.json 不存在）

```cmd
cd /d D:\opencode\juejin-signin
python login_capture.py
# 在弹出的 Chrome 窗口中手动登录掘金，脚本自动保存 cookie
```

### 掘金签到失败（cookie 过期）

同上，重新运行 `login_capture.py` 登录一次。

### 阿里云盘 token 过期

1. 登录阿里云盘网页版获取新 refresh_token
2. 更新 `aliyun_tokens.json`
3. 运行 `python aliyun_signin.py` 验证

### 计划任务没执行

```cmd
schtasks /query /tn "JuejinAutoSignIn" /fo list /v
# 检查"上次运行结果"，0 = 成功
```

### Chrome 端口被占用

脚本启动前会 `taskkill /F /IM chrome.exe`，不会冲突。

---

## 八、代码说明

### juejin_signin.py 核心函数

| 函数 | 作用 |
|------|------|
| `run_chrome(headless)` | 启动 Chrome 并返回 CDP URL |
| `Session.send(method, params)` | CDP 命令发送 |
| `Session.evl(expr, await_p)` | 页面 JS 求值 |
| `Session.pump(t, on_msg)` | 消息泵（等待事件） |
| `net_capture(s)` | 捕获 check_in/draw 网络响应 |
| `click(s, keys)` | 按关键词查找并点击按钮 |
| `prepare(s, headless)` | 导航到签到页并等待组件渲染 |
| `main()` | 主流程：签到 → 抽奖 → 输出结果 |

### run_all.py 流程

1. 导入并运行 `juejin_signin.main()`
2. 读取 `aliyun_tokens.json`（或环境变量 `ALIYUN_REFRESH_TOKEN`）
3. 调用 `aliyun_signin.run(tokens)`，将新 token 写回文件

---

## 九、待办事项

1. **验证未签到场景**：「立即签到」按钮点击路径代码已就位，但从未在真正未签到时测试过（测试时都是已签到状态）
2. **cookies.json 过期监控**：签到失败时需人工重新登录，可考虑增加过期检测和通知
3. **GitHub 推送**：最近一次推送失败（网络问题），需要检查 `git push origin master` 是否成功
4. **Headless 优化**：当前 headless 常被风控，长期方案是有头模式（窗口会闪约 15 秒）

---

## 十、注意事项

- **不要修改** `chrome_profile/` 目录（包含登录态）
- **不要提交** `cookies.json`、`aliyun_tokens.json` 到 git（已在 .gitignore）
- **Node 不在 PATH**：需要 Node 时用全路径 `& "C:\Program Files\nodejs\node.exe"`
- **本机 Python 是 32 位**：安装包时注意选择 32 位版本
- **代理**：git push / gh 命令需要 `HTTPS_PROXY=http://127.0.0.1:7897`
