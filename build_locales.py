from __future__ import annotations

import os

import polib


BASE_DIR = 'funpayhub/locales'


for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith('.po'):
            po_path = os.path.join(root, file)
            mo_path = os.path.splitext(po_path)[0] + '.mo'

            po = polib.pofile(po_path)
            po.save_as_mofile(mo_path)
