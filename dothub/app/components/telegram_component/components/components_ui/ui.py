from __future__ import annotations

from hubplatform.telegram.ui import (
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
)
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer

from .menu_ids import ComponentsUIMenuIDs


registry = UIRegistry()


@registry.add_menu_builder(menu_id=ComponentsUIMenuIDs.components_menu)
async def build_components_menu(ctx: MenuBuildContext[MenuContext]) -> MenuBuildingSpec:
    """
    List of app components.

    Empty by default: each component adds its own button with a menu modification
    (``UIRegistry.add_menu_modification(ComponentsUIMenuIDs.components_menu, ...)``).
    """
    return MenuBuildingSpec(menu=MenuSpec(), finalizer=StripAndNavigationFinalizer())
