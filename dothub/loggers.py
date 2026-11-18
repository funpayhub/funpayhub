from __future__ import annotations


__all__ = ['app', 'funpay_component', 'telegram_component']

from logging import LoggerAdapter, getLogger


app = getLogger('dothub.app')
funpay_component = LoggerAdapter(getLogger('funpay_component'), extra={'hub_component': 'FunPay'})
telegram_component = LoggerAdapter(
    getLogger('telegram_component'),
    extra={'hub_component': 'Telegram'},
)
