import polib


po = polib.pofile('funpayhub/locales/ru/LC_MESSAGES/main.po')
po.save_as_mofile('funpayhub/locales/ru/LC_MESSAGES/main.mo')

po = polib.pofile('funpayhub/locales/en/LC_MESSAGES/main.po')
po.save_as_mofile('funpayhub/locales/en/LC_MESSAGES/main.mo')


import gettext


tr = gettext.translation('main', localedir='funpayhub/locales', languages=['en', 'ru'], fallback=True)
_ = tr.gettext


from pathlib import Path
from types import MappingProxyType
from collections import defaultdict
import os


class Translater:
    def __init__(self):
        self._catalogs: dict[str, list[gettext.GNUTranslations]] = defaultdict(list)

    def add_translations(self, path_to_locales: str | Path, domain="main") -> None:
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


if __name__ == '__main__':
    tr = Translater()
    tr.add_translations('funpayhub/locales')
    print(tr.translate('telegram_settings_pname', 'ru'))