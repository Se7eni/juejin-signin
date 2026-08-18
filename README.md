# 掘金自动签到 + 自动抽奖

基于真实浏览器指纹（Chrome + CDP）自动完成掘金（juejin.cn）每日签到与每日抽奖，规避服务端对非浏览器 TLS/HTTP2 指纹的静默拦截。

## 功能

- 每日自动签到（`growth_api/v1/check_in`）
- 每日自动抽奖（`growth_api/v1/lottery/draw`）
- 自动识别"已签到/签到成功/抽中奖品"并输出结果
- 使用真实登录态 cookie（浏览器登录后自动抓取）
- 支持 Windows 计划任务每日运行

## 原理

掘金接口对非浏览器客户端（urllib/curl/Node fetch 等 TLS 指纹）会静默返回空体或"路由不存在"。
本方案让 Chrome（真实指纹）通过 DevTools Protocol 导航到签到页，再在**页面上下文内**用 `fetch(..., {credentials: 'include'})` 发起请求——a_bogus 由页面内 SDK（bdms.js）自动签名，cookie/UA/Origin/msToken 全部由浏览器提供。

## 项目结构

```
juejin-signin/
├── juejin_signin.py    # 主脚本：启动 Chrome -> 签到 -> 抽奖
├── login_capture.py    # 一次性：浏览器登录并抓取 cookie（cookies.json）
├── sign.js             # 备用：Node 直出 a_bogus 签名（纯 urllib 方案已被指纹拦截，仅作研究保留）
├── bdms.js             # 掘金页面 SDK（原版，sign.js 依赖）
├── cookies.json        # 登录态（敏感，不入库）
├── mstokens.json       # msToken（敏感，不入库）
└── requirements.txt
```

## 快速开始

1. 安装依赖：
   ```
   pip install websocket-client
   ```
   需要本机安装 Chrome/Edge，并确认路径（脚本默认 `C:\Program Files\Google\Chrome\Application\chrome.exe`）。

2. 抓取登录态（首次）：
   ```
   python login_capture.py
   ```
   会弹出浏览器窗口，手动扫码/登录掘金后脚本自动把 cookie 保存到 `cookies.json`。

3. 运行签到 + 抽奖：
   ```
   python juejin_signin.py
   ```
   输出示例：
   ```
   today_status -> 200 {"err_no":0,...,"check_in_done":false,...}
   RESULT: 签到成功!
   RESULT: 抽奖成功，获得 99矿石
   ```

   默认 headless 模式；加 `--headed` 参数可看到浏览器窗口。

## Windows 计划任务（每日 08:00）

```powershell
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c ""<python路径>\python.exe" -X utf8 "<项目路径>\juejin_signin.py" >> "<项目路径>\signin_log.txt" 2>&1"'
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00
Register-ScheduledTask -TaskName "JuejinAutoSignIn" -Action $action -Trigger $trigger -Force
```

## 注意事项

- `cookies.json` 包含登录态，**切勿提交到公开仓库**（已加入 .gitignore）。
- cookie 过期后重新执行 `login_capture.py`。
- 若页面未渲染签到组件（风控降级），稍等再运行；频繁重启浏览器会话可能触发字节风控。
- 本工具仅用于个人自动化，请遵守掘金服务条款与相关法律法规。
