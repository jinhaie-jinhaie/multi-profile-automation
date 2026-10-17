# -*- coding: utf-8 -*-
"""CDP 会话封装：连接 Chrome 调试端口，执行 JS / 导航 / 真实输入 / 点击 / 关闭。

用法：
    from core.cdp_manager import CDPSession
    s = CDPSession(9231)          # 连接 9231 端口
    s.navigate("https://example.com")
    print(s.eval("location.href"))
    s.close()
"""
import json
import time

import requests
import websocket


class CDPSession:
    """单个 Chrome 实例的 CDP 会话"""

    def __init__(self, port: int, timeout: int = 25):
        self.port = port
        pages = requests.get("http://127.0.0.1:%d/json/list" % port, timeout=5).json()
        target = next((p for p in pages if p.get("type") == "page"), None)
        if not target:
            raise RuntimeError("端口 %d 无页面 target（Chrome 未启动？）" % port)
        self.ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=timeout)
        self._mid = 0

    # ---------- 基础 ----------
    def _send(self, method: str, params: dict = None) -> dict:
        self._mid += 1
        self.ws.send(json.dumps({"id": self._mid, "method": method, "params": params or {}}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self._mid:
                return r

    def eval(self, expression: str):
        """执行 JS 并返回值"""
        r = self._send("Runtime.evaluate", {"expression": expression, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    def navigate(self, url: str):
        self._send("Page.navigate", {"url": url})
        time.sleep(2)

    def close(self):
        """优雅关闭浏览器（保留 profile 登录态）"""
        try:
            self._send("Browser.close", {})
        except Exception:
            pass
        try:
            self.ws.close()
        except Exception:
            pass

    # ---------- 输入 ----------
    def _enter(self):
        self._send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter",
                                               "windowsVirtualKeyCode": 13})
        self._send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter",
                                               "windowsVirtualKeyCode": 13})

    def type_text(self, selector: str, text: str):
        """真实键盘输入：聚焦 -> 清空 -> 输入"""
        ok = self.eval("(()=>{const el=document.querySelector(%s);if(!el)return false;"
                       "el.focus();el.click();return true})()" % json.dumps(selector))
        if not ok:
            return False
        time.sleep(0.4)
        # 全选删除
        self._send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
        self._send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
        self._send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace",
                                               "windowsVirtualKeyCode": 8})
        self._send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace",
                                               "windowsVirtualKeyCode": 8})
        time.sleep(0.3)
        self._send("Input.insertText", {"text": text})
        time.sleep(0.3)
        return True

    def press_enter(self):
        """真实回车键（常用于表单提交）"""
        self._enter()

    def click_text(self, text_pattern: str, timeout: int = 10) -> bool:
        """按文本正则真实点击元素（适用于 React 等 JS 渲染页面）"""
        end = time.time() + timeout
        while time.time() < end:
            box = self.eval("(()=>{const els=Array.from(document.querySelectorAll('button,a,[role=button]'));"
                            "const e=els.filter(x=>new RegExp(%s).test((x.textContent||'').trim()))"
                            ".sort((a,b)=>a.children.length-b.children.length)[0];"
                            "if(!e)return null;const r=e.getBoundingClientRect();"
                            "return {x:r.x+r.width/2,y:r.y+r.height/2}})()" % json.dumps(text_pattern))
            if box:
                self._send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": box["x"], "y": box["y"],
                                                        "button": "left", "clickCount": 1})
                self._send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": box["x"], "y": box["y"],
                                                        "button": "left", "clickCount": 1})
                return True
            time.sleep(1.5)
        return False

    # ---------- 便捷 ----------
    def wait_selector(self, selector: str, timeout: int = 25, visible_only: bool = True) -> bool:
        """等待元素出现"""
        end = time.time() + timeout
        while time.time() < end:
            r = self.eval("(()=>{const el=document.querySelector(%s);if(!el)return false;"
                          "return %s?el.offsetParent!==null:true})()" % (
                              json.dumps(selector), "true" if visible_only else "false"))
            if r:
                return True
            time.sleep(1)
        return False

    def page_text(self, limit: int = 300) -> str:
        return (self.eval("document.body.innerText.slice(0, %d)" % limit) or "")

    def current_url(self) -> str:
        return (self.eval("location.href") or "")
