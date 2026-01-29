from __future__ import annotations

import asyncio

from funpaybotengine import Router
from funpaybotengine.types import Subcategory
from funpaybotengine.runner import EventsStack
from funpaybotengine.dispatching import NewSaleEvent
from funpaybotengine.types.enums import SubcategoryType

from funpayhub.app.funpay.main import FunPay


router = Router(name='fph:on_new_sale')


@router.on_new_sale(lambda events_stack: events_stack.data.get('offers_info') is not None)
async def prepare_offers_info(events_stack: EventsStack, fp: FunPay) -> None:
    """
    Данный хэндлер (который по сути должен быть миддлварью, (и в будущем будет)) собирает
    все события о новых продажах из events stack, сортирует их по категориям / подкатегориям и
    запрашивает лоты получившихся подкатегорий.

    Полученные подкатегории хранятся в EventsStack.data['offers_info'] в словаре вида
    {subcategory_id: [list of offers]}.

    # todo: должно срабатывать только если есть настройка автовыдачи с идентификатором лота, а не
    названием
    """
    events_to_process = [i for i in events_stack.events if isinstance(i, NewSaleEvent)]
    subcategories_to_get: set[Subcategory] = set()

    categories = await fp.bot.storage.get_categories()
    categories_by_name = {i.name: i for i in categories}

    for event in events_to_process:
        preview = await event.get_order_preview()

        # todo:
        # На данный момент нет ни одной подкатегории, в названии которой была бы запятая.
        # Но данный вариант нестабилен, ибо никто не мешает FunPay добавить такую категорию.
        # Необходимо использовать другой способ.
        category_name, subcategory_name = preview.category_text.rsplit(',', 1)
        category = categories_by_name.get(category_name)
        if category is None:
            continue

        subcategories_by_name = {i.name: i for i in category.subcategories}
        subcategory = subcategories_by_name.get(subcategory_name)
        if subcategory is None or subcategory.type is not SubcategoryType.COMMON:
            continue

        subcategories_to_get.add(subcategory)
        event['assigned_subcategory'] = subcategory

    if len(subcategories_to_get) == 0:
        return

    if len(subcategories_to_get) <= 2:
        tasks = [
            asyncio.create_task(fp.bot.get_my_offers_page(i.id)) for i in subcategories_to_get
        ]
        complete, pending = await asyncio.wait(*tasks)
    else:
        ...
