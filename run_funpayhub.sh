#!/bin/sh

if [ -t 1 ]; then
    C_RESET="$(printf '\033[0m')"
    C_RED="$(printf '\033[31m')"
    C_GREEN="$(printf '\033[32m')"
    C_YELLOW="$(printf '\033[33m')"
    C_BLUE="$(printf '\033[34m')"
    C_CYAN="$(printf '\033[36m')"
    C_DIM="$(printf '\033[2m')"
else
    C_RESET=""
    C_RED=""
    C_GREEN=""
    C_YELLOW=""
    C_BLUE=""
    C_CYAN=""
    C_DIM=""
fi

TG_TOKEN=""
PYTHON_BIN=""


check_tg_token() {
    token="$1"

    curl -s -o /dev/null \
        -w "%{http_code}" \
        --max-time 5 \
        "https://api.telegram.org/bot${token}/getMe"
}

for arg in "$@"; do
    case "$arg" in
        --python=*) PYTHON_BIN="${arg#*=}" ;;
        --python) shift; PYTHON_BIN="$1" ;;
    esac
    shift
done

[ -z "$PYTHON_BIN" ] && PYTHON_BIN=".venv/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
    printf "${C_RED}(x_x) Не удалось запустить приложение.${C_RESET}\n"
    printf "Ожидался Python по пути:\n  ${C_GREEN}%s${C_RESET}\n\n" "$PYTHON_BIN"
    printf "${C_YELLOW}Пожалуйста, покажите это сообщение разработчику — он вам обязательно поможет.${C_RESET}\n"
    exit 1
fi

if [ -f "releases/current/launcher.py" ]; then
    exec "$PYTHON_BIN" releases/current/launcher.py
fi

echo ""
printf "${C_CYAN}(◕‿◕)${C_RESET} Привет!\n"
echo "Я не нашел лаунчер FunPay Hub. Похоже, это первый запуск."
echo ""

while :; do
    printf "${C_CYAN}(・ω・)${C_RESET} Мне нужен токен Telegram-бота.\n"
    printf "Он выглядит примерно так: ${C_YELLOW}123456789:AAHg7K...${C_RESET}\n\n"
    printf "Пожалуйста, вставь токен и нажми Enter: "
    read -r TG_TOKEN
    echo ""

    if [ -z "$TG_TOKEN" ]; then
        printf "${C_RED}(μ_μ)${C_RESET} Кажется, токен не был введён.\n"
        continue
    fi

    STATUS_CODE="$(check_tg_token "$TG_TOKEN")"

    case "$STATUS_CODE" in
        200)
            break
            ;;
        404)
            printf "${C_RED}(x_x)${C_RESET} Неверный токен (HTTP %s).\n\n" "$STATUS_CODE"
            ;;
        000)
            printf "${C_YELLOW}(ಠ_ಠ)${C_RESET} Не удалось подключиться к Telegram (HTTP %s).\n\n" "$STATUS_CODE"
            ;;
        *)
            printf "${C_YELLOW}(・_・?)${C_RESET} Неожиданный ответ Telegram (HTTP %s).\n\n" "$STATUS_CODE"
            ;;
    esac
done

printf "${C_GREEN}°˖✧◝(⁰▿⁰)◜✧˖°${C_RESET} Токен принят! Отлично!\n"
printf "${C_CYAN}(⌐■_■)${C_RESET} Запускаю FunPay Hub.\n"
printf ""

exec "$PYTHON_BIN" bootstrap.py --init-tg-token "$TG_TOKEN"
