# -*- coding: utf-8 -*-
"""Token 本地存取：账号名 -> token / 端口 / 更新时间。

存储为 JSON（默认 accounts.json）。属于敏感数据，勿提交到公开仓库。
"""
import json
import os
import time


class TokenStore:
    """简单的 JSON 键值存储，key = 账号标识（邮箱/用户名）"""

    def __init__(self, path: str = "accounts.json"):
        self.path = path
        self.data = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def upsert(self, key: str, token: str, port: int = None, extra: dict = None):
        """写入/更新一个账号（token 为空则保留旧值）"""
        old = self.data.get(key, {})
        self.data[key] = {
            "key": key,
            "token": token or old.get("token"),
            "port": port or old.get("port"),
            "updated_at": int(time.time()),
            "extra": extra or old.get("extra", {}),
        }
        self._save()

    def get(self, key: str) -> dict:
        return self.data.get(key)

    def all(self) -> dict:
        return self.data

    def keys(self) -> list:
        return list(self.data.keys())

    def remove(self, key: str):
        self.data.pop(key, None)
        self._save()
