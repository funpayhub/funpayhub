from __future__ import annotations

from funpayhub.lib.base_app.telegram import (
    MenuIds as BaseMenuIds,
    ButtonIds as BaseButtonIds,
)


class MenuIds(BaseMenuIds):
    state_menu = 'fph:state_menu'
    main_menu = 'fph:main_menu'
    formatters_list = 'fph:formatters_list'
    formatter_info = 'fph:formatter_info'
    tg_chat_notifications = 'fph:tg_chat_notifications'
    add_command = 'fph:add_command'
    control = 'fph:control'

    new_funpay_message = 'fph:new_funpay_message'
    send_funpay_message = 'fph:send_funpay_message'

    start_notification = 'fph:start_notification'
    funpay_start_notification = 'fph:funpay_start_notification'
    update = 'fph:update_menu'
    install_update = 'fph:install_update'

    plugins_list = 'fph:plugins_list'
    plugin_info = 'fph:plugin_info'
    install_plugin = 'fph:install_plugin'

    repositories_list = 'fph:repositories_list'
    repository_info = 'fph:repository_info'
    repo_plugin_info = 'fph:repo_plugin_info'

    goods_sources_list = 'fph:goods_sources_list'
    goods_source_info = 'fph:goods_source_info'
    autodelivery_goods_sources_list = 'fph:autodelivery_goods_sources_list'
    new_sale_notification = 'fph:new_sale_notification'

    add_auto_delivery_rule = 'fph:add_auto_delivery_rule'

    review_notification = 'fph:new_review_notification'
    bind_first_response_to_offer = 'fph:first_response_bind_to_offer'


class ButtonIds(BaseButtonIds): ...
