from __future__ import annotations

import string


def entries_validator(value: int) -> int:
    if value <= 0 or value > 100:
        raise ValueError('Значение должно быть числом от 1 до 100.')
    return value


def validate_password(text: str) -> str:
    rules: list[tuple[str, callable]] = []

    # --- Длина пароля ---
    rules.append(('Пароль должен быть не короче 12 символов', lambda s: len(s) >= 12))
    rules.append(('Пароль должен быть не длиннее 128 символов', lambda s: len(s) <= 128))

    # --- Базовые проверки на символы ---
    rules.append(
        ('Пароль должен содержать хотя бы одну цифру', lambda s: any(ch.isdigit() for ch in s)),
    )
    rules.append(
        (
            'Пароль должен содержать хотя бы одну заглавную букву',
            lambda s: any(ch.isupper() for ch in s),
        ),
    )
    rules.append(
        (
            'Пароль должен содержать хотя бы одну строчную букву',
            lambda s: any(ch.islower() for ch in s),
        ),
    )
    rules.append(
        (
            'Пароль должен содержать хотя бы один символ пунктуации',
            lambda s: any(ch in string.punctuation for ch in s),
        ),
    )
    rules.append(('Пароль не должен содержать пробелы', lambda s: ' ' not in s))

    # --- Запрещенные слова ---
    forbidden = [
        'password',
        'qwerty',
        '123456',
        'admin',
        'letmein',
        'dragon',
        'iloveyou',
        'monkey',
        'welcome',
        'abc123',
        'user',
        'login',
        'test',
        'root',
        'god',
        'sex',
        'love',
        'money',
    ]
    for word in forbidden:
        rules.append(
            (f"Пароль не должен содержать слово '{word}'", lambda s, w=word: w not in s.lower()),
        )

    # --- Минимум разных символов ---
    rules.append(
        ('Пароль должен содержать хотя бы 8 уникальных символов', lambda s: len(set(s)) >= 8),
    )
    rules.append(
        ('Пароль должен содержать хотя бы 12 уникальных символов', lambda s: len(set(s)) >= 12),
    )

    # --- Нельзя повторять один и тот же символ слишком много раз ---
    rules.append(
        (
            'Ни один символ не должен встречаться более 5 раз подряд',
            lambda s: all(
                s[i] != s[i + 1] or s[i] != s[i + 2] or s[i] != s[i + 3] or s[i] != s[i + 4]
                for i in range(len(s) - 4)
            ),
        ),
    )

    # --- Каждая буква алфавита (26 правил) ---
    for ch in string.ascii_lowercase[:26]:
        rules.append(
            (f"Пароль должен содержать хотя бы одну букву '{ch}'", lambda s, c=ch: c in s.lower()),
        )

    # --- Каждая цифра (10 правил) ---
    for d in string.digits:
        rules.append((f"Пароль должен содержать цифру '{d}'", lambda s, d=d: d in s))

    # --- Несколько правил на пунктуацию (10 символов) ---
    for p in '!@#$%^&*()':
        rules.append((f"Пароль должен содержать символ '{p}'", lambda s, p=p: p in s))

    # --- Дополнительные общие правила ---
    rules.append(('Пароль не должен начинаться с цифры', lambda s: not s[0].isdigit()))
    rules.append(('Пароль не должен заканчиваться пробелом', lambda s: not s.endswith(' ')))
    rules.append(('Пароль не должен состоять только из букв', lambda s: not s.isalpha()))
    rules.append(('Пароль не должен состоять только из цифр', lambda s: not s.isdigit()))
    rules.append(
        (
            'Пароль не должен состоять только из заглавных букв',
            lambda s: not (s.isupper() and s.isalpha()),
        ),
    )
    rules.append(
        (
            'Пароль не должен состоять только из строчных букв',
            lambda s: not (s.islower() and s.isalpha()),
        ),
    )
    rules.append(
        (
            'Пароль не должен содержать подряд три одинаковых символа',
            lambda s: all(s[i] != s[i + 1] or s[i] != s[i + 2] for i in range(len(s) - 2)),
        ),
    )
    rules.append(
        (
            'Пароль не должен содержать более 3 подряд идущих цифр',
            lambda s: not any(
                s[i].isdigit() and s[i + 1].isdigit() and s[i + 2].isdigit() and s[i + 3].isdigit()
                for i in range(len(s) - 3)
            ),
        ),
    )

    # --- Выполняем проверки ---
    for msg, check in rules:
        if not check(text):
            raise ValueError(msg)
    return text
