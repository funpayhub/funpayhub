from aiogram.filters.callback_data import CallbackData


class Dummy(CallbackData, prefix='dummy'): ...

class Clear(CallbackData, prefix='clear'): ...


class OpenProperties(CallbackData, prefix='o'):
    path: str
    page: int = 0


class ToggleParameter(CallbackData, prefix='t'):
    path: str
    page: int


class ChangeParameter(CallbackData, prefix='c'):
    path: str
    page: int


class OpenChoiceParameter(CallbackData, prefix='s'):
    path: str
    page: int = 0


class SelectParameterValue(CallbackData, prefix='s'):
    path: str
    page: int
