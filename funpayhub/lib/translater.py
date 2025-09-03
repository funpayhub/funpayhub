from __future__ import annotations

import re
import gettext
from pathlib import Path
from collections import defaultdict


TRANSLATION_RE = re.compile(r'(?<!\$)\$[a-zA-Z0-9._\-:]+')


class Translater:
    def __init__(self) -> None:
        self._catalogs: dict[str, list[gettext.GNUTranslations]] = defaultdict(list)

    def add_translations(self, path_to_locales: str | Path, domain: str = 'main') -> None:
        path = Path(path_to_locales)
        if not path.is_dir():
            return

        for lang_dir in path.iterdir():
            mo_path = lang_dir / 'LC_MESSAGES' / f'{domain}.mo'
            if mo_path.exists():
                with mo_path.open('rb') as f:
                    tr = gettext.GNUTranslations(f)
                self._catalogs[lang_dir.name].append(tr)

    def translate(self, key: str, language: str) -> str:
        for tr in self._catalogs.get(language, []):
            result = tr.gettext(key)
            if result != key:
                return result if result != '__empty__' else ''

        for tr in self._catalogs.get('ru', []):
            result = tr.gettext(key)
            if result != key:
                return result if result != '__empty__' else ''

        return key

    def translate_text(self, text: str, language: str) -> str:
        text = text.replace('$$', '__ESCAPED_DOLLAR__')
        text = TRANSLATION_RE.sub(
            lambda m: self.translate(m.group(0), language),
            text,
        )
        return text.replace('__ESCAPED_DOLLAR__', '$')
