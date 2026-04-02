"""Simple JSON-based i18n."""
from __future__ import annotations

import json
from pathlib import Path

_locales: dict[str, dict] = {}
_LOCALES_DIR = Path(__file__).parent.parent.parent / "locales"


def _load(locale: str) -> dict:
    if locale not in _locales:
        path = _LOCALES_DIR / f"{locale}.json"
        if not path.exists():
            path = _LOCALES_DIR / "en.json"
        with open(path, encoding="utf-8") as f:
            _locales[locale] = json.load(f)
    return _locales[locale]


def t(key: str, locale: str = "en", **kwargs: str | int) -> str:
    """Translate a key with optional format arguments."""
    strings = _load(locale)
    template = strings.get(key, _load("en").get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    return template
