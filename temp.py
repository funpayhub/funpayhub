import polib


po = polib.pofile('funpayhub/locales/ru/LC_MESSAGES/main.po')
po.save_as_mofile('funpayhub/locales/ru/LC_MESSAGES/main.mo')

po = polib.pofile('funpayhub/locales/en/LC_MESSAGES/main.po')
po.save_as_mofile('funpayhub/locales/en/LC_MESSAGES/main.mo')
