"""
Временный костыль.
"""

from __future__ import annotations

from funpaybotengine import Bot
from funpaybotengine.types import SubcategoryType
from funpaybotengine.types.pages import ProfilePage


async def get_profile_raisable_categories(profile: ProfilePage, bot: Bot) -> set[int]:
    result = set()

    if not profile.offers.get(SubcategoryType.COMMON):
        return result

    categories = await bot.storage.get_categories()
    subcategories_to_category = {
        subcat.id: cat
        for cat in categories
        for subcat in cat.subcategories
        if subcat.type is SubcategoryType.COMMON
    }

    for subcategory_id in profile.offers[SubcategoryType.COMMON]:
        if subcategory_id in subcategories_to_category:
            result.add(subcategories_to_category[subcategory_id].id)
    return result
