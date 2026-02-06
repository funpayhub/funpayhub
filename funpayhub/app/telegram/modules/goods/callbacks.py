from __future__ import annotations


__all__ = [
    'DownloadGoods',
    'UploadGoods',
    'AddGoods',
    'RemoveGoods',
    'RemoveGoodsSource',
    'ReloadGoodsSource',
    'AddGoodsTxtSource',
]


from funpayhub.lib.telegram.callback_data import CallbackData


class DownloadGoods(CallbackData, identifier='download_goods'):
    source_id: str


class UploadGoods(CallbackData, identifier='upload_goods'):
    source_id: str


class AddGoods(CallbackData, identifier='add_goods'):
    source_id: str


class RemoveGoods(CallbackData, identifier='remove_goods'):
    source_id: str


class RemoveGoodsSource(CallbackData, identifier='remove_goods_source'):
    source_id: str
    confirm: bool = False


class ReloadGoodsSource(CallbackData, identifier='reload_goods_source'):
    source_id: str


class AddGoodsTxtSource(CallbackData, identifier='add_goods_txt_source'): ...
