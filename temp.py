import polib
import os


for i in os.listdir('funpayhub/locales'):
    po = polib.pofile(f'funpayhub/locales/{i}/LC_MESSAGES/main.po')
    po.save_as_mofile(f'funpayhub/locales/{i}/LC_MESSAGES/main.mo')

