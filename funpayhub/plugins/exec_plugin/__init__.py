from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub



class Plugin:
    async def setup(self, hub: FunPayHub) -> None:
        ...
