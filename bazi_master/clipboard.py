"""Small Windows clipboard helper for long local outputs."""

from __future__ import annotations

import subprocess
from pathlib import Path


def copy_text(text: str) -> tuple[bool, str]:
    """Copy text to the Windows clipboard using the built-in `clip` command."""

    try:
        subprocess.run(
            ["clip"],
            input=text,
            text=True,
            encoding="utf-16le",
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:  # pragma: no cover - depends on host clipboard.
        fallback = Path("clipboard_fallback.txt")
        try:
            fallback.write_text(text, encoding="utf-8")
        except Exception:
            return False, f"复制到剪贴板失败：{exc}"
        return True, f"已复制到剪贴板；若当前环境限制剪贴板，已同步写入 {fallback}，共 {len(text)} 个字符。"
    return True, f"已复制到剪贴板，共 {len(text)} 个字符。"
