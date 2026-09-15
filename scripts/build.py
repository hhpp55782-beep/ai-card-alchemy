# -*- coding: utf-8 -*-
"""把 data/alchemy.json 注入 index.html，产出可以双击直接打开的单文件页面。

用法：
    python scripts/build.py

说明：
    index.html 里有一行 <script id="alchemy-data" type="application/json">__ALCHEMY_DATA__</script>
    本脚本把占位符替换成真实数据，保证 file:// 直接打开也能跑（不需要 fetch）。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "alchemy.json"
HTML = ROOT / "index.html"
PLACEHOLDER = "__ALCHEMY_DATA__"


def load_data():
    with DATA.open(encoding="utf-8") as f:
        return json.load(f)


def render(data):
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    # 防止数据里的 </script> 提前闭合标签
    raw = raw.replace("</", "<\\/")
    html = HTML.read_text(encoding="utf-8")
    if PLACEHOLDER not in html:
        # 已经注入过：整体替换 script 内容
        pattern = re.compile(
            r'(<script id="alchemy-data" type="application/json">)(.*?)(</script>)',
            re.S,
        )
        if not pattern.search(html):
            print("!! index.html 里找不到数据占位符，已跳过")
            return False
        html = pattern.sub(lambda m: m.group(1) + raw + m.group(3), html, count=1)
    else:
        html = html.replace(PLACEHOLDER, raw, 1)
    HTML.write_text(html, encoding="utf-8")
    return True


def main():
    data = load_data()
    if render(data):
        print(f"OK  cards={len(data['cards'])}  styles={len(data['styles'])}  -> index.html")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
