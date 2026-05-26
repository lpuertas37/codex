from __future__ import annotations
import json
from pathlib import Path


def load_editorial_malla() -> dict:
    yaml_path = Path('config/editorial_malla.yaml')
    fallback_path = Path('config/editorial_malla.fallback.json')
    if yaml_path.exists():
        try:
            import yaml  # lazy optional
            return yaml.safe_load(yaml_path.read_text(encoding='utf-8')) or {}
        except ModuleNotFoundError:
            print('pyyaml no disponible; usando editorial_malla.fallback.json')
        except Exception:
            pass
    if fallback_path.exists():
        return json.loads(fallback_path.read_text(encoding='utf-8'))
    return {}


def load_topics() -> list[str]:
    topics = []
    tp = Path('config/topics.yaml')
    if tp.exists():
        try:
            import yaml
            topics.extend((yaml.safe_load(tp.read_text(encoding='utf-8')) or {}).get('topics', []))
        except ModuleNotFoundError:
            pass
    m = load_editorial_malla()
    for _, ld in m.get('lineas_editoriales', {}).items():
        for t in ld.get('temas', []):
            topics.extend(t.get('keywords', []))
    return sorted(set(topics))
