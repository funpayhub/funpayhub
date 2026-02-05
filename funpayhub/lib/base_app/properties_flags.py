from __future__ import annotations

from enum import auto


class ParameterFlags:
    HIDE = auto()
    """Параметры с данным флагом не отображаются в меню параметров."""

    HIDE_VALUE = auto()
    """Значения параметров с данным флагом не отображаются в меню параметров."""

    PROTECT_VALUE = auto()
    """Значения параметров с данным флагом замаскированы в меню параметров."""

    NEED_RESTART = auto()
    """
    После изменения значения параметра с данным флагом пользователь получит сообщение о том,
    что FunPay Hub необходимо перезапустить.
    """


class PropertiesFlags:
    HIDE = auto()
