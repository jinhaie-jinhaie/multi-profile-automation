# -*- coding: utf-8 -*-
"""示例：批量启动多号 Chrome + 登录站点 + 采集 token。

用法：
    python examples\\batch_login_flow.py --start 2            # 启动 p1~p2
    python examples\\batch_login_flow.py --grab 9231 user1@example.com   # 在 p1 采集 token
    python examples\\batch_login_flow.py --close              # 优雅关闭全部
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.profile_manager import ProfileManager
from core.cdp_manager import CDPSession
from core.token_store import TokenStore

LOGIN_URL = "https://example.com/login"   # 替换为实际登录页
USERNAME_SEL = "input[name=email]"        # 替换为实际选择器
PASSWORD_SEL = "input[name=password]"
TOKEN_KEY = "accessToken"                 # 替换为实际的 localStorage key


def do_start(count: int):
    pm = ProfileManager(base_dir="profiles", start_port=9231)
    pm.launch(count=count)
    print("已启动 %d 个 profile（端口 9231~%d）" % (count, 9230 + count))


def do_grab(port: int, email: str, password: str = ""):
    s = CDPSession(port)
    s.navigate(LOGIN_URL)
    if not s.wait_selector(USERNAME_SEL, timeout=20):
        print("登录表单未出现，请检查选择器/是否已登录")
        return
    s.type_text(USERNAME_SEL, email)
    s.type_text(PASSWORD_SEL, password)
    s.press_enter()
    # 等待登录完成（按页面特征调整）
    import time
    time.sleep(5)
    token = s.eval("localStorage.getItem(%s)" % repr(TOKEN_KEY)) if TOKEN_KEY else None
    if token:
        store = TokenStore("accounts.json")
        store.upsert(email, token, port=port)
        print("已采集 token：%s" % email)
    else:
        print("未找到 token，当前页面：%s" % s.current_url()[:80])
    s.close()


def do_close():
    pm = ProfileManager(base_dir="profiles", start_port=9231)
    pm.close_all()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="多号批量登录示例")
    ap.add_argument("--start", type=int, help="启动 N 个 profile")
    ap.add_argument("--grab", nargs=2, metavar=("PORT", "EMAIL"), help="在指定端口采集 token")
    ap.add_argument("--close", action="store_true", help="关闭全部")
    args = ap.parse_args()

    if args.start:
        do_start(args.start)
    elif args.grab:
        do_grab(int(args.grab[0]), args.grab[1])
    elif args.close:
        do_close()
    else:
        ap.print_help()
