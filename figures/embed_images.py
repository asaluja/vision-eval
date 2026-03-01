"""Replace <img src="..."> file paths with inline base64 data URIs."""
from __future__ import annotations

import base64
import re
import sys
from pathlib import Path


def embed(html_path: str) -> None:
    html_file = Path(html_path)
    html = html_file.read_text()
    html_dir = html_file.parent

    def replace_src(m: re.Match) -> str:
        src = m.group(1)
        img_path = (html_dir / src).resolve()
        if not img_path.exists():
            print(f"  skipping (not found): {src}")
            return m.group(0)
        b64 = base64.b64encode(img_path.read_bytes()).decode()
        suffix = img_path.suffix.lstrip(".")
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "gif": "image/gif", "svg": "image/svg+xml"}.get(suffix, f"image/{suffix}")
        print(f"  embedded: {src} ({img_path.stat().st_size // 1024}KB)")
        return f'src="data:{mime};base64,{b64}"'

    result = re.sub(r'src="([^"]+\.(png|jpe?g|gif|svg))"', replace_src, html)
    html_file.write_text(result)
    print(f"Wrote {html_file} ({len(result) // 1024}KB)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python figures/embed_images.py <path-to-report.html>")
        sys.exit(1)
    embed(sys.argv[1])
