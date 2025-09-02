from dataclasses import dataclass, field
from aiogram.types import Message
from funpayhub.lib.properties import MutableParameter



class State:
    name: str = field(init=False, repr=False, default='state')

@dataclass
class ChangingParameterValueState(State):
    name: str = field(init=False, repr=False, default='changing_parameter_value')

    parameter: MutableParameter
    page: int
    menu_message: Message
    message: Message
    user_messages: list[Message]
