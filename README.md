<h1 align="center">FunPay Hub</h1>
<p align="center">
    <a href="https://github.com/funpayhub/funpayhub/commits"><img src="https://img.shields.io/github/commit-activity/w/funpayhub/funpayhub.svg?style=flat-square" alt="Commit activity" /></a>
    <a href="https://t.me/funpay_hub" target="_blank"><img src="https://img.shields.io/badge/Telegram-@funpay_hub-2CA5E0?logo=telegram&logoColor=white" alt="Telegram"></a>
</p>

**FunPayHub** — это не просто бот, а полноценный инструмент для автоматизации продаж и рутинных действий на FunPay.

Проект создан для тех, кому нужен **бесплатный, опенсорсный и расширяемый** бот с продуманной архитектурой и возможностью глубокой кастомизации под свои задачи.

---

Статус проекта
--------------

🚧 **FunPayHub находится в активной стадии разработки.**

Функционал активно расширяется. Могут иметься ошибки в работе, а так же изменения в поведении API.
Если у вас есть пожелания по функционалу или информация об ошибках - [напишите в Telegram](https://t.me/funpay_hub) - оперативно все сделаю.

---

Возможности
-----------

- 📈 **Автоподнятие лотов**
- 💬 **Автоответы**:
  - 💬 на личные сообщения;
  - 🌟 на отзывы: как в сам отзыв, так и в чат;
  - 🖐 на приветственные сообщения c возможностью кастомизировать сообщения в зависимости от просматриваемого лота;
- 📦 **Автоматическая выдача товаров**
- 🏷🏷️ **Большое кол-во форматтеров с воможностью передавать параметры.** Например:
```Привет, $message<username>! Вот твой заказ: $goods``` 
- 🧩 **Плагиная архитектура**, позволяющая:
  - легко писать и поддерживать собственные плагины  
  - делать их максимально функциональными
- 🧩 **Репозитории плаигнов**, позволяющие:
  - разработчикам держать все свои плаигны в одном месте
  - пользователям легко скачивать и обновлять плагины прямо из Telegram интерфейса без надобности ручной загрузки.
- 🎆 **Кастомизация Telegram UI**
- **Многое другое**

---

### Для разработчиков

- 🧩 **Проработанная система плагинов**

В отличии от других проектов, в FunPay Hub плагины можно писать в модульном виде.
Вся информация о плагине хранится в манифесте (`manifest.json`) с указанием точки входа.
Используемые в FunPay Hub фреймворки (`aiogram`, `funpaybotengine` и др.), а так же сама архитектура FPH позволяет писать в плагинах качественный код, а не сплошные костыли.

- 🔘 **Система параметров**

Разработчикам плагинов больше не нужно думать о том, как и где хранить параметры.
Просто создайте свое древо параметров с помощью готовых классов и передайте его FunPay Hub'у.
FunPay Hub сам позаботится о сериализации, валидации и отображении параметров в Telegram UI!

- 🏷🏷️ **Создание и модификация существующих меню**

Каждое меню в FunPay Hub - это зарегистрированный в реестре объект построителя.
Для любого построителя меню можно добавить модификатор, так же зарегистрировав его через реестр.
Таким образом можно модифицировать уже существующие меню, легко добавляя свои кастомные элементы.

- 🔘 **Поддержка пагинации в Telegram UI; Структура UI;**

В FunPay Hub каждое меню состоит из клавиатуры и текста (в будущем: и из изображения). И клавиатура, и текст, разбиты на 3 секции:
  - загловок
  - основная секция
  - подвал
Это позволяет легко создавать структурированные меню с вомзожностью пагинации.
А пагинацию в FunPayHub можно добавить всего в 1 строку кода! Не нужно писать никакую логику, все за вас сделает FPH.

---


Скриншоты
---------

<details>
<summary>Telegram UI</summary>
<img width="396" height="388" alt="image" src="https://github.com/user-attachments/assets/3428cef1-7cae-413e-b600-323f1c7872a5" />
<img width="303" height="404" alt="image" src="https://github.com/user-attachments/assets/48db2661-4c7d-4c05-bb8d-57a07484aa0f" />
<img width="437" height="985" alt="image" src="https://github.com/user-attachments/assets/c140c9ec-7216-48f4-ac8d-e118f8162b78" />
<img width="337" height="350" alt="image" src="https://github.com/user-attachments/assets/936fad07-581f-4d84-979a-28a1bff62336" />
</details>

<details>
<summary>Плагины</summary>
<img width="229" height="349" alt="image" src="https://github.com/user-attachments/assets/0a202663-9a60-4185-9abe-b15f2c212d74" />
<img width="431" height="375" alt="image" src="https://github.com/user-attachments/assets/965ed817-5caa-433d-bc83-d24685014095" />
<img width="430" height="311" alt="image" src="https://github.com/user-attachments/assets/6f89e18c-b85a-4fe4-9d03-6fa7241f5284" />
<img width="430" height="311" alt="image" src="https://github.com/user-attachments/assets/c201e2a0-7a85-4b9b-8be5-989dbc70de6e" />
</details>


<details>
<summary>Уведомления</summary>
<img width="448" height="883" alt="image" src="https://github.com/user-attachments/assets/a8ef2e43-8e73-4c69-b5d3-62536d2c83e1" />
<img width="443" height="380" alt="image" src="https://github.com/user-attachments/assets/e6abeb30-65d4-4fa8-8c03-a6a02471cf31" />
</details>

<details>
<summary>Прочее</summary>
<img width="434" height="413" alt="image" src="https://github.com/user-attachments/assets/ffded71a-2666-4235-855a-418dd84a6d4d" />
<img width="436" height="575" alt="image" src="https://github.com/user-attachments/assets/2c12037f-77a2-4ff7-974c-1667960e5be8" />
<img width="438" height="551" alt="image" src="https://github.com/user-attachments/assets/520b7d8f-082c-43b6-ac6e-3f48713d8e73" />
</details>

---

Используемые технологии
-----------------------

FunPayHub построен на основе нескольких ключевых библиотек:

- [FunpayBotEngine](https://github.com/funpayhub/funpaybotengine) — фреймворк для разработки FunPay ботов;
- [aiogram](https://github.com/aiogram/aiogram) — фреймворк для разработки Telegram ботов;
- [Eventry](https://github.com/qvvonk/eventry) — фреймворк для создания событийной системы с роутерами, фильтрами, хэндлерами и т.п.; 

Эта комбинация позволяет строить **мощные и расширяемые приложения**.

---

Планируемый функционал
----------------------

В планах / рарзработке:

- 🧰 **Многочисленные команды-утилиты**, позволяющие управлять свои FunPay аккаунтом. Например:
  - управление лотами: массовое включение / отключение / копирование своих и чужих лотов.
  - сбор статистики аккаунта с графиками
  - и т.д.

- 🧩 **Разработка плагинов в официальном репозитории**.

- ♻️ **Автообновление плагинов**

- 🌐 **REST API** (в виде плагина)  
  Для интеграции с внешними сервисами и панелями управления.

- 🖥 **Web UI** (в виде плагина)  
  Веб-интерфейс для управления FunPay Hub.

- 🧰 **GUI-установщик**  
  Установщик, позволяющий развернуть FunPayHub:
  - на текущем компьютере;
  - на удалённом сервере (VPS / dedicated).


---

Установка
=========

Windows
-------
**PowerShell (от имени администратора)**  
```
Set-ExecutionPolicy Bypass -Scope Process -Force; (iwr https://raw.githubusercontent.com/funpayhub/fph_install_scripts/refs/heads/main/install_fph.ps1 -UseBasicParsing).Content | iex
```


Linux (Ubuntu / Debian / Arch linux)
------------------------------------
**curl**
```
curl -fsSL https://raw.githubusercontent.com/funpayhub/fph_install_scripts/refs/heads/main/install_fph.sh > install_fph.sh && chmod +x install_fph.sh && ./install_fph.sh
```


**wget**
```
wget -qO install_fph.sh https://raw.githubusercontent.com/funpayhub/fph_install_scripts/refs/heads/main/install_fph.sh && chmod +x install_fph.sh && ./install_fph.sh
```
