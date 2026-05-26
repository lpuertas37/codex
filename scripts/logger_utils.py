from __future__ import annotations
from datetime import datetime
from pathlib import Path


def log_line(path:str,msg:str)->None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    ts=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + f"[{ts}] {msg}\n",encoding='utf-8')
