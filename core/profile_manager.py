# -*- coding: utf-8 -*-
"""多 Profile 管理：批量启动 / 关闭独立 Chrome 实例。

每个 profile 拥有独立用户目录（登录态隔离），分配固定调试端口。
"""
import os
import subprocess
import time

import requests

DEFAULT_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEFAULT_EXTENSION = None  # 例如 r"D:\extensions\metamask"（可选）


class ProfileManager:
    """管理一批独立 Chrome profile"""

    def __init__(self, base_dir: str = "profiles", start_port: int = 9231,
                 chrome_path: str = None, extension_path: str = None):
        self.base_dir = base_dir
        self.start_port = start_port
        self.chrome = chrome_path or DEFAULT_CHROME
        self.extension = extension_path or DEFAULT_EXTENSION

    def _profile_dir(self, index: int) -> str:
        return os.path.join(self.base_dir, "p%d" % index)

    def _port(self, index: int) -> int:
        return self.start_port + index - 1

    def is_running(self, index: int) -> bool:
        try:
            requests.get("http://127.0.0.1:%d/json/version" % self._port(index), timeout=3)
            return True
        except Exception:
            return False

    def launch(self, count: int = 1, indexes: list = None):
        """启动 count 个 profile（p1..pN）。已运行的跳过。"""
        indexes = indexes or list(range(1, count + 1))
        for i in indexes:
            if self.is_running(i):
                print("p%d 已在运行，跳过" % i)
                continue
            args = [self.chrome, "--user-data-dir=" + self._profile_dir(i),
                    "--remote-debugging-port=%d" % self._port(i),
                    "--remote-allow-origins=*", "--no-first-run",
                    "--no-default-browser-check", "--window-size=1280,900"]
            if self.extension:
                args.append("--load-extension=" + self.extension)
            subprocess.Popen(args, shell=False)
            print("p%d 启动中（端口 %d）..." % (i, self._port(i)))
            # 等待端口就绪
            for _ in range(20):
                time.sleep(1)
                if self.is_running(i):
                    print("p%d 就绪" % i)
                    break

    def close_all(self):
        """优雅关闭全部（保留登录态）。通过 CDP Browser.close 实现，不影响其他 Chrome。"""
        import websocket as ws_mod
        from .cdp_manager import CDPSession
        closed = []
        for i in range(1, 20):  # 最多扫 19 个
            port = self._port(i)
            if not self.is_running(i):
                continue
            try:
                s = CDPSession(port)
                s.close()
                closed.append(i)
                time.sleep(1)
            except Exception:
                pass
        print("已关闭:", closed)
