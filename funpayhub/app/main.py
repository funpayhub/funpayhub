from __future__ import annotations

from funpayhub.app.properties import FunPayHubProperties
from funpayhub.app.funpay.main import FunPay


class FunPayHub:
    def __init__(
        self,
        properties: FunPayHubProperties | None = None,
    ):
        workflow_data = {}

        if properties is None:
            properties = FunPayHubProperties()
            properties.load()
        self._properties = properties

        self._funpay = FunPay(self, workflow_data=workflow_data)

        workflow_data.update(
            {
                'hub': self,
                'properties': self.properties,
                'fp': self.funpay,
                'fp_bot': self.funpay.bot,
                'fp_dp': self.funpay.dispatcher,
                'fp_formatters': self.funpay.text_formatters,
            }
        )

    async def start(self):
        await self.funpay.start()

    @property
    def properties(self) -> FunPayHubProperties:
        return self._properties

    @property
    def funpay(self) -> FunPay:
        return self._funpay
