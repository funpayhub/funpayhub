__all__ = [
    'FunPayImageFragment',
]


from hubplatform.expressions.fragments import Fragment


class FunPayImageFragment(Fragment):
    def __init__(self, image_id: str) -> None:
        self._image_id = image_id

    @property
    def image_id(self) -> str:
        return self._image_id

    @property
    def url(self) -> str:
        return f'https://s.funpay.com/{self._image_id}'
