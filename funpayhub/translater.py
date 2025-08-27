import gettext
from collections import defaultdict
from pathlib import Path


class Translater:
    def __init__(self) -> None:
        self._catalogs: dict[str, list[gettext.GNUTranslations]] = defaultdict(list)

    def add_translations(self, path_to_locales: str | Path, domain: str = "main") -> None:
        path = Path(path_to_locales)
        if not path.is_dir():
            return

        for lang_dir in path.iterdir():
            mo_path = lang_dir / "LC_MESSAGES" / f"{domain}.mo"
            if mo_path.exists():
                with mo_path.open("rb") as f:
                    tr = gettext.GNUTranslations(f)
                self._catalogs[lang_dir.name].append(tr)

    def translate(self, key: str, language: str) -> str:
        for tr in self._catalogs.get(language, []):
            result = tr.gettext(key)
            if result != key:
                return result

        for tr in self._catalogs.get('ru', []):
            result = tr.gettext(key)
            if result != key:
                return result

        return key