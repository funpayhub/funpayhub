from aiogram.filters.callback_data import CallbackData


class Dummy(CallbackData, prefix='dummy'): ...


class Clear(CallbackData, prefix='clear'): ...


class Hash(CallbackData, prefix='hash'):
    hash: str


class OpenProperties(CallbackData, prefix='o'):
    path: str
    page: int = 0


class ToggleParameter(CallbackData, prefix='t'):
    path: str
    page: int


class ChangeParameter(CallbackData, prefix='c'):
    path: str
    page: int


class OpenChoiceParameter(CallbackData, prefix='open_choice_param'):
    path: str
    page: int = 0


class SelectParameterValue(CallbackData, prefix='select_param_val'):
    path: str
    index: int
    page: int


class SelectPage(CallbackData, prefix='select_page'):
    query: str
