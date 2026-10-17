# Multi-Profile Automation 多号浏览器自动化框架

一个基于 Chrome DevTools Protocol (CDP) 的**多账号浏览器自动化框架**：独立 profile 隔离、批量启动、统一 token 采集与存储。

> 适用场景：多账号运营、账号数据管理、批量登录采集、Web 自动化测试。
> 轻量无依赖（Python 3.8+ 即可），不依赖 Selenium、不依赖额外浏览器内核。

## ✨ 功能

- **多 Profile 隔离**：每个账号独立 Chrome 用户目录，登录态/指纹完全隔离
- **一键批量启动**：`--user-data-dir` + 自动分配调试端口（9231~9240），10 个窗口秒级拉起
- **CDP 统一封装**：连接、执行 JS、页面导航、真实键盘/鼠标输入（Input 域）、优雅关闭
- **Token 自动采集**：登录后自动从 `localStorage` 抓取鉴权 token，写入本地 JSON 存储
- **状态持久化**：账号名 ↔ 端口 ↔ token 对应关系存 `accounts.json`，重启不丢

## 🚀 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 1. 创建 profile 目录
mkdir profiles\p1 profiles\p2

# 2. 启动多号浏览器（端口 9231、9232 ...）
python examples\batch_login_flow.py --start 2

# 3. 示例：在 p1 中打开站点并采集 token
python examples\batch_login_flow.py --grab 9231 "user1@example.com"
```

### 手动启动单个 profile（带 MetaMask 等扩展）

```bat
chrome.exe --user-data-dir=profiles\p1 --remote-debugging-port=9231 --remote-allow-origins=*
```

## 📁 项目结构

```
multi-profile-automation/
├── core/
│   ├── cdp_manager.py      # CDP 连接/执行 JS/键盘鼠标/关闭
│   ├── profile_manager.py  # 多 profile 启动与端口管理
│   └── token_store.py      # token 本地存取
├── examples/
│   └── batch_login_flow.py # 示例：批量启动 + 登录采集
├── requirements.txt
└── README.md
```

## 🧩 核心用法

### 1. CDP 连接与执行 JS

```python
from core.cdp_manager import CDPSession

# 连接到已启动的 Chrome（端口 9231）
session = CDPSession(9231)
print(session.eval("location.href"))        # 执行 JS
session.navigate("https://example.com")     # 导航
session.type_text("#input", "hello")        # 真实输入
session.click_text("提交")                  # 点击按钮
session.close()                             # 优雅关闭
```

### 2. Token 采集与存储

```python
from core.token_store import TokenStore

store = TokenStore("accounts.json")
token = session.eval("localStorage.getItem('accessToken')")
store.upsert("user1@example.com", token, port=9231)
print(store.all())          # 全部账号
```

### 3. 多号批量启动

```python
from core.profile_manager import ProfileManager

pm = ProfileManager(base_dir="profiles", start_port=9231)
pm.launch(count=3)          # 启动 p1~p3，端口 9231~9233
pm.close_all()              # 优雅关闭全部（保留登录态）
```

## ⚠️ 使用须知

- 仅用于**合法合规**的多账号管理与自动化测试
- 请遵守目标网站服务条款，不要用于绕过风控、刷量或任何违规行为
- 登录态属于敏感数据，`accounts.json` 请勿提交到公开仓库（已在 `.gitignore`）

## 📄 License

MIT License

## ⭐ 支持

如果这个框架对你有帮助，点个 Star ⭐ 是对我最大的支持。完整版（多站点模板、GUI 管理面板、定时任务）持续开发中。
