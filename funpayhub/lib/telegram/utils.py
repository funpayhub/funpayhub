from __future__ import annotations


__all__ = [
    'join_callbacks',
    'split_callbacks',
]


def join_callbacks(*callbacks: str) -> str:
    """
    Объединяет последовательность предыдущих коллбэков с новым коллбэком в одну строку.

    История коллбэков `callbacks_history` и новый коллбэк `callback_query`
    соединяются с помощью разделителя `'->'`, чтобы образовать единый путь вызовов.

    Пример:
        >>> join_callbacks('start','menu','settings')
        'start->menu->settings'

    :param callbacks: коллбэки.

    :return: Строка, представляющая объединённую историю коллбэков.
    """
    return '->'.join(callbacks)


def split_callbacks(callback_query: str) -> tuple[list[str], str]:
    """
    Разделяет строку коллбэка на историю предыдущих коллбэков и текущий коллбэк.

    Функция ожидает, что коллбэки объединены в строку с помощью разделителя `'->'`.
    Последний элемент после разделителя считается текущим коллбэком, а все предыдущие — историей.

    Пример:
        >>> split_callbacks('start->menu->settings')
        (['start', 'menu'], 'settings')
        >>> split_callbacks('start')
        ([], 'start')

    :param callback_query: Строка с объединёнными коллбэками.

    :return: Кортеж из двух элементов:
        - список строк с историей предыдущих коллбэков
        - строка текущего коллбэка.
    """
    split = callback_query.split('->')
    if len(split) < 2:
        return [], callback_query
    return split[:-1], split[-1]
