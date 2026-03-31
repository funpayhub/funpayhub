from __future__ import annotations


__all__ = ['Translater', '_', '_en', '_ru', 'ru', 'en', 'translater']


import re
import gettext
from typing import Any
from string import Formatter
from pathlib import Path
from collections import defaultdict


TRANSLATION_RE = re.compile(r'(?<!\$)\$[a-zA-Z0-9._\-:]+')


class SafeFormatter(Formatter):
    missing = '~ERR'

    def get_value(self, key: str | int, args, kwargs) -> Any:
        if isinstance(key, int):
            return args[key] if len(args) >= key + 1 else self.missing
        return kwargs.get(key, self.missing)


formatter = SafeFormatter()


class Translater:
    def __init__(self, language: str = 'en') -> None:
        self._catalogs: dict[str, list[gettext.GNUTranslations]] = defaultdict(list)
        self.current_language = language

    def add_translations(self, path_to_locales: str | Path, skip_errors: bool = True) -> None:
        path = Path(path_to_locales)
        if not path.is_dir():
            if not skip_errors:
                raise ValueError('Path to locales must be a directory.')
            return

        for lang_dir in path.iterdir():
            lc_messages_path = lang_dir / 'LC_MESSAGES'
            if not lc_messages_path.exists() or not lc_messages_path.is_dir():
                continue

            for mo_path in lc_messages_path.iterdir():
                if not mo_path.is_file() or not mo_path.suffix == '.mo':
                    continue

                with mo_path.open('rb') as f:
                    tr = gettext.GNUTranslations(f)
                self._catalogs[lang_dir.name].append(tr)

    def translate(self, key: str, *args, language: str | None = None, **kwargs) -> str:
        if not key:
            return ''

        result = key
        for tr in self._catalogs.get(language or self.current_language, []):
            result = tr.gettext(key)
            result = result if result != '__empty__' else ''
            if result != key:
                break

        if result and (args or kwargs):
            result = formatter.format(result, *args, **kwargs)

        return result


translater = Translater()
"""Глобальный объект переводчика."""


def _(_: str, /) -> str:
    """
    Возвращает переданную строку без изменений.
    Используется как маркер для экстракторов строк.
    """
    return _


en = _
ru = _

# Deprecated
_en = _
_ru = _
