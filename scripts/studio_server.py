# -*- coding: utf-8 -*-
"""AI 卡片炼金术 · 本地扩充服务

启动：
    python scripts/studio_server.py           # 默认 http://127.0.0.1:8796
    python scripts/studio_server.py 8801      # 指定端口

能做什么：
    1. 以 http 方式打开工作台（比 file:// 更符合浏览器安全策略）
    2. GET  /api/data                  拿全部卡片与风格
    3. POST /api/card                  新增一张卡片，自动写回 data/alchemy.json 并重建 index.html
    4. POST /api/style                 新增一种风格
    5. GET  /api/export                导出 Markdown

新增卡片示例（curl）：
    curl -X POST http://127.0.0.1:8796/api/card -H "Content-Type: application/json" ^
         -d "{\"type\":\"语录\",\"title\":\"标题\",\"core\":\"一句话\",\"body\":\"正文\",\"source\":\"来源\",\"date\":\"2026-09\",\"tags\":[\"a\",\"b\"],\"fit\":[\"zen-line\"]}"

只依赖 Python 标准库。
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "alchemy.json"
MIME = {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}


def load():
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import build  # noqa: E402
        build.main()
    except Exception as e:  # 构建失败不影响数据写入
        print("build skipped:", e)


def next_id(items, prefix):
    used = [int(i["id"].replace(prefix, "")) for i in items if i["id"].startswith(prefix)]
    return f"{prefix}{max(used) + 1 if used else 1:02d}"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 安静一点

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/data":
            return self._send(200, load())
        if path == "/api/export":
            data = load()
            lines = ["# AI 卡片炼金术 · 丸子的无限进步", ""]
            for t in ["故事", "进展", "语录"]:
                lines += ["", "## " + t, ""]
                for c in data["cards"]:
                    if c["type"] == t:
                        lines += [f"### {c['title']}", "", f"**{c['core']}**", "", c["body"], "",
                                  f"— {c['source']}　{c['date']}", ""]
            return self._send(200, "\n".join(lines), "text/markdown; charset=utf-8")
        # 静态文件
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        target = (ROOT / rel).resolve()
        if not str(target).startswith(str(ROOT)) or not target.exists():
            return self._send(404, {"error": "not found"})
        self._send(200, target.read_bytes(), MIME.get(target.suffix, "application/octet-stream"))

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception as e:
            return self._send(400, {"error": f"bad json: {e}"})

        data = load()
        if path == "/api/card":
            for key in ["type", "title", "core", "body"]:
                if not payload.get(key):
                    return self._send(400, {"error": f"缺少字段 {key}"})
            payload["id"] = payload.get("id") or next_id(data["cards"], "c")
            payload.setdefault("date", "")
            payload.setdefault("tags", [])
            payload.setdefault("fit", [])
            payload.setdefault("source", "")
            data["cards"].append(payload)
            save(data)
            return self._send(200, {"ok": True, "id": payload["id"], "total": len(data["cards"])})

        if path == "/api/style":
            for key in ["name", "category", "prompt"]:
                if not payload.get(key):
                    return self._send(400, {"error": f"缺少字段 {key}"})
            payload["id"] = payload.get("id") or payload["name"]
            payload.setdefault("keep", "")
            payload.setdefault("fit", [])
            payload.setdefault("source", "丸子原创")
            payload.setdefault("added", "")
            payload.setdefault("sample", "")
            data["styles"].append(payload)
            save(data)
            return self._send(200, {"ok": True, "id": payload["id"], "total": len(data["styles"])})

        return self._send(404, {"error": "unknown endpoint"})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8796
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"AI 卡片炼金术 · 本地扩充服务已启动: http://127.0.0.1:{port}")
    print("Ctrl+C 停止")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
