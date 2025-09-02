from __future__ import annotations

import os

import polib


for i in os.listdir('funpayhub/locales'):
    po = polib.pofile(f'funpayhub/locales/{i}/LC_MESSAGES/main.po')
    po.save_as_mofile(f'funpayhub/locales/{i}/LC_MESSAGES/main.mo')
