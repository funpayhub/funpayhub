from __future__ import annotations

from typing import TYPE_CHECKING

from hubplatform.i18n import I18nString

from dothub.loggers import funpay_component as logger
from dothub.app.components.funpay_component.dispatching import ComponentRouter
lazy from dothub.app.components.funpay_component.component import FunPayComponentState


if TYPE_CHECKING:
    from pyconfigtree import BoolParameter
    from funpaybotengine.types.pages import ProfilePage

    from dothub.app.components.funpay_component import FunPayComponent
    from dothub.app.components.funpay_component.offers_raiser import OffersRaiser


router = ComponentRouter(name='app:funpay_component:offers_raiser')


async def _start_raising(funpay_component: FunPayComponent, offers_raiser: OffersRaiser) -> None:
    # Fresh profile, so the raiser starts with actual offers.
    await offers_raiser.start(await funpay_component.profile(update=True))


@router.on_component_start(
    lambda funpay_props: funpay_props.auto_raise.value,
    name='app:funpay_component:start_auto_raise',
    as_task=True,  # do not delay events listening with a profile request
)
async def start_auto_raise(funpay_component: FunPayComponent, offers_raiser: OffersRaiser) -> None:
    logger.info(I18nString('Starting auto raise for all profile offers.'))
    await _start_raising(funpay_component, offers_raiser)


@router.on_component_stop(name='app:funpay_component:stop_auto_raise')
async def stop_auto_raise(offers_raiser: OffersRaiser) -> None:
    await offers_raiser.stop()


@router.on_profile_updated(name='app:funpay_component:update_offers_raiser')
async def update_offers_raiser(profile: ProfilePage, offers_raiser: OffersRaiser) -> None:
    await offers_raiser.update(profile)


async def on_auto_raise_toggled(
    parameter: BoolParameter,
    funpay_component: FunPayComponent,
    offers_raiser: OffersRaiser,
) -> None:
    """
    App router handler (``on_parameter_value_changed``) for ``FunPayProperties.auto_raise``.
    Bound in ``FunPayComponent.setup``.
    """
    if not parameter.value:
        await offers_raiser.stop()
        return

    if funpay_component.state is not FunPayComponentState.RUNNING:
        logger.info(I18nString('Auto raise has been enabled, it will start with the component.'))
        return
    await _start_raising(funpay_component, offers_raiser)
