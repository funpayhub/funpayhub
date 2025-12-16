from __future__ import annotations

from funpayhub.lib.telegram.callback_data import CallbackData


class ProxyAction:
    no_proxy = 0
    from_properties = 1
    from_env = 2


class UserAgentAction:
    default = 0
    from_properties = 1
    from_env = 2


class SelectSetupLanguage(CallbackData, identifier='1'):
    lang: str


class SetupProxy(CallbackData, identifier='2'):
    action: int


class SetupUserAgent(CallbackData, identifier='3'):
    action: int
