from __future__ import annotations


async def entries_validator(value: int) -> None:
    if value <= 0 or value > 100:
        raise ValueError('Значение должно быть числом от 1 до 100.')
