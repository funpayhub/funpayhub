from __future__ import annotations

from pydantic import BaseModel, field_validator, field_serializer
from aiogram.filters.callback_data import CallbackData


class Pagable(BaseModel):
    page: int = 0

    @field_validator('page', mode='before')
    def parse_page(cls, v: str | int) -> int:
        if isinstance(v, str) and v.startswith('page-'):
            return int(v.split('-', 1)[1])
        return int(v)

    @field_serializer('page')
    def serialize_page(self, v: int) -> str:
        return f'page-{v}'


class Dummy(CallbackData, prefix='dummy'): ...


class Clear(CallbackData, prefix='clear'): ...


class Hash(CallbackData, prefix='hash'):
    hash: str


class OpenProperties(CallbackData, Pagable, prefix='o'):
    path: str


class ToggleParameter(CallbackData, Pagable, prefix='t'):
    path: str


class ChangeParameter(CallbackData, Pagable, prefix='c'):
    path: str


class OpenChoiceParameter(CallbackData, Pagable, prefix='open_choice_param'):
    path: str


class SelectParameterValue(CallbackData, Pagable, prefix='select_param_val'):
    path: str
    index: int


class SelectPage(CallbackData, prefix='select_page', sep='|'):
    query: str
    pages_amount: int


# new
class NextParamValue(CallbackData, prefix='next_param_value'):
    path: str


class ManualParamValueInput(CallbackData, prefix='manual_value_input'):
    path: str


class MenuParamValueInput(CallbackData, Pagable, prefix='menu_value_input'):
    path: str


class ChangePageTo(CallbackData, prefix='change_page_to'):
    page: int


class ManualPageChange(CallbackData, prefix='manual_page_change'):
    total_pages: int