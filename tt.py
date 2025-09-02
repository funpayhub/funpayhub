from __future__ import annotations

import json

from funpayhub.lib.telegram.menu_constructor.renderer import PropsMenuOverridesDict


a = PropsMenuOverridesDict()

a['category1.*'] = 1
print(json.dumps(a._rules, indent=2, ensure_ascii=False))
a['category1.*.some_person'] = 123
print(json.dumps(a._rules, indent=2, ensure_ascii=False))
print(a['category1.category2.some_person'])
