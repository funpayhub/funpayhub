from funpayhub.app.funpay.main import FunPay
from funpayhub.app.properties import FunPayHubProperties
from typing import Any


class FunPayHub:
    def __init__(
        self,
        properties: FunPayHubProperties | None = None,
    ):
        workflow_data: dict[str, Any] = {
            'hub': self,
            'properties': properties,
        }

        self.properties = properties or FunPayHubProperties()
        self.funpay = FunPay(self.properties, workflow_data=workflow_data)

        workflow_data.update({
            'fp': self.funpay,
            'fp_bot': self.funpay.bot,
            'fp_dp': self.funpay.dispatcher,
            'fp_formatters': self.funpay.text_formatters
        })

    async def start(self):
        await self.funpay.start()